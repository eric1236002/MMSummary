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
    use_map: bool = True # 對應 UI 上的 button (False = 使用 Map, True = 不使用 Map -> 變數名稱有點反直覺，這裡我定義正向參數)

class SummarizeResponse(BaseModel):
    summary: str
    processing_time: float
