from pydantic import BaseModel
from typing import Optional

class Course(BaseModel):
    id: int
    title: str
    description: str
    credits: int

class CourseCreate(BaseModel):
    title: str
    description: str
    credits: int

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
