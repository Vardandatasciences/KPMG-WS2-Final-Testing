import sys
from pathlib import Path


def try_import(path_entries):
    for entry in path_entries:
        if entry not in sys.path:
            sys.path.insert(0, entry)
    try:
        from backend.grc.routes.Global.s3_fucntions_kpi import (
            upload_bytes_via_microservice,  # type: ignore
        )
        print("Imported from backend.grc.routes.Global.s3_fucntions_kpi")
        return True
    except ModuleNotFoundError:
        try:
            from grc.routes.Global.s3_fucntions_kpi import (
                upload_bytes_via_microservice,  # type: ignore
            )
            print("Imported from grc.routes.Global.s3_fucntions_kpi")
            return True
        except ModuleNotFoundError:
            return False


if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    backend_root = current_dir.parent
    project_root = backend_root.parent

    attempts = [
        [str(project_root)],
        [str(backend_root)],
        [str(project_root), str(backend_root)],
    ]

    for idx, entries in enumerate(attempts, 1):
        print(f"Attempt {idx}: trying sys.path entries {entries}")
        if try_import(entries):
            print("Success!")
            break
    else:
        print("Failed to import upload_bytes_via_microservice after all attempts.")
        print("sys.path (first 10 entries):")
        for p in sys.path[:10]:
            print("  ", p)

