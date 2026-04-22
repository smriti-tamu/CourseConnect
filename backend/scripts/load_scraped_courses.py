import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session

from app.database import DATA_DIR, engine, init_db
from app.models import Course


SCRAPED_PATH = DATA_DIR / "scraped_courses.json"


def infer_level(course_number: str | None, default_level: str | None) -> str | None:
    if not course_number:
        return default_level
    digits_match = re.match(r"(\d+)", course_number)
    if not digits_match:
        return default_level
    number = int(digits_match.group(1))
    if number >= 600:
        return "graduate"
    if number <= 499:
        return "undergraduate"
    return default_level


def clean_record(item: dict) -> dict:
    course_number = (
        str(item.get("course_number"))
        if item.get("course_number") is not None
        else None
    )
    default_level = item.get("level")
    return {
        "code": item.get("code"),
        "course_number": course_number,
        "title": item.get("title"),
        "description": item.get("description") or "",
        "department": item.get("department"),
        "level": infer_level(course_number, default_level),
        "catalog_origin": item.get("catalog_origin"),
        "prerequisites": item.get("prerequisites"),
        "topics": item.get("topics"),
        "credits": str(item.get("credits")) if item.get("credits") is not None else None,
        "source_url": item.get("source_url"),
    }


def main():
    init_db()
    if not SCRAPED_PATH.exists():
        raise FileNotFoundError(
            f"Missing scraped dataset at {SCRAPED_PATH}. Run python scripts/scrape_catalog.py first."
        )

    with SCRAPED_PATH.open("r", encoding="utf-8") as f:
        rows = json.load(f)

    courses = []
    for item in rows:
        record = clean_record(item)
        if not record["code"]:
            continue
        courses.append(record)

    with Session(engine) as session:
        deleted = session.query(Course).delete()
        session.commit()

        for record in courses:
            session.add(Course(**record))
        session.commit()

    print(f"Loaded {len(courses)} scraped courses into the database.")
    print(f"Replaced {deleted} existing course rows.")


if __name__ == "__main__":
    main()
