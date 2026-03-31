"""
Reset script: restores saathi.db from the saathi_seed.db snapshot, clears MinIO
artifacts, and re-runs preprocessing for all 7 aspiration videos.

Run from the project root:
    python data/reset_db.py
"""

import shutil

from config.settings import settings
from storage.minio_client import MinIOClient


def _db_path_from_url(url: str) -> str:
    return url.replace("sqlite:///", "")


def reset():
    db_path = _db_path_from_url(settings.DATABASE_URL)
    seed_path = _db_path_from_url(settings.SEED_DB_PATH)

    print(f"Restoring {seed_path} -> {db_path} ...")
    shutil.copy2(seed_path, db_path)
    print("Database restored.")

    print("Clearing MinIO artifacts...")
    storage = MinIOClient()
    keys = storage.list_keys("videos/")
    for key in keys:
        storage._client.remove_object(settings.MINIO_BUCKET, key)
    print(f"  {len(keys)} object(s) removed from MinIO.")

    print("Re-running preprocessing pipeline...")
    try:
        from preprocessing.pipeline import preprocess_all
        preprocess_all()
        print("Preprocessing complete.")
    except ImportError:
        print("  Preprocessing pipeline not yet available — skipping.")

    print("Reset complete.")


if __name__ == "__main__":
    reset()
