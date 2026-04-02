"""
Backfill script for Race Condition fix (Users.username_hash / Users.email_hash).

What it does (safe order):
1) Ensures `users.username_hash` and `users.email_hash` columns exist (adds them if missing)
2) Backfills hashes for all rows (decrypting UserName/Email if stored encrypted)
3) Detects duplicates (same hash used by multiple rows)
4) Optionally enforces NOT NULL + UNIQUE constraints (only if duplicates are resolved)

Run from repo root (recommended):
    python grc_backend/backfill_user_hashes.py

Notes:
- This script is intended for environments where you cannot/don't want to run migrations immediately.
- Best practice is still to use Django migrations; this script is a maintenance fallback.
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict

import django


def setup_django() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    django.setup()


def _plain(value: str) -> str:
    if not value:
        return ""
    try:
        from grc.utils.data_encryption import decrypt_data, is_encrypted_data

        if isinstance(value, str) and is_encrypted_data(value):
            return decrypt_data(value) or ""
    except Exception:
        pass
    return value


def _column_exists(cursor, table: str, column: str) -> bool:
    # Works on MySQL; for other DBs, Django connection introspection is used by default below.
    try:
        cursor.execute(f"SHOW COLUMNS FROM `{table}` LIKE %s", [column])
        return cursor.fetchone() is not None
    except Exception:
        return False


def ensure_columns_exist() -> None:
    from django.db import connection

    table = "users"
    with connection.cursor() as cursor:
        # Prefer DB introspection; fallback to MySQL SHOW COLUMNS.
        try:
            existing = {c.name for c in connection.introspection.get_table_description(cursor, table)}
            has_username_hash = "username_hash" in existing
            has_email_hash = "email_hash" in existing
        except Exception:
            has_username_hash = _column_exists(cursor, table, "username_hash")
            has_email_hash = _column_exists(cursor, table, "email_hash")

        if not has_username_hash:
            cursor.execute("ALTER TABLE `users` ADD COLUMN `username_hash` VARCHAR(64) NULL")
            cursor.execute("CREATE INDEX `users_username_hash_idx` ON `users` (`username_hash`)")
            print("Added column users.username_hash + index")
        else:
            print("Column users.username_hash already exists")

        if not has_email_hash:
            cursor.execute("ALTER TABLE `users` ADD COLUMN `email_hash` VARCHAR(64) NULL")
            cursor.execute("CREATE INDEX `users_email_hash_idx` ON `users` (`email_hash`)")
            print("Added column users.email_hash + index")
        else:
            print("Column users.email_hash already exists")


def backfill_hashes(*, chunk_size: int = 500) -> None:
    from django.db import transaction
    from grc.models import Users

    total = Users.objects.count()
    print(f"Backfilling hashes for {total} users...")

    updated = 0
    with transaction.atomic():
        qs = Users.objects.all().only("UserId", "UserName", "Email", "username_hash", "email_hash")
        for u in qs.iterator(chunk_size=chunk_size):
            uname_plain = _plain(u.UserName)
            email_plain = _plain(u.Email)

            new_username_hash = u.username_hash
            new_email_hash = u.email_hash

            if not new_username_hash:
                if uname_plain:
                    new_username_hash = Users.compute_identifier_hash(uname_plain, kind="username")
                else:
                    new_username_hash = Users.compute_identifier_hash(f"__missing_username__:{u.UserId}", kind="username")

            if not new_email_hash:
                if email_plain:
                    new_email_hash = Users.compute_identifier_hash(email_plain, kind="email")
                else:
                    new_email_hash = Users.compute_identifier_hash(f"__missing_email__:{u.UserId}", kind="email")

            if new_username_hash != u.username_hash or new_email_hash != u.email_hash:
                u.username_hash = new_username_hash
                u.email_hash = new_email_hash
                u.save(update_fields=["username_hash", "email_hash"])
                updated += 1

    print(f"Backfill done. Rows updated: {updated}")


def find_duplicates() -> dict[str, list[int]]:
    """
    Returns dict of {hash_value: [UserId, ...]} for hashes that appear >1 times.
    """
    from grc.models import Users

    dup_map: dict[str, list[int]] = defaultdict(list)

    # username_hash duplicates
    for row in Users.objects.values("UserId", "username_hash").iterator(chunk_size=1000):
        hv = row.get("username_hash")
        if hv:
            dup_map[f"username_hash:{hv}"].append(row["UserId"])

    # email_hash duplicates
    for row in Users.objects.values("UserId", "email_hash").iterator(chunk_size=1000):
        hv = row.get("email_hash")
        if hv:
            dup_map[f"email_hash:{hv}"].append(row["UserId"])

    # Filter only actual duplicates
    return {k: v for k, v in dup_map.items() if len(v) > 1}


def enforce_constraints() -> None:
    """
    Adds UNIQUE constraints for username_hash/email_hash if not present.
    Will error if duplicates exist.
    """
    from django.db import connection

    with connection.cursor() as cursor:
        # Make fields NOT NULL (assumes backfill already ran)
        cursor.execute("ALTER TABLE `users` MODIFY COLUMN `username_hash` VARCHAR(64) NOT NULL")
        cursor.execute("ALTER TABLE `users` MODIFY COLUMN `email_hash` VARCHAR(64) NOT NULL")

        # Add unique indexes if missing (MySQL)
        cursor.execute("CREATE UNIQUE INDEX `users_username_hash_uniq` ON `users` (`username_hash`)")
        cursor.execute("CREATE UNIQUE INDEX `users_email_hash_uniq` ON `users` (`email_hash`)")

    print("Constraints enforced: NOT NULL + UNIQUE on username_hash/email_hash")


def main() -> None:
    setup_django()

    # Step 1: columns
    ensure_columns_exist()

    # Step 2: backfill
    backfill_hashes()

    # Step 3: duplicates report
    dups = find_duplicates()
    if dups:
        print("\nDUPLICATES FOUND. Do NOT enforce UNIQUE constraints yet.")
        for k, user_ids in list(dups.items())[:50]:
            print(f"- {k} -> UserIds={user_ids}")
        if len(dups) > 50:
            print(f"... and {len(dups) - 50} more")
        print("\nResolve duplicates (merge/delete) then re-run this script with --enforce.")
        return

    # Step 4: enforce constraints (optional)
    if "--enforce" in sys.argv:
        enforce_constraints()
    else:
        print("\nNo duplicates detected. Re-run with --enforce to add UNIQUE constraints.")


if __name__ == "__main__":
    main()