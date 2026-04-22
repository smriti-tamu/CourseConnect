from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), nullable=False, index=True)
    course_number = Column(String(16), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    department = Column(String(16), nullable=True, index=True)
    level = Column(String(32), nullable=True, index=True)
    catalog_origin = Column(String(32), nullable=True, index=True)
    prerequisites = Column(Text, nullable=True)
    topics = Column(Text, nullable=True)
    credits = Column(String(32), nullable=True)
    source_url = Column(Text, nullable=True)

    def embedding_text(self) -> str:
        parts = [
            self.code or "",
            self.title or "",
            self.description or "",
            self.prerequisites or "",
            self.topics or "",
        ]
        return " ".join(part.strip() for part in parts if part and part.strip())
