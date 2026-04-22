from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, init_db, seed_sample_courses
from app.models import Course
from app.schemas import CourseRead, SearchResult
from app.search import SearchService


app = FastAPI(title="CourseConnect API", version="0.1.0")
search_service = SearchService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    seed_sample_courses()
    search_service._load_index()


@app.get("/")
def root():
    return {
        "message": "CourseConnect API is running",
        "semantic_index_loaded": search_service.semantic_ready(),
    }


@app.get("/courses", response_model=list[CourseRead])
def list_courses(db: Session = Depends(get_db)):
    return db.query(Course).order_by(Course.code.asc()).all()


@app.get("/search", response_model=list[SearchResult])
def search_courses(
    q: str = Query(..., min_length=2, description="Natural language search query"),
    top_k: int = Query(5, ge=1, le=20),
    level: str | None = Query(None, description="all, undergraduate, or graduate"),
    department: str | None = Query(None, description="Department code such as CSCE"),
    db: Session = Depends(get_db),
):
    return search_service.search(
        db, q, top_k=top_k, level=level, department=department
    )
