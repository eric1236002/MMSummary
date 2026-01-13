from pydantic import BaseModel
from typing import Optional, List


class TextSplitRequest(BaseModel):
    text: str
    chunk_size: int = 16000
    chunk_overlap: int = 4000


class TextSplitResponse(BaseModel):
    chunks: List[str]
    total_chunks: int

class SummarizeRequest(BaseModel):
    text: str
    chunk_size_1: int = 16000
    chunk_overlap_1: int = 4000
    chunk_size_2: int = 8000
    chunk_overlap_2: int = 0
    token_max: int = 16000
    temperature: float = 0.0
    model: str = "gpt-5-mini"
    use_map: bool = True
    test_mode: bool = False
    reduce_temple: Optional[str] = None
    map_temple: Optional[str] = None
    reduce_temperature: float = 0.0
    language: str = "Traditional Chinese"

class SummarizeResponse(BaseModel):
    summary: str
    processing_time: float

class HistoryResponse(BaseModel):
    id: str
    original_text: str
    summary: str
    model: str
    processing_time: float
    created_at: str
