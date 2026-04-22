from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Iterable

import numpy as np
from sqlalchemy.orm import Session

from app.models import Course

try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None


BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_DIR = BASE_DIR / "artifacts"
INDEX_PATH = INDEX_DIR / "courses.index"
METADATA_PATH = INDEX_DIR / "courses_metadata.json"
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
MIN_RESULT_SCORE = 0.12
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


class SearchService:
    def __init__(self) -> None:
        self.model = None
        self.index = None
        self.metadata = []
        self._load_index()

    def _load_index(self) -> None:
        if (
            faiss is None
            or SentenceTransformer is None
            or not INDEX_PATH.exists()
            or not METADATA_PATH.exists()
        ):
            return

        self.model = SentenceTransformer(MODEL_NAME)
        self.index = faiss.read_index(str(INDEX_PATH))
        with METADATA_PATH.open("r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def semantic_ready(self) -> bool:
        return self.model is not None and self.index is not None and bool(self.metadata)

    def search(
        self,
        db: Session,
        query: str,
        top_k: int = 5,
        level: str | None = None,
        department: str | None = None,
    ) -> list[dict]:
        if self.semantic_ready():
            return self._semantic_search(
                db, query, top_k, level=level, department=department
            )
        return self._keyword_fallback(
            db, query, top_k, level=level, department=department
        )

    def _semantic_search(
        self,
        db: Session,
        query: str,
        top_k: int,
        level: str | None = None,
        department: str | None = None,
    ) -> list[dict]:
        query_vector = self.model.encode([query], normalize_embeddings=True)
        query_terms = self._query_terms(query)
        candidate_k = min(max(15, top_k * 5), len(self.metadata))
        scores, indices = self.index.search(
            np.array(query_vector, dtype=np.float32), candidate_k
        )

        reranked = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            course_id = self.metadata[idx]["id"]
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                continue
            if level and level != "all" and (course.level or "").lower() != level.lower():
                continue
            if department and (course.department or "").lower() != department.lower():
                continue
            final_score, explanation = self._hybrid_score(
                course=course,
                query_terms=query_terms,
                semantic_score=float(score),
            )
            reranked.append(
                (
                    final_score,
                    {
                        "id": course.id,
                        "code": course.code,
                        "course_number": course.course_number,
                        "title": course.title,
                        "description": course.description,
                        "department": course.department,
                        "level": course.level,
                        "prerequisites": course.prerequisites,
                        "topics": course.topics,
                        "credits": course.credits,
                        "score": round(final_score, 3),
                        "match_reason": explanation,
                    },
                )
            )

        reranked.sort(key=lambda item: item[0], reverse=True)
        filtered = [result for score, result in reranked if score >= MIN_RESULT_SCORE]
        if filtered:
            return filtered[:top_k]
        return [result for _, result in reranked[: min(top_k, 3)]]

    def _keyword_fallback(
        self,
        db: Session,
        query: str,
        top_k: int,
        level: str | None = None,
        department: str | None = None,
    ) -> list[dict]:
        query_terms = self._query_terms(query)
        courses_query = db.query(Course)
        if level and level != "all":
            courses_query = courses_query.filter(Course.level == level)
        if department:
            courses_query = courses_query.filter(Course.department == department.upper())
        courses = courses_query.all()

        scored = []
        for course in courses:
            haystack = course.embedding_text().lower()
            overlap = sum(1 for term in query_terms if term in haystack)
            if overlap == 0:
                continue
            lexical_score = overlap / max(len(query_terms), 1)
            final_score, explanation = self._hybrid_score(
                course=course,
                query_terms=query_terms,
                semantic_score=lexical_score,
                semantic_weight=0.35,
            )
            scored.append(
                (
                    final_score,
                    {
                        "id": course.id,
                        "code": course.code,
                        "course_number": course.course_number,
                        "title": course.title,
                        "description": course.description,
                        "department": course.department,
                        "level": course.level,
                        "prerequisites": course.prerequisites,
                        "topics": course.topics,
                        "credits": course.credits,
                        "score": round(final_score, 3),
                        "match_reason": f"{explanation} Retrieved using keyword fallback because the semantic index is not available.",
                    },
                )
            )

        scored.sort(key=lambda item: item[0], reverse=True)
        filtered = [result for score, result in scored if score >= MIN_RESULT_SCORE]
        if filtered:
            return filtered[:top_k]
        return [result for _, result in scored[: min(top_k, 3)]]

    def _query_terms(self, query: str) -> list[str]:
        terms = re.findall(r"[a-zA-Z0-9]+", query.lower())
        return [term for term in terms if term not in STOPWORDS]

    def _overlap_ratio(self, query_terms: list[str], text: str | None) -> tuple[float, list[str]]:
        if not text:
            return 0.0, []
        text_lower = text.lower()
        matches = [term for term in query_terms if term in text_lower]
        ratio = len(matches) / max(len(query_terms), 1)
        return ratio, matches

    def _hybrid_score(
        self,
        *,
        course: Course,
        query_terms: list[str],
        semantic_score: float,
        semantic_weight: float = 0.65,
    ) -> tuple[float, str]:
        title_ratio, title_matches = self._overlap_ratio(query_terms, course.title)
        topic_ratio, topic_matches = self._overlap_ratio(query_terms, course.topics)
        prereq_ratio, prereq_matches = self._overlap_ratio(query_terms, course.prerequisites)
        desc_ratio, desc_matches = self._overlap_ratio(query_terms, course.description)

        semantic_component = max(0.0, min(1.0, semantic_score))
        title_component = min(1.0, title_ratio * 1.4)
        topic_component = min(1.0, topic_ratio * 1.25)
        prereq_component = prereq_ratio
        description_component = desc_ratio

        final_score = (
            semantic_weight * semantic_component
            + 0.15 * title_component
            + 0.10 * topic_component
            + 0.05 * prereq_component
            + 0.05 * description_component
        )

        reasons = []
        if semantic_component >= 0.5:
            reasons.append("strong semantic match")
        elif semantic_component >= 0.25:
            reasons.append("moderate semantic match")

        if title_matches:
            reasons.append(
                f"matched title terms: {', '.join(self._unique_terms(title_matches))}"
            )
        if topic_matches:
            reasons.append(
                f"matched topics: {', '.join(self._unique_terms(topic_matches))}"
            )
        if prereq_matches:
            reasons.append(
                f"related prerequisites: {', '.join(self._unique_terms(prereq_matches))}"
            )
        elif desc_matches:
            reasons.append(
                f"matched description terms: {', '.join(self._unique_terms(desc_matches[:3]))}"
            )

        if course.level:
            reasons.append(f"{course.level} course")

        explanation = ". ".join(reason.capitalize() for reason in reasons if reason)
        if explanation:
            explanation += "."
        else:
            explanation = "Relevant based on combined semantic and text matching."

        return final_score, explanation

    def _unique_terms(self, terms: list[str]) -> list[str]:
        seen = set()
        ordered = []
        for term in terms:
            if term in seen:
                continue
            seen.add(term)
            ordered.append(term)
        return ordered


def build_embedding_corpus(courses: Iterable[Course]) -> tuple[list[str], list[dict]]:
    texts = []
    metadata = []
    for course in courses:
        texts.append(course.embedding_text())
        metadata.append(
            {
                "id": course.id,
                "code": course.code,
                "title": course.title,
                "department": course.department,
                "level": course.level,
            }
        )
    return texts, metadata
