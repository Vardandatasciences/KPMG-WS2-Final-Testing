"""
Decrypt Name and Code in company_folders when they were stored encrypted.

The company_folders table is not in ENCRYPTED_FIELDS_CONFIG, but some rows
have Name/Code containing Fernet ciphertext (e.g. gAAAAA...). This command
decrypts those values and writes plain text back so the UI and DB show
readable names and codes.

Usage:
    python manage.py decrypt_company_folders
    python manage.py decrypt_company_folders --dry-run
    python manage.py decrypt_company_folders --verbose   # show why decryption skipped/failed
    python manage.py decrypt_company_folders --test-key  # verify GRC_ENCRYPTION_KEY is loaded and works
"""
from django.core.management.base import BaseCommand
from grc.models import CompanyFolder
from grc.utils.auto_decrypt_helper import decrypt_any_encrypted_value
from grc.utils.data_encryption import encrypt_data, decrypt_data, get_encryption_service


def _looks_encrypted(s):
    """Match Fernet-style encrypted strings; DB may store with capital G."""
    if not s or not isinstance(s, str) or len(s) < 20:
        return False
    lower = s.lower()
    return (
        lower.startswith('gaaaaa') or
        (len(s) >= 6 and lower[1:6] == 'aaaaa') or
        (len(s) >= 7 and lower[:2] == 'bs' and lower[2:7] == 'aaaaa')
    )


class Command(BaseCommand):
    help = "Decrypt Name and Code in company_folders and save plain text back to the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only print what would be updated; do not save.',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print every folder with encrypted-looking data and whether decryption succeeded.',
        )
        parser.add_argument(
            '--test-key',
            action='store_true',
            help='Verify GRC_ENCRYPTION_KEY is loaded and can encrypt/decrypt; then try one stored value.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)
        test_key = options.get('test_key', False)

        if test_key:
            self._test_key()
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN – no changes will be saved.'))

        updated = 0
        encrypted_count = 0
        failed_decrypt_count = 0
        for folder in CompanyFolder.objects.all():
            name = folder.name or ''
            code = folder.code or ''
            name_enc = _looks_encrypted(name)
            code_enc = _looks_encrypted(code)
            if name_enc or code_enc:
                encrypted_count += 1

            new_name = decrypt_any_encrypted_value(name) if name_enc else name
            new_code = decrypt_any_encrypted_value(code) if code_enc else code

            if verbose and (name_enc or code_enc):
                self.stdout.write(f"FolderId={folder.folder_id}: name_enc={name_enc}, code_enc={code_enc}")
                if name_enc:
                    name_ok = not _looks_encrypted(new_name)
                    self.stdout.write(f"  Name decrypted OK: {name_ok} -> {repr((new_name or '')[:60])}...")
                    if not name_ok:
                        failed_decrypt_count += 1
                if code_enc:
                    code_ok = not _looks_encrypted(new_code)
                    self.stdout.write(f"  Code decrypted OK: {code_ok} -> {repr((new_code or '')[:60])}...")
                    if not code_ok:
                        failed_decrypt_count += 1

            if new_name != name or new_code != code:
                self.stdout.write(
                    f"FolderId={folder.folder_id}: Name {repr(name[:50])}... -> {repr((new_name or '')[:50])}..."
                )
                self.stdout.write(
                    f"  Code {repr(code[:50])}... -> {repr((new_code or '')[:50])}..."
                )
                if dry_run:
                    updated += 1
                else:
                    fields = []
                    if new_name and new_name != name and not _looks_encrypted(new_name):
                        folder.name = new_name[:255]
                        fields.append('name')
                    if new_code and new_code != code and not _looks_encrypted(new_code):
                        folder.code = new_code[:100]
                        fields.append('code')
                    if fields:
                        folder.save(update_fields=fields)
                        updated += 1
                    elif verbose and (name_enc or code_enc):
                        self.stdout.write(self.style.WARNING(
                            f"  Skipped saving: decryption failed (result still encrypted). "
                            "Check GRC_ENCRYPTION_KEY in .env matches the key used to encrypt this data."
                        ))

        self.stdout.write(self.style.SUCCESS(f"Done. {'Would update' if dry_run else 'Updated'} {updated} folder(s)."))
        if verbose:
            self.stdout.write(f"Folders with encrypted-looking Name/Code: {encrypted_count}. Failed decryptions: {failed_decrypt_count}")
            if failed_decrypt_count and not updated:
                self.stdout.write(self.style.WARNING(
                    "Decryption failed for all encrypted values. Set GRC_ENCRYPTION_KEY in .env to the key that was used to encrypt company_folders Name/Code."
                ))

    def _test_key(self):
        """Verify key is loaded and works; try decrypting one stored ciphertext."""
        self.stdout.write("Testing GRC_ENCRYPTION_KEY...")
        try:
            svc = get_encryption_service()
            plain = "test_company_folder"
            enc = encrypt_data(plain)
            dec = decrypt_data(enc)
            if dec == plain:
                self.stdout.write(self.style.SUCCESS("  Key is loaded and works (encrypt/decrypt OK)."))
            else:
                self.stdout.write(self.style.ERROR(f"  Key test failed: decrypt returned {repr(dec)[:50]}"))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Key not loaded or invalid: {e}"))
            return

        # Try to decrypt one stored encrypted code from DB
        sample = (
            CompanyFolder.objects.exclude(code__isnull=True)
            .exclude(code="")
            .filter(code__icontains="gaaaaa")
            .values_list("code", flat=True)
            .first()
        )
        if not sample:
            self.stdout.write("  No encrypted Code found in DB to test.")
            return
        self.stdout.write(f"  Trying to decrypt one stored Code (length {len(sample)})...")
        try:
            dec = decrypt_data(sample)
            if _looks_encrypted(dec):
                self.stdout.write(self.style.WARNING(
                    f"  Stored value decrypted but result still looks encrypted. "
                    "Data was likely encrypted with a different key. Use that key in GRC_ENCRYPTION_KEY (or add it to GRC_ENCRYPTION_KEYS)."
                ))
            else:
                self.stdout.write(self.style.SUCCESS(f"  Stored value decrypted OK -> {repr(dec)[:60]}..."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"  Stored value decrypt failed: {type(e).__name__}: {e}. "
                "Company folder Code was encrypted with a different key. Set GRC_ENCRYPTION_KEY to that key (or add it to GRC_ENCRYPTION_KEYS)."
            ))