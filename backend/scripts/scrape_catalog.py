"""Scrape TAMU course pages by discovering department links from the catalog indexes."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests
from bs4 import BeautifulSoup


OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "scraped_courses.json"
UNDERGRADUATE_INDEX_URL = "https://catalog.tamu.edu/undergraduate/course-descriptions/"
GRADUATE_INDEX_URL = "https://catalog.tamu.edu/graduate/course-descriptions/"


def infer_level(course_number: str | None, default_level: str) -> str:
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


def fetch_html(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def normalize_space(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def discover_department_sources(
    index_url: str,
    *,
    level: str,
    allowed_departments: set[str] | None = None,
) -> list[dict]:
    html = fetch_html(index_url)
    soup = BeautifulSoup(html, "html.parser")
    pages = []
    seen = set()

    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        label = normalize_space(anchor.get_text(" ", strip=True))
        if not href:
            continue

        full_url = urljoin(index_url, href)
        match = re.search(r"/course-descriptions/([a-z0-9-]+)/?$", full_url)
        if not match:
            continue

        department = match.group(1).upper()
        if allowed_departments and department not in allowed_departments:
            continue
        if full_url in seen:
            continue

        seen.add(full_url)
        pages.append(
            {
                "url": full_url,
                "department": department,
                "level": level,
                "label": label,
            }
        )

    return pages


def parse_course_block(block, *, department: str, level: str, source_url: str) -> Optional[dict]:
    title_el = block.select_one(".courseblocktitle")
    desc_el = block.select_one(".courseblockdesc")

    if not title_el:
        return None

    title_text = normalize_space(title_el.get_text(" ", strip=True))
    desc_text = normalize_space(desc_el.get_text(" ", strip=True)) if desc_el else ""

    first_sentence = title_text.split(".", maxsplit=1)[0].strip()
    subject_pattern = re.escape(department)
    code_match = re.match(
        rf"^({subject_pattern}\s+\d{{3}}[A-Z]?(?:/[A-Z]{{4}}\s+\d{{3}}[A-Z]?)?)\s+(.*)$",
        first_sentence,
    )
    if not code_match:
        return None

    code = normalize_space(code_match.group(1))
    title = normalize_space(code_match.group(2))
    number_match = re.search(rf"{subject_pattern}\s+(\d{{3}}[A-Z]?)", code)
    course_number = number_match.group(1) if number_match else None

    credits_match = re.search(r"Credits?\s+([0-9]+(?:\s+to\s+[0-9]+)?)", title_text)

    prerequisites = None
    prereq_match = re.search(r"(Prerequisite[s]?:.*?)(?=Cross Listing:|$)", desc_text)
    if prereq_match:
        prerequisites = prereq_match.group(1).strip()

    description = desc_text
    if prerequisites:
        description = description.replace(prerequisites, "").strip()
    description = re.sub(r"Cross Listing:\s*.*?(\.\s*$|$)", "", description).strip()
    description = normalize_space(description)

    return {
        "code": code,
        "course_number": course_number,
        "title": title,
        "description": description,
        "department": department,
        "level": infer_level(course_number, level),
        "catalog_origin": level,
        "prerequisites": prerequisites,
        "topics": None,
        "credits": credits_match.group(1) if credits_match else None,
        "source_url": source_url,
    }


def parse_courses(html: str, *, department: str, level: str, source_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    courses = []

    for block in soup.select(".courseblock"):
        course = parse_course_block(
            block,
            department=department,
            level=level,
            source_url=source_url,
        )
        if course:
            courses.append(course)

    return courses


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    pages = []
    pages.extend(
        discover_department_sources(
            UNDERGRADUATE_INDEX_URL,
            level="undergraduate",
        )
    )
    pages.extend(
        discover_department_sources(
            GRADUATE_INDEX_URL,
            level="graduate",
        )
    )

    all_courses = []
    for page in pages:
        html = fetch_html(page["url"])
        all_courses.extend(
            parse_courses(
                html,
                department=page["department"],
                level=page["level"],
                source_url=page["url"],
            )
        )

    OUTPUT_PATH.write_text(json.dumps(all_courses, indent=2), encoding="utf-8")
    print(f"Found {len(pages)} department pages.")
    print(f"Saved {len(all_courses)} courses to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
