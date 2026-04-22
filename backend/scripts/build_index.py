import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.database import engine, has_courses, init_db, seed_sample_courses
from app.models import Course
from app.search import INDEX_DIR, INDEX_PATH, METADATA_PATH, build_embedding_corpus

import faiss  # type: ignore


MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"


def main():
    init_db()
    if not has_courses():
        seed_sample_courses()
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    with Session(engine) as session:
        courses = session.query(Course).order_by(Course.id.asc()).all()

    texts, metadata = build_embedding_corpus(courses)
    if not texts:
        raise ValueError("No courses found. Seed or scrape data before building the index.")

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(texts, normalize_embeddings=True)
    vectors = np.array(embeddings, dtype=np.float32)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(INDEX_PATH))
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Saved FAISS index to {INDEX_PATH}")
    print(f"Saved metadata to {METADATA_PATH}")


if __name__ == "__main__":
    main()
