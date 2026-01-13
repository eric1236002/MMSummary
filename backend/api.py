from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import TextSplitRequest, TextSplitResponse, SummarizeRequest, SummarizeResponse, HistoryResponse
from backend.core import split_text, generate_summary
from backend.database import Database
import time
import os
import dotenv
dotenv.load_dotenv()
app = FastAPI(title="MMSummary API", description="API for meeting minutes summarization")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
database = Database()

@app.get("/")
def read_root():
    return {"message": "Welcome to MMSummary API"}

@app.get("/DB_health")
def health_check():
    try:
        database.client.admin.command('ping')
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/split", response_model=TextSplitResponse)
def api_split_text(request: TextSplitRequest):
    """
    Split the text into chunks
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
    Summarize the text
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
            use_map=request.use_map,
            test_mode=request.test_mode,
            map_template=request.map_temple,
            reduce_template=request.reduce_temple,
            reduce_temperature=request.reduce_temperature,
            language=request.language
        )
        
        duration = time.time() - start_time
        
        if not request.test_mode:
            database.insert_history({
                "text": request.text,
                "model": request.model,
                "chunk_size_1": request.chunk_size_1,
                "chunk_overlap_1": request.chunk_overlap_1,
                "chunk_size_2": request.chunk_size_2,
                "chunk_overlap_2": request.chunk_overlap_2,
                "token_max": request.token_max,
                "use_map": request.use_map,
                "summary": summary,
                "processing_time": duration,
                "map_temple": request.map_temple,
                "reduce_temple": request.reduce_temple,
                "reduce_temperature": request.reduce_temperature,
                "language": request.language
            })
        return SummarizeResponse(summary=summary, processing_time=duration)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history", response_model=list[HistoryResponse])
def api_history():
    try:
        return database.get_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/history/{id}")
def api_delete_history(id: str):
    try:
        result = database.delete_history(id)
        return {"status": "ok", "deleted_count": result.deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
