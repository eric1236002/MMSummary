from __future__ import annotations

import json
from typing import Any, Optional

from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate

from backend.core import init_llm
from .state import EffectiveParams, Plan, ReviewResult


_PLANNER_TEMPLATE = """
    你是會議記錄摘要系統的 Planner。你的任務是根據輸入文字特性，決定摘要流程的參數（是否 map、chunk 參數、token_max、reduce_temperature），以提升摘要品質並控制成本。

    請只輸出 JSON（不要任何額外文字），格式如下：
    {
    "use_map": true|false|null,
    "chunk_size_1": number|null,
    "chunk_overlap_1": number|null,
    "chunk_size_2": number|null,
    "chunk_overlap_2": number|null,
    "token_max": number|null,
    "reduce_temperature": number|null,
    "notes": string|null
    }

    限制：
    - 若不確定就回 null，不要亂猜。
    - chunk_size 合理範圍：1000~32000；overlap：0~8000。
    - token_max 合理範圍：2000~32000。

    輸入文字長度（字元）：{text_length}
    目前參數：{current_params_json}

    文字內容：
    {text}
    """.strip()


_REVIEWER_TEMPLATE = """
    你是會議記錄摘要系統的 Reviewer。你要檢查摘要是否：
    1) 忠實於原文（避免幻想/捏造）
    2) 覆蓋關鍵決議/行動項/重要結論（若原文有）
    3) 結構清晰、可讀

    若需要修訂，請直接給出 revised_summary。

    請只輸出 JSON（不要任何額外文字），格式如下：
    {
    "verdict": "pass"|"revise",
    "revised_summary": string|null,
    "issues": [string]|null,
    "notes": string|null
    }

    原文：
    {text}

    摘要（草稿）：
    {draft_summary}
    """.strip()


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found")
    return json.loads(text[start : end + 1])


def plan_parameters(
    *,
    text: str,
    effective: EffectiveParams,
    planner_model: Optional[str] = None,
) -> Plan:
    llm = init_llm(temperature=0.0, model=planner_model or effective.model, max_tokens=800)
    prompt = PromptTemplate.from_template(_PLANNER_TEMPLATE)
    chain = LLMChain(llm=llm, prompt=prompt)

    res = chain.invoke(
        {
            "text": text,
            "text_length": len(text),
            "current_params_json": json.dumps(effective.to_dict(), ensure_ascii=False),
        }
    )

    if isinstance(res, dict):
        content = res.get("text") or res.get("output_text") or res.get("output")
    else:
        content = str(res)

    data = _extract_json(str(content))
    if not isinstance(data, dict):
        print("Planner response JSON is not a dict:", data)
        return Plan()
    return Plan(
        use_map=data.get("use_map"),
        chunk_size_1=data.get("chunk_size_1"),
        chunk_overlap_1=data.get("chunk_overlap_1"),
        chunk_size_2=data.get("chunk_size_2"),
        chunk_overlap_2=data.get("chunk_overlap_2"),
        token_max=data.get("token_max"),
        reduce_temperature=data.get("reduce_temperature"),
        notes=data.get("notes"),
    )


def review_summary(
    *,
    text: str,
    draft_summary: str,
    effective: EffectiveParams,
    reviewer_model: Optional[str] = None,
) -> ReviewResult:
    llm = init_llm(temperature=0.0, model=reviewer_model or effective.model, max_tokens=1200)
    prompt = PromptTemplate.from_template(_REVIEWER_TEMPLATE)
    chain = LLMChain(llm=llm, prompt=prompt)

    res = chain.invoke({"text": text, "draft_summary": draft_summary})

    if isinstance(res, dict):
        content = res.get("text") or res.get("output_text") or res.get("output")
    else:
        content = str(res)

    data = _extract_json(str(content))
    verdict = data.get("verdict") or "pass"
    return ReviewResult(
        verdict=verdict,
        revised_summary=data.get("revised_summary"),
        issues=data.get("issues"),
        notes=data.get("notes"),
    )
