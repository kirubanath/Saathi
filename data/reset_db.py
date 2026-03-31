"""
Reset script: restores saathi.db from the saathi_seed.db snapshot.
MinIO artifacts are preserved (they don't change between runs).

Run from the project root:
    python data/reset_db.py
"""

import shutil

from config.settings import settings


def _db_path_from_url(url: str) -> str:
    return url.replace("sqlite:///", "")


def reset():
    db_path = _db_path_from_url(settings.DATABASE_URL)
    seed_path = _db_path_from_url(settings.SEED_DB_PATH)

    print(f"Restoring {seed_path} -> {db_path} ...")
    shutil.copy2(seed_path, db_path)
    print("Database restored.")


if __name__ == "__main__":
    reset()
