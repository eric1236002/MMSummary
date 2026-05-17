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
    description="API for Meeting Minutes Summarization Service",
    version="1.0.6"
)

# 註解：這個檔案負責暴露 HTTP API，將外部請求轉成內部呼叫（core / agents / database）。
# 設計要點：
# - 路由保持輕量：盡量在 controller 層做輸入轉換、驗證與紀錄，實際邏輯委派給 backend.core / backend.agents。
# - 測試模式（test_mode）會跳過會造成非決定性或高成本的檢查/紀錄，方便寫穩定的單元測試。
# - agent flow（planner/reviewer）為選用功能，可透過 `agent_mode` 開關控制，以便在成本或延遲敏感時關閉。

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
    # 註解：此路由負責下列工作：
    # 1) 正規化輸入（例如把 agent_mode 接受多種 truthy/falsey 表示）
    # 2) 驗證必要的 API key（視所使用的模型供應商而定）
    # 3) 決定走 agent orchestration 還是直接呼叫 generate_summary
    # 4) 非測試模式下將輸入/結果寫入資料庫以供歷史查詢
    #
    # 設計理由：把這些邏輯放在 API 層可以避免模型/執行流程耦合到 HTTP 層，
    # 並且保留對外介面的清楚行為（例如 test_mode 不會寫入 DB，也不需要 API key）。
    start_time = time.time()
    try:
        # Normalize agent_mode: accept several truthy/falsey values from clients
        # 為何要 normalize：前端或客戶端可能透過表單或 query 傳入不同字串，統一處理減少錯誤。
        raw_agent_mode = (request.agent_mode or "off").lower()

        if raw_agent_mode in {"on", "true", "1"}:
            agent_mode = "on"
        elif raw_agent_mode in {"off", "none", "false", "0", ""}:
            agent_mode = "off"
        else:
            agent_mode = raw_agent_mode


        # 選擇 planner/reviewer model：若未指定，fallback 到 agent_model
        planner_model = request.planner_model or request.agent_model
        reviewer_model = request.reviewer_model or request.agent_model

        def _is_openai_model(model_name: str) -> bool:
            return model_name.lower().startswith("gpt")

        # Key validation: depends on model provider(s)
        # 理由：不同模型供應商可能需要不同的 API key。此處透過 model 名稱簡單判定，
        # 以避免在執行到呼叫模型時才發現缺少金鑰導致失敗。
        if not request.test_mode:
            models_to_check = [request.model]
            if agent_mode == "on":
                if planner_model:
                    models_to_check.append(planner_model)
                if reviewer_model:
                    models_to_check.append(reviewer_model)

            # 若任何 model 名稱看起來是 OpenAI（例如以 'gpt' 開頭），就檢查 `OPENAI_API_KEY`。
            # 反之則簡單地要求 `OPENROUTER_API_KEY`。這是輕量的檢查；複雜情況可改成更精確的 provider mapping。
            needs_openai = any(_is_openai_model(m) for m in models_to_check)
            needs_openrouter = any(not _is_openai_model(m) for m in models_to_check)

            if needs_openai and not os.environ.get("OPENAI_API_KEY"):
                raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set in environment.")
            if needs_openrouter and not os.environ.get("OPENROUTER_API_KEY"):
                raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set in environment.")

        # 預設 agent_meta 為 None；若啟用 agent flow，summarize_with_agents 會回傳 meta
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
                # 注意：schemas 使用的是 `map_temple` / `reduce_temple`（typo），
                # 在內部我們直接把值傳下去，未改動公共 API 欄位名稱以避免向後相容性問題。
                map_template=request.map_temple,
                reduce_template=request.reduce_temple,
                reduce_temperature=request.reduce_temperature,
            )
        
        duration = time.time() - start_time
        
        if not request.test_mode:
            # 儲存使用紀錄（非測試模式）：包含輸入參數與生成的摘要，方便後續查詢與除錯。
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
                # 保持與 schema 一致的欄位名稱（即使拼字是 temple），以免現有客戶端或 DB schema 出錯。
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
