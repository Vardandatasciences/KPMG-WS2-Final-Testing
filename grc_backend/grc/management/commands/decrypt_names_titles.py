from django.core.management.base import BaseCommand

from grc.models import (
    Framework,
    Policy,
    SubPolicy,
    Compliance,
    Risk,
    RiskInstance,
    Incident,
    Event,
)
from grc.utils.data_encryption import decrypt_data, is_encrypted_data


class Command(BaseCommand):
    """
    One-time utility to decrypt previously encrypted *name/title* fields
    and store the plain-text values back in the database.

    IMPORTANT:
    - Run this ONLY after updating encryption_config.py so these fields are
      no longer listed in ENCRYPTED_FIELDS_CONFIG.
    - Ensure GRC_ENCRYPTION_KEY (or equivalent) is configured with the SAME
      key that was used to encrypt the existing data.

    Usage:
        python manage.py decrypt_names_titles
    """

    help = "Decrypts framework/policy/subpolicy/compliance/risk/incident/event name/title fields in-place."

    def handle(self, *args, **options):
        model_fields = [
            (Framework, ["FrameworkName"]),
            (Policy, ["PolicyName"]),
            (SubPolicy, ["SubPolicyName"]),
            (Compliance, ["ComplianceTitle"]),
            (Risk, ["RiskTitle"]),
            (RiskInstance, ["RiskTitle"]),
            (Incident, ["IncidentTitle"]),
            (Event, ["EventTitle"]),
        ]

        total_updated = 0

        for model, fields in model_fields:
            model_name = model.__name__
            self.stdout.write(self.style.MIGRATE_HEADING(f"Processing {model_name}..."))
            updated_for_model = 0

            # Iterate in chunks to avoid loading everything into memory.
            # NOTE: We will use queryset.update(...) to avoid triggering
            # model save() and post_save signals (e.g. retention timeline),
            # which makes this command much faster and side‑effect free.
            queryset = model.objects.all().only("pk", *fields)
            for obj in queryset.iterator(chunk_size=500):
                changed = False
                update_fields = []

                for field in fields:
                    value = getattr(obj, field, None)
                    if not value or not isinstance(value, str):
                        continue

                    # Only touch values that look encrypted
                    if is_encrypted_data(value):
                        plain = decrypt_data(value)
                        # If decryption worked and changed the value, write it back
                        if plain is not None and plain != value:
                            setattr(obj, field, plain)
                            update_fields.append(field)
                            changed = True

                if changed:
                    # Write decrypted values directly to DB without calling save()
                    # so that no signals (like retention timeline) are fired.
                    update_data = {field: getattr(obj, field) for field in update_fields}
                    model.objects.filter(pk=obj.pk).update(**update_data)
                    updated_for_model += 1
                    total_updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"{model_name}: decrypted & updated {updated_for_model} row(s)."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed. Total decrypted & updated rows across all models: {total_updated}"
            )
        )


