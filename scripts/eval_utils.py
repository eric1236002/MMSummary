import json
import os
import re
import statistics
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from rouge_score import rouge_scorer
from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu

@dataclass(frozen=True)
class Example:
    # `Example` 用來統一表示評估資料的一筆樣本，避免在不同流程裡重複處理欄位名稱。
    id: str
    transcript: str
    reference_summary: str
    split: str = "test"

def as_text(value: Any) -> str:
    # 這個 helper 負責把不同型態的輸入資料轉成純文字，方便後續拿來做摘要評估。
    # 它支援 string / list / dict，避免資料來源格式不一致時每個呼叫端都要自己處理。
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: List[str] = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("utterance") or item.get("content")
                speaker = item.get("speaker") or item.get("role") or item.get("name")
                if speaker and text:
                    parts.append(f"{speaker}: {text}")
                elif text:
                    parts.append(str(text))
                else:
                    parts.append(json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)

def load_ids(path: str) -> Optional[List[str]]:
    # 如果有提供 ids 檔，就從 JSON list 讀取指定樣本 ID；沒有提供則回傳 None。
    if not path:
        return None
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return [str(x) for x in data]
    raise ValueError(f"ids file must be a JSON list: {path}")

def save_ids(path: str, ids: Sequence[str]) -> None:
    # 把抽樣到的 ID 存回檔案，方便之後重跑同一批資料得到可重現的結果。
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, ensure_ascii=False, indent=2)

def load_records_file(path: str) -> List[Dict[str, Any]]:
    # 讀取本地資料檔，支援 parquet / JSON / JSONL 三種常見格式。
    # 這讓評估腳本除了 Hugging Face dataset，也能直接吃本地實驗資料。
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    if path.lower().endswith(".parquet"):
        import pandas as pd
        df = pd.read_parquet(path)
        return df.to_dict(orient="records")

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            f.seek(0)
            records: List[Dict[str, Any]] = []
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON on line {line_no} of {path}: {e}") from e
                if not isinstance(obj, dict):
                    raise ValueError(f"JSONL line {line_no} is not an object in {path}")
                records.append(obj)
            return records

    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"Unsupported JSON root type in {path}: {type(data)}")

def select_examples(
    *,
    dataset_split: Iterable[Dict[str, Any]],
    split_name: str,
    limit: int,
    ids: Optional[Sequence[str]],
) -> List[Example]:
    # 從 dataset_split 中挑出要評估的樣本。
    # 若有 ids，就精準選取指定資料；若沒有，就依 limit 取前 N 筆。
    selected: List[Example] = []

    if ids is not None:
        wanted = {str(x) for x in ids}
        for instance in dataset_split:
            ex_id = str(instance.get("id"))
            if ex_id not in wanted:
                continue
            selected.append(
                Example(
                    id=ex_id,
                    transcript=as_text(instance.get("transcript") or instance.get("report") or instance.get("text") or ""),
                    reference_summary=as_text(instance.get("summary")),
                    split=split_name,
                )
            )
            if len(selected) >= len(wanted):
                break
        missing = wanted - {ex.id for ex in selected}
        if missing:
            raise RuntimeError(f"Missing ids in split {split_name}: {sorted(missing)[:5]}...")
        return selected

    count = 0
    for instance in dataset_split:
        if count >= limit:
            break
        selected.append(
            Example(
                id=str(instance.get("id", count)),
                transcript=as_text(instance.get("transcript") or instance.get("report") or instance.get("text") or ""),
                reference_summary=as_text(instance.get("summary")),
                split=split_name,
            )
        )
        count += 1

    return selected

def compute_metrics(*, reference: str, prediction: str) -> Dict[str, float]:
    # 計算摘要評估常用的 ROUGE 與 BLEU。
    # ROUGE 看重覆蓋率，BLEU 偏向 n-gram 一致性；兩者搭配可粗略反映摘要品質。
    scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=True)
    rouge = scorer.score(reference, prediction)

    smoothing = SmoothingFunction().method1
    bleu = sentence_bleu([reference.split()], prediction.split(), smoothing_function=smoothing)

    return {
        "rouge1_f": float(rouge["rouge1"].fmeasure),
        "rougeL_f": float(rouge["rougeL"].fmeasure),
        "bleu": float(bleu),
    }

_TEMPLATE_HEADING_RE = re.compile(
    r"^\s*(?:"
    r"會議摘要|摘要|重點摘要|總結|結論|決議|決策|行動項|行動事項|待辦|後續行動|"
    r"Summary|Key\s*Points|Decisions|Action\s*Items"
    r")\s*[:：]?\s*$",
    re.IGNORECASE,
)

_TEMPLATE_HEADING_PREFIX_RE = re.compile(
    r"^\s*(?:會議摘要|摘要|重點摘要|總結|結論|決議|決策|行動項|行動事項|待辦|後續行動|Summary|Key\s*Points|Decisions|Action\s*Items)\s*[:：]\s*",
    re.IGNORECASE,
)

def normalize_for_eval(text: str) -> str:
    """Normalize a summary/reference for metric computation.

    Goal: remove fixed, non-semantic wrappers (e.g., headings) and normalize whitespace.
    This is optional and should be used only when your output is forced into a template
    that the reference does not share.
    """
    # 這個函式的目的是在算指標前，先把模板標題、code fence、JSON 外殼與多餘空白去掉。
    # 這樣可以避免格式差異影響評分，讓指標更聚焦在內容本身。
    if text is None:
        return ""
    text = str(text).strip()
    if not text:
        return ""

    # Remove markdown code fences (common when prompting for JSON).
    text = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", text.strip())
    text = re.sub(r"\s*```\s*$", "", text).strip()

    # If output is (or contains) JSON, extract the most likely summary field.
    json_candidate = text
    if not (json_candidate.startswith("{") and json_candidate.endswith("}")):
        start = json_candidate.find("{")
        end = json_candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_candidate = json_candidate[start : end + 1]
    if json_candidate.startswith("{") and json_candidate.endswith("}"):
        try:
            obj = json.loads(json_candidate)
            if isinstance(obj, dict):
                for key in ("summary", "final_summary", "revised_summary", "output"):
                    if key in obj and isinstance(obj[key], (str, int, float)):
                        text = str(obj[key]).strip()
                        break
        except Exception:
            pass

    lines = [ln.rstrip() for ln in text.splitlines()]
    cleaned_lines: List[str] = []
    for ln in lines:
        if _TEMPLATE_HEADING_RE.match(ln):
            continue
        ln = _TEMPLATE_HEADING_PREFIX_RE.sub("", ln)
        cleaned_lines.append(ln)

    text = "\n".join(cleaned_lines).strip()
    # Normalize whitespace for token-based metrics.
    text = re.sub(r"\s+", " ", text).strip()
    return text

def list_mean(values: List[float]) -> float:
    # 安全地計算平均值；如果列表是空的就回傳 0.0，避免 statistics.mean 拋例外。
    return float(statistics.mean(values)) if values else 0.0
