from django.core.management.base import BaseCommand
from django.db import connection
from grc.models import Users
from grc.utils.data_encryption import decrypt_data, is_encrypted_data


class Command(BaseCommand):
    """
    One-time utility to decrypt all encrypted fields in the users table
    and store the plain-text values back in the database.

    IMPORTANT:
    - This command decrypts ALL encrypted fields in the users table
    - Uses direct SQL updates to bypass model save() method and prevent re-encryption
    - Does NOT affect any other tables
    - Ensure GRC_ENCRYPTION_KEY is configured with the SAME key used to encrypt the data

    Usage:
        python manage.py decrypt_users_table
    """

    help = "Decrypts all encrypted fields in the users table (UserName, Email, FirstName, LastName, PhoneNumber, Address, session_token, license_key)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be decrypted without actually updating the database',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Fields that are encrypted in the Users model (from encryption_config.py)
        encrypted_fields = [
            'UserName',
            'Email',
            'FirstName',
            'LastName',
            'PhoneNumber',
            'Address',
            'session_token',
            'license_key',
        ]

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING("Decrypting Users Table"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made to the database"))
        
        total_updated = 0
        total_fields_decrypted = 0
        errors = []

        # Get all users
        users = Users.objects.all()
        total_users = users.count()
        self.stdout.write(f"\nFound {total_users} user(s) to process\n")

        # Process each user
        for user in users.iterator(chunk_size=100):
            user_id = user.UserId
            changed = False
            update_data = {}

            for field_name in encrypted_fields:
                try:
                    # Get current field value
                    field_value = getattr(user, field_name, None)
                    
                    # Skip if field is None or empty
                    if not field_value or not isinstance(field_value, str):
                        continue
                    
                    # Check if field is encrypted
                    if is_encrypted_data(field_value):
                        # Decrypt the value
                        decrypted_value = decrypt_data(field_value)
                        
                        # Verify decryption worked and value changed
                        if decrypted_value and decrypted_value != field_value:
                            update_data[field_name] = decrypted_value
                            changed = True
                            total_fields_decrypted += 1
                            
                            if not dry_run:
                                self.stdout.write(
                                    f"  User {user_id}: Decrypting {field_name} "
                                    f"({len(field_value)} chars -> {len(decrypted_value)} chars)"
                                )
                            else:
                                self.stdout.write(
                                    f"  [DRY RUN] User {user_id}: Would decrypt {field_name} "
                                    f"({len(field_value)} chars -> {len(decrypted_value)} chars)"
                                )
                    else:
                        # Field is already plain text, skip
                        continue
                        
                except Exception as e:
                    error_msg = f"User {user_id}, field {field_name}: {str(e)}"
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(f"  ERROR: {error_msg}"))
                    continue

            # Update database if changes were made
            if changed:
                if not dry_run:
                    try:
                        # Use direct SQL update to bypass model save() method
                        # This prevents the EncryptedFieldsMixin from re-encrypting the values
                        with connection.cursor() as cursor:
                            set_clauses = []
                            params = []
                            
                            for field_name, value in update_data.items():
                                set_clauses.append(f"{field_name} = %s")
                                params.append(value)
                            
                            # Add UserId to params for WHERE clause
                            params.append(user_id)
                            
                            sql = f"""
                                UPDATE users 
                                SET {', '.join(set_clauses)}
                                WHERE UserId = %s
                            """
                            
                            cursor.execute(sql, params)
                            connection.commit()
                            
                            total_updated += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  ✓ User {user_id}: Updated {len(update_data)} field(s)"
                                )
                            )
                    except Exception as e:
                        error_msg = f"User {user_id}: Failed to update database - {str(e)}"
                        errors.append(error_msg)
                        self.stdout.write(self.style.ERROR(f"  ERROR: {error_msg}"))
                else:
                    # Dry run - just count
                    total_updated += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"  [DRY RUN] User {user_id}: Would update {len(update_data)} field(s)"
                        )
                    )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("SUMMARY"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Total users processed: {total_users}")
        self.stdout.write(f"Users with decrypted fields: {total_updated}")
        self.stdout.write(f"Total fields decrypted: {total_fields_decrypted}")
        
        if errors:
            self.stdout.write(self.style.ERROR(f"\nErrors encountered: {len(errors)}"))
            for error in errors[:10]:  # Show first 10 errors
                self.stdout.write(self.style.ERROR(f"  - {error}"))
            if len(errors) > 10:
                self.stdout.write(self.style.ERROR(f"  ... and {len(errors) - 10} more errors"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN completed - No changes were made"))
            self.stdout.write(self.style.WARNING("Run without --dry-run to apply changes"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Decryption completed successfully!"))
            self.stdout.write(self.style.WARNING(
                "\nIMPORTANT: To prevent re-encryption, you should remove 'Users' from "
                "ENCRYPTED_FIELDS_CONFIG in grc/utils/encryption_config.py"
            ))
