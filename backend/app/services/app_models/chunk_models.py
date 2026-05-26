from pydantic import BaseModel

class Ranges(BaseModel):
    start: int
    end: int
    chapter_number: int | None = None
    chapter_title: str | None = None

class ChapterRangesFormat(BaseModel):
    chapter_ranges: list[Ranges]