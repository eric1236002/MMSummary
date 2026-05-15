from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import TextSplitRequest, TextSplitResponse, SummarizeRequest, SummarizeResponse, HistoryResponse
from backend.core import split_text, generate_summary
from backend.agents import summarize_with_agents
from backend.database import Database
import time
import os
import dotenv
dotenv.load_dotenv()
app = FastAPI(
    title="MMSummary API",
    description="API for meeting minutes summarization",
    version="1.0.0"
)


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
        raw_agent_mode = (request.agent_mode or "off").lower()

        if raw_agent_mode in {"on", "true", "1"}:
            agent_mode = "on"
        elif raw_agent_mode in {"off", "none", "false", "0", ""}:
            agent_mode = "off"
        else:
            agent_mode = raw_agent_mode


        planner_model = request.planner_model or request.agent_model
        reviewer_model = request.reviewer_model or request.agent_model

        def _is_openai_model(model_name: str) -> bool:
            return model_name.lower().startswith("gpt")

        # Key validation: depends on model provider(s)
        if not request.test_mode:
            models_to_check = [request.model]
            if agent_mode == "on":
                if planner_model:
                    models_to_check.append(planner_model)
                if reviewer_model:
                    models_to_check.append(reviewer_model)

            needs_openai = any(_is_openai_model(m) for m in models_to_check)
            needs_openrouter = any(not _is_openai_model(m) for m in models_to_check)

            if needs_openai and not os.environ.get("OPENAI_API_KEY"):
                raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set in environment.")
            if needs_openrouter and not os.environ.get("OPENROUTER_API_KEY"):
                raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set in environment.")

        agent_meta = None
        if agent_mode == "on":
            summary, agent_meta = summarize_with_agents(
                request=request,
                agent_mode=agent_mode,
                quality_check=request.quality_check,
                max_iters=request.max_iters,
                planner_model=planner_model,
                reviewer_model=reviewer_model,
            )
        else:
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
                direct_mode=request.direct_mode,
                map_template=request.map_temple,
                reduce_template=request.reduce_temple,
                reduce_temperature=request.reduce_temperature,
            )
        
        duration = time.time() - start_time
        
        if not request.test_mode:
            payload = {
                "text": request.text,
                "model": request.model,
                "chunk_size_1": request.chunk_size_1,
                "chunk_overlap_1": request.chunk_overlap_1,
                "chunk_size_2": request.chunk_size_2,
                "chunk_overlap_2": request.chunk_overlap_2,
                "token_max": request.token_max,
                "use_map": request.use_map,
                "direct_mode": request.direct_mode,
                "summary": summary,
                "processing_time": duration,
                "map_temple": request.map_temple,
                "reduce_temple": request.reduce_temple,
                "reduce_temperature": request.reduce_temperature
            }
            if agent_meta is not None:
                payload["agent_mode"] = agent_mode
                payload["agent_meta"] = agent_meta
            database.insert_history(payload)
        return SummarizeResponse(
            summary=summary,
            processing_time=duration,
            trace=agent_meta
        )
        
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
