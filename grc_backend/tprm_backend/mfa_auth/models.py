from django.db import models
from django.utils import timezone
import hashlib
import secrets
import string


class User(models.Model):
    userid = models.AutoField(db_column="UserId", primary_key=True)
    username = models.CharField(db_column="UserName", max_length=255)
    password = models.CharField(db_column="Password", max_length=255)
    created_at = models.DateTimeField(db_column="CreatedAt", null=True, blank=True)
    updated_at = models.DateTimeField(db_column="UpdatedAt", null=True, blank=True)
    email = models.CharField(db_column="Email", max_length=100, null=True, blank=True)
    first_name = models.CharField(db_column="FirstName", max_length=45, null=True, blank=True)
    last_name = models.CharField(db_column="LastName", max_length=45, null=True, blank=True)
    is_active_raw = models.CharField(db_column="IsActive", max_length=45, null=True, blank=True)
    department_id = models.IntegerField(db_column="DepartmentId", null=True, blank=True)
    session_token = models.CharField(db_column="session_token", max_length=1045, null=True, blank=True)
    consent_accepted = models.CharField(db_column="consent_accepted", max_length=1, null=True, blank=True)
    license_key = models.CharField(db_column="license_key", max_length=255, null=True, blank=True)

    class Meta:
        db_table = "users"
        managed = False  # set to True only if Django should manage this table
        app_label = 'mfa_auth'

    def __str__(self):
        return self.username

    @property
    def is_active(self) -> bool:
        # Treat Y/YES/1/TRUE (case-insensitive) as active
        val = (self.is_active_raw or "").strip().lower()
        return val in {"y", "yes", "1", "true"}

    def generate_session_token(self):
        """Generate a secure session token"""
        return secrets.token_urlsafe(64)

    def set_session_token(self):
        """Set a new session token for the user"""
        self.session_token = self.generate_session_token()
        self.save(update_fields=['session_token'])
        return self.session_token


# --- MFA: Email OTP challenge table ---
class MfaEmailChallenge(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SATISFIED = "satisfied"
    STATUS_EXPIRED = "expired"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "pending"),
        (STATUS_SATISFIED, "satisfied"),
        (STATUS_EXPIRED, "expired"),
        (STATUS_FAILED, "failed"),
    ]

    challenge_id = models.BigAutoField(db_column="ChallengeId", primary_key=True)
    user = models.ForeignKey(
        User,
        db_column="UserId",
        related_name="mfa_challenges",
        on_delete=models.CASCADE,
    )
    otp_hash = models.BinaryField(db_column="OtpHash", max_length=64)  # SHA-256 bytes
    expires_at = models.DateTimeField(db_column="ExpiresAt")
    attempts = models.IntegerField(db_column="Attempts", default=0)
    status = models.CharField(
        db_column="Status", max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    ip_address = models.CharField(db_column="IpAddress", max_length=45, null=True, blank=True)
    user_agent = models.CharField(db_column="UserAgent", max_length=400, null=True, blank=True)
    created_at = models.DateTimeField(db_column="CreatedAt", default=timezone.now)
    used_at = models.DateTimeField(db_column="UsedAt", null=True, blank=True)

    class Meta:
        db_table = "mfa_email_challenges"
        indexes = [
            models.Index(fields=["user", "status"], name="idx_mfaec_user_status"),
            models.Index(fields=["expires_at"], name="idx_mfaec_expires"),
        ]

    def __str__(self):
        return f"Challenge#{self.challenge_id} for {self.user_id} ({self.status})"

    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))

    @classmethod
    def hash_otp(cls, otp):
        """Hash OTP using SHA-256"""
        return hashlib.sha256(otp.encode()).digest()

    def verify_otp(self, otp):
        """Verify the provided OTP against the stored hash"""
        return hashlib.sha256(otp.encode()).digest() == self.otp_hash

    def is_expired(self):
        """Check if the challenge has expired"""
        return timezone.now() > self.expires_at

    def mark_satisfied(self):
        """Mark the challenge as satisfied"""
        self.status = self.STATUS_SATISFIED
        self.used_at = timezone.now()
        self.save(update_fields=['status', 'used_at'])

    def mark_failed(self):
        """Mark the challenge as failed"""
        self.status = self.STATUS_FAILED
        self.save(update_fields=['status'])

    def increment_attempts(self):
        """Increment the number of attempts"""
        self.attempts += 1
        self.save(update_fields=['attempts'])


# --- MFA: Audit log (optional but recommended) ---
class MfaAuditLog(models.Model):
    EVT_ISSUED = "challenge_issued"
    EVT_OK = "challenge_ok"
    EVT_FAIL = "challenge_fail"
    EVENT_CHOICES = [
        (EVT_ISSUED, "challenge_issued"),
        (EVT_OK, "challenge_ok"),
        (EVT_FAIL, "challenge_fail"),
    ]

    mfa_event_id = models.BigAutoField(db_column="MfaEventId", primary_key=True)
    user = models.ForeignKey(
        User,
        db_column="UserId",
        related_name="mfa_audit_events",
        on_delete=models.CASCADE,
    )
    event_type = models.CharField(db_column="EventType", max_length=32, choices=EVENT_CHOICES)
    detail_json = models.JSONField(db_column="DetailJson", null=True, blank=True)
    ip_address = models.CharField(db_column="IpAddress", max_length=45, null=True, blank=True)
    user_agent = models.CharField(db_column="UserAgent", max_length=400, null=True, blank=True)
    created_at = models.DateTimeField(db_column="CreatedAt", default=timezone.now)

    class Meta:
        db_table = "mfa_audit_log"
        indexes = [
            models.Index(fields=["user", "created_at"], name="idx_mfaal_user_time"),
        ]

    def __str__(self):
        return f"MFA {self.event_type} for {self.user_id} @ {self.created_at}"

    @classmethod
    def log_event(cls, user, event_type, detail_json=None, request=None):
        """Log an MFA event"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:400]
        
        return cls.objects.create(
            user=user,
            event_type=event_type,
            detail_json=detail_json,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
