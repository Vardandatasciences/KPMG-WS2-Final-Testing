from django.db import migrations, models


def _compute_sha256_hex(value: str) -> str:
    import hashlib
    v = (value or "").strip().lower()
    return hashlib.sha256(v.encode("utf-8")).hexdigest()


def backfill_user_identifier_hashes(apps, schema_editor):
    Users = apps.get_model("grc", "Users")

    # Avoid importing runtime code directly where possible; fall back safely if decrypt helpers aren't available.
    decrypt_data = None
    is_encrypted_data = None
    try:
        from grc.utils.data_encryption import decrypt_data as _decrypt_data, is_encrypted_data as _is_encrypted_data

        decrypt_data = _decrypt_data
        is_encrypted_data = _is_encrypted_data
    except Exception:
        decrypt_data = None
        is_encrypted_data = None

    # Populate hashes for existing rows. We do best-effort decryption when values are encrypted.
    #
    # Important: legacy data may contain empty identifiers. Because we will enforce NOT NULL +
    # UNIQUE constraints, we must still generate a unique hash value per row in those cases
    # to avoid migration failure. Those rows should be corrected at the application/data level.
    batch_size = 500
    qs = Users.objects.all().only("UserId", "UserName", "Email", "username_hash", "email_hash")

    start = 0
    total = qs.count()
    while start < total:
        for u in qs.order_by("UserId")[start : start + batch_size]:
            username_val = getattr(u, "UserName", None) or ""
            email_val = getattr(u, "Email", None) or ""

            try:
                if decrypt_data and is_encrypted_data and isinstance(username_val, str) and is_encrypted_data(username_val):
                    username_val = decrypt_data(username_val) or username_val
            except Exception:
                pass

            try:
                if decrypt_data and is_encrypted_data and isinstance(email_val, str) and is_encrypted_data(email_val):
                    email_val = decrypt_data(email_val) or email_val
            except Exception:
                pass

            updates = {}
            if not getattr(u, "username_hash", None):
                if username_val:
                    updates["username_hash"] = _compute_sha256_hex(username_val)
                else:
                    updates["username_hash"] = _compute_sha256_hex(f"__missing_username__:{u.UserId}")

            if not getattr(u, "email_hash", None):
                if email_val:
                    updates["email_hash"] = _compute_sha256_hex(email_val)
                else:
                    updates["email_hash"] = _compute_sha256_hex(f"__missing_email__:{u.UserId}")

            if updates:
                Users.objects.filter(UserId=u.UserId).update(**updates)

        start += batch_size


class Migration(migrations.Migration):
    dependencies = [
        ("grc", "0003_add_multi_tenancy"),
    ]

    operations = [
        migrations.AddField(
            model_name="users",
            name="username_hash",
            field=models.CharField(max_length=64, null=True, blank=True, db_index=True),
        ),
        migrations.AddField(
            model_name="users",
            name="email_hash",
            field=models.CharField(max_length=64, null=True, blank=True, db_index=True),
        ),
        migrations.RunPython(backfill_user_identifier_hashes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="users",
            name="username_hash",
            field=models.CharField(max_length=64, null=False, blank=False, db_index=True, unique=True),
        ),
        migrations.AlterField(
            model_name="users",
            name="email_hash",
            field=models.CharField(max_length=64, null=False, blank=False, db_index=True, unique=True),
        ),
    ]

