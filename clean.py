import re
from pathlib import Path

# -----------------------------
# CONFIG: set your dump folder
# -----------------------------
DUMP_FOLDER = Path(r"C:\Users\Admin\Documents\dumps\Dump_ITSM")

# Output mode:
# 1) same folder with suffix _clean.sql  (default)
# 2) write into a subfolder "_cleaned" inside the dump folder
WRITE_TO_SUBFOLDER = False  # set True if you prefer a _cleaned folder

# If True: replace DEFINER=`user`@`host` with DEFINER=CURRENT_USER (recommended)
FIX_DEFINER = True


def clean_sql(text: str) -> str:
    """
    Remove or neutralize statements that require admin privileges on managed MySQL,
    commonly causing ERROR 1227 during restore.

    Also optionally fixes DEFINER clauses.
    """

    # 1) Remove GTID_PURGED set (very common culprit)
    text = re.sub(
        r'(?im)^\s*SET\s+@@GLOBAL\.GTID_PURGED\s*=\s*.*?;\s*$',
        '',
        text
    )

    # 2) Remove any SET GLOBAL ... (requires elevated privileges)
    text = re.sub(
        r'(?im)^\s*SET\s+GLOBAL\s+.*?;\s*$',
        '',
        text
    )

    # 3) Remove any SET @@GLOBAL.... (also privileged for many vars)
    text = re.sub(
        r'(?im)^\s*SET\s+@@GLOBAL\..*?;\s*$',
        '',
        text
    )

    # 4) Remove sql_log_bin toggles (privileged in managed services)
    #    (some dumps contain SET @@SESSION.sql_log_bin = 0; or SET sql_log_bin = 0;)
    text = re.sub(
        r'(?im)^\s*SET\s+@@SESSION\.sql_log_bin\s*=\s*.*?;\s*$',
        '',
        text
    )
    text = re.sub(
        r'(?im)^\s*SET\s+sql_log_bin\s*=\s*.*?;\s*$',
        '',
        text
    )

    # 5) Optional: Replace DEFINER to avoid "You do not have the SUPER privilege..." when creating views/procs/triggers
    if FIX_DEFINER:
        # Handles patterns like: DEFINER=`root`@`%`
        text = re.sub(
            r'(?im)DEFINER\s*=\s*`[^`]+`\s*@\s*`[^`]+`',
            'DEFINER=CURRENT_USER',
            text
        )
        # Sometimes appears without backticks: DEFINER=root@%
        text = re.sub(
            r'(?im)DEFINER\s*=\s*[^ \t\r\n]+@[^ \t\r\n]+',
            'DEFINER=CURRENT_USER',
            text
        )

    # 6) Cleanup: collapse too many blank lines (optional, keeps file readable)
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    return text


def main():
    if not DUMP_FOLDER.exists():
        raise FileNotFoundError(f"Dump folder not found: {DUMP_FOLDER}")

    sql_files = sorted(DUMP_FOLDER.glob("*.sql"))
    if not sql_files:
        print(f"No .sql files found in: {DUMP_FOLDER}")
        return

    if WRITE_TO_SUBFOLDER:
        out_dir = DUMP_FOLDER / "_cleaned"
        out_dir.mkdir(exist_ok=True)
    else:
        out_dir = DUMP_FOLDER

    converted = 0
    skipped = 0

    for f in sql_files:
        # Avoid re-processing already cleaned files
        if f.name.endswith("_clean.sql"):
            skipped += 1
            continue

        raw = f.read_text(encoding="utf-8", errors="replace")
        cleaned = clean_sql(raw)

        if WRITE_TO_SUBFOLDER:
            out_path = out_dir / f.name
        else:
            out_path = out_dir / f"{f.stem}_clean.sql"

        out_path.write_text(cleaned, encoding="utf-8")
        converted += 1
        print(f"✅ Cleaned: {f.name}  ->  {out_path.name}")

    print("\n-------------------------")
    print(f"Done. Converted: {converted}, Skipped: {skipped}")
    print(f"Output folder: {out_dir}")
    print("-------------------------\n")


if __name__ == "__main__":
    main()
