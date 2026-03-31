import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "saathi")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///saathi.db")
    SEED_DB_PATH: str = os.getenv("SEED_DB_PATH", "sqlite:///saathi_seed.db")

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "prototype")


settings = Settings()
