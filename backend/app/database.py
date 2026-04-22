import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, Course


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "courseconnect.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)


def seed_sample_courses():
    init_db()
    sample_path = DATA_DIR / "sample_courses.json"
    if not sample_path.exists():
        raise FileNotFoundError(f"Missing sample dataset at {sample_path}")

    with sample_path.open("r", encoding="utf-8") as f:
        courses = json.load(f)

    with Session(engine) as session:
        existing_codes = {
            code for (code,) in session.query(Course.code).all()
        }
        for item in courses:
            if item["code"] in existing_codes:
                continue
            session.add(Course(**item))
        session.commit()


def has_courses() -> bool:
    init_db()
    with Session(engine) as session:
        return session.query(Course.id).first() is not None


if __name__ == "__main__":
    seed_sample_courses()
    print(f"Database initialized at {DB_PATH}")
