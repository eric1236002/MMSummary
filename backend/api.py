from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import TextSplitRequest, TextSplitResponse, SummarizeRequest, SummarizeResponse
from backend.core import split_text, generate_summary
import time
import os
import dotenv
dotenv.load_dotenv()
app = FastAPI(title="MMSummary API", description="API for meeting minutes summarization")

# 新增 CORS 中端點設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 在開發環境允許所有來源，生產環境應限制網域
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to MMSummary API"}

@app.post("/split", response_model=TextSplitResponse)
def api_split_text(request: TextSplitRequest):
    """
    測試用 Endpoint：僅執行文本切分
    """
    try:
        docs = split_text(request.text, request.chunk_size, request.chunk_overlap)
        chunks = [doc.page_content for doc in docs]
        return TextSplitResponse(chunks=chunks, total_chunks=len(chunks))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize", response_model=SummarizeResponse)
def api_summarize(request: SummarizeRequest):
    """
    執行完整的摘要流程
    """
    start_time = time.time()
    try:
        if not os.environ.get('OPENAI_API_KEY'):
            raise HTTPException(status_code=500, detail="OpenAI API Key not set in environment.")

        summary = generate_summary(
            text=request.text,
            model=request.model,
            chunk_size_1=request.chunk_size_1,
            chunk_overlap_1=request.chunk_overlap_1,
            chunk_size_2=request.chunk_size_2,
            chunk_overlap_2=request.chunk_overlap_2,
            token_max=request.token_max,
            use_map=request.use_map
        )
        
        duration = time.time() - start_time
        return SummarizeResponse(summary=summary, processing_time=duration)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
