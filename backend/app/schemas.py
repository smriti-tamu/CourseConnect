from typing import Optional

from pydantic import BaseModel


class CourseBase(BaseModel):
    code: str
    course_number: Optional[str] = None
    title: str
    description: str
    department: Optional[str] = None
    level: Optional[str] = None
    catalog_origin: Optional[str] = None
    prerequisites: Optional[str] = None
    topics: Optional[str] = None
    credits: Optional[str] = None
    source_url: Optional[str] = None


class CourseRead(CourseBase):
    id: int

    model_config = {"from_attributes": True}


class SearchResult(CourseRead):
    score: float
    match_reason: str
