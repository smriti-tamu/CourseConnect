# CourseConnect

CourseConnect is a semantic course discovery tool for Texas A&M course catalogs. The system allows users to enter a natural-language query such as `deep learning for computer vision` or `security in distributed systems` and returns ranked courses that are relevant to that topic.

The project combines catalog scraping, structured storage, embedding-based retrieval, and a lightweight web interface. It is intended as a prototype for helping students explore courses across departments more effectively than with keyword-only browsing.

## Features

- FastAPI backend for course search
- React frontend for natural-language queries
- Sentence-BERT embeddings for semantic retrieval
- FAISS index for nearest-neighbor search
- Hybrid reranking with title, topic, description, and prerequisite overlap
- Level filter for undergraduate and graduate courses
- TAMU catalog scraper for both undergraduate and graduate course indexes
- SQLite database for storing course records

## Project Structure

```text
courseconnect/
├── backend/
│   ├── app/
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── search.py
│   ├── data/
│   │   ├── sample_courses.json
│   │   └── scraped_courses.json
│   ├── scripts/
│   │   ├── build_index.py
│   │   ├── load_scraped_courses.py
│   │   └── scrape_catalog.py
│   ├── artifacts/
│   ├── requirements.txt
│   └── courseconnect.db
└── frontend/
    ├── index.html
    ├── package.json
    ├── src/
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── styles.css
    └── vite.config.js
```

## Requirements

- Python 3.13 or 3.14
- Node.js and npm
- Internet access for catalog scraping and first-time model download

## Running with Sample Data

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python -m app.database
python scripts/build_index.py
uvicorn app.main:app --reload
```

The backend runs at:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

- `http://127.0.0.1:5173`

## Running with Scraped TAMU Data

To replace the sample dataset with scraped course data:

```bash
cd backend
source .venv/bin/activate
rm -f courseconnect.db
python scripts/scrape_catalog.py
python scripts/load_scraped_courses.py
python scripts/build_index.py
uvicorn app.main:app --reload
```

What these scripts do:

- `scrape_catalog.py` discovers department pages from the TAMU undergraduate and graduate course indexes and saves the results to `backend/data/scraped_courses.json`
- `load_scraped_courses.py` loads the scraped JSON into SQLite
- `build_index.py` rebuilds the semantic search index from the current database contents

## Search Pipeline

CourseConnect uses a two-stage retrieval pipeline:

1. Candidate retrieval with Sentence-BERT embeddings and FAISS
2. Lightweight reranking using:
   - semantic similarity
   - title overlap
   - topic overlap
   - description overlap
   - prerequisite overlap

This makes the results more interpretable than raw nearest-neighbor search alone.

## Notes

- The scraper currently discovers department pages from:
  - `https://catalog.tamu.edu/undergraduate/course-descriptions/`
  - `https://catalog.tamu.edu/graduate/course-descriptions/`
- Scraping all departments can take some time because it fetches many catalog pages.
- Some course codes may appear more than once if they are exposed through different catalog origins; those entries are stored separately.
- The frontend currently searches across all departments by default and exposes a level filter.
- `sentence-transformers` downloads the model the first time the index is built.
- If you change the schema, delete `backend/courseconnect.db` and rebuild the FAISS index.

## Suggested Git Ignore

These files are usually local or generated and should not be committed:

```text
backend/.venv/
backend/courseconnect.db
backend/artifacts/
node_modules/
.DS_Store
```
