from typing import List

from pydantic import BaseModel, Field


class SubWord(BaseModel):
    word: str
    start_time: int
    end_time: int


class FlattedSub(BaseModel):
    text: str = ""
    words: List[SubWord] = Field([])
