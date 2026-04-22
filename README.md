# CourseConnect Starter

CourseConnect is a starter implementation of a semantic course discovery tool. This scaffold includes:

- A FastAPI backend
- A sample course dataset
- A scraper starter for Texas A&M catalog index discovery
- A loader for importing scraped catalog data into SQLite
- A Sentence-BERT + FAISS indexing pipeline
- A React frontend for natural-language search

This is designed to help your team get from proposal to working prototype quickly.

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
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── package.json
    ├── src/
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── styles.css
    └── vite.config.js
```

## What This Starter Already Does

- Stores courses in SQLite with SQLAlchemy
- Exposes a REST API for listing and searching courses
- Builds semantic embeddings with `sentence-transformers`
- Indexes vectors with FAISS
- Displays ranked results in a simple React UI
- Supports filtering by course level
- Scrapes both undergraduate and graduate catalog indexes
- Stores duplicate course codes separately when they come from different catalog origins
- Falls back to a lightweight keyword scorer if the semantic index is not built yet

## Quick Start

### 1. Backend setup

```bash
cd /Users/smritis/Documents/Codex/2026-04-22-courseconnect-a-tool-for-discovering-relevant/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

If you already created the virtual environment with an older dependency set and `pip install` failed, recreate it before retrying:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 2. Seed the database with sample data

```bash
python -m app.database
```

### 3. Build the semantic index

```bash
python scripts/build_index.py
```

### 4. Run the backend

```bash
uvicorn app.main:app --reload
```

Backend URL:

- `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

### 5. Frontend setup

In a second terminal:

```bash
cd /Users/smritis/Documents/Codex/2026-04-22-courseconnect-a-tool-for-discovering-relevant/frontend
npm install
npm run dev
```

Frontend URL:

- `http://127.0.0.1:5173`

## Real Data Workflow

If you want to use scraped TAMU data instead of the sample dataset:

```bash
cd /Users/smritis/Documents/Codex/2026-04-22-courseconnect-a-tool-for-discovering-relevant/backend
source .venv/bin/activate
rm -f courseconnect.db
python scripts/scrape_catalog.py
python scripts/load_scraped_courses.py
python scripts/build_index.py
uvicorn app.main:app --reload
```

What each step does:

- `scrape_catalog.py` discovers department pages from the TAMU undergraduate and graduate course indexes and writes `scraped_courses.json`
- `load_scraped_courses.py` clears the `courses` table and loads the scraped JSON into SQLite
- `build_index.py` rebuilds the embedding index from whatever is currently in the database

## Suggested Development Plan

### Phase 1: Get a demo running

1. Run the sample dataset end to end.
2. Verify that a query like `deep learning for computer vision` returns relevant results.
3. Use the frontend during your presentation as an initial proof of concept.

### Phase 2: Scrape real course data

1. Discover department pages automatically from the TAMU undergraduate and graduate course descriptions indexes.
2. Scrape department subject pages into JSON.
3. Load the scraped JSON into SQLite.
4. Rebuild the semantic index.

### Phase 3: Improve ranking

1. Add syllabus topics when available.
2. Combine description, title, and topics into a richer embedding text.
3. Add optional boosts for prerequisite alignment or topic matches.
4. Log queries and manually inspect ranking quality.

### Phase 4: Polish for presentation

1. Improve UI styling and add loading states.
2. Add a relevance score explanation.
3. Prepare 2-3 demo queries.
4. Compare manual catalog browsing versus CourseConnect.

## Recommended Team Split

1. One teammate on scraping and data cleaning
2. One teammate on embeddings, FAISS, and ranking
3. One teammate on FastAPI and database/API integration
4. One teammate on React frontend and demo polish

## Notes

- Real TAMU pages may change structure over time, so the scraper should be treated as a starting point.
- The current scraper discovers department pages from:
  - `https://catalog.tamu.edu/undergraduate/course-descriptions/`
  - `https://catalog.tamu.edu/graduate/course-descriptions/`
- It currently scrapes all discovered undergraduate and graduate department subject pages from those indexes.
- The frontend currently searches across all departments by default and only exposes a level filter.
- `sentence-transformers` downloads the model the first time you run the indexing script.
- If FAISS or embeddings are not ready, the backend still provides a keyword-based fallback so you can keep developing.
- Python 3.14 needs a newer `pydantic`/`pydantic-core` line than older 2025-era pins. This starter now uses a compatible range.
- If you change the schema or seed data shape, delete `backend/courseconnect.db` and rebuild the index so SQLite and FAISS stay in sync.
