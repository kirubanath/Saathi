from db.base import engine, Base
import db.models  # noqa: F401 — registers all models with Base


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


if __name__ == "__main__":
    init_db()
