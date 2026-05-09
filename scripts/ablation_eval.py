#!/usr/bin/env python3
"""Ablation evaluation script: compare strategies and agent mode.

Default compares 4 conditions:
- strategy=map, agent_mode=off
- strategy=nomap, agent_mode=off
- strategy=original, agent_mode=off
- strategy=auto (planner decides), agent_mode=on

You can optionally run a full 3x2 matrix (map/nomap/original) x (agent off/on).

Data sources:
- Hugging Face MeetingBank: `huuuyeah/meetingbank`
- Local records file (JSONL/JSON): objects with at least `transcript` and `summary`

Examples:
  # Use local JSONL and dry-run (no API calls)
  python scripts/ablation_eval.py --records-file scripts/test.json --limit 10 --dry-run

  # Real eval on local JSONL (needs backend running)
  python scripts/ablation_eval.py --records-file scripts/test.json --limit 10 \
    --endpoint http://localhost:8000 --model gpt-5-mini --out results/ablation.jsonl

  # MeetingBank test split with fixed ids
  python scripts/ablation_eval.py --split test --limit 10 \
    --ids-file .cache/meetingbank_test_ids.json --out results/meetingbank_ablation.jsonl

  # Full 3x2 matrix
  python scripts/ablation_eval.py --records-file scripts/test.json --limit 10 --matrix full
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests
from eval_utils import (
    Example,
    load_ids,
    save_ids,
    load_records_file,
    select_examples,
    compute_metrics,
    normalize_for_eval,
    list_mean,
)

try:
    from datasets import load_dataset  # type: ignore
except Exception:  # pragma: no cover
    load_dataset = None  # type: ignore


@dataclass(frozen=True)
class Condition:
    name: str
    agent_mode: str  # off|on
    strategy: str  # map|nomap|original|auto



def _strategy_to_payload(strategy: str) -> Dict[str, Any]:
    """Map frontend strategies to backend request fields.

    - map: use_map=True
    - nomap: use_map=False
    - original: no split; reduce directly on original text
    """
    if strategy == "map":
        return {"use_map": True}
    if strategy == "nomap":
        return {"use_map": False}
    if strategy == "original":
        return {"use_map": False, "chunk_size_1": 0, "chunk_size_2": 0}
    if strategy == "direct":
        return {"use_map": False, "direct_mode": True}
    if strategy == "auto":
        return {}
    raise ValueError(f"Unknown strategy: {strategy}")


def call_summarize(
    *,
    endpoint: str,
    text: str,
    base_payload: Dict[str, Any],
    timeout_s: float,
) -> Tuple[str, float, Dict[str, Any]]:
    url = endpoint.rstrip("/") + "/summarize"
    payload = dict(base_payload)
    payload["text"] = text
    start = time.time()
    resp = requests.post(url, json=payload, timeout=timeout_s)
    latency = time.time() - start

    if not resp.ok:
        detail: str
        try:
            body = resp.json()
            if isinstance(body, dict) and "detail" in body:
                detail = str(body.get("detail"))
            else:
                detail = json.dumps(body, ensure_ascii=False)
        except Exception:
            detail = (resp.text or "").strip()

        raise RuntimeError(f"HTTP {resp.status_code} from {url}: {detail or 'no response body'}")

    data = resp.json()
    return str(data.get("summary", "")), float(data.get("processing_time", latency)), data




def _safe_path_component(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "unknown"
    cleaned: List[str] = []
    for ch in value:
        if ch.isalnum() or ch in {"-", "_", "."}:
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned)[:120]


def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def build_conditions(matrix: str) -> List[Condition]:
    if matrix == "default":
        return [
            Condition(name="map_off", strategy="map", agent_mode="off"),
            Condition(name="nomap_off", strategy="nomap", agent_mode="off"),
            Condition(name="original_off", strategy="original", agent_mode="off"),
            Condition(name="direct_off", strategy="direct", agent_mode="off"),
            Condition(name="auto_on", strategy="auto", agent_mode="on"),
        ]

    if matrix == "full":
        conds: List[Condition] = []
        for strategy in ["map", "nomap", "original", "direct"]:
            for agent_mode in ["off", "on"]:
                conds.append(Condition(name=f"{strategy}_{agent_mode}", strategy=strategy, agent_mode=agent_mode))
        return conds

    raise ValueError("--matrix must be default or full")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ablation eval: strategies x agent mode")

    parser.add_argument("--records-file", type=str, default="", help="Local JSONL/JSON with transcript+summary")
    parser.add_argument("--split", choices=["train", "validation", "test"], default="test")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--ids-file", type=str, default="", help="JSON list of ids; if missing, save first N ids")
    parser.add_argument("--revision", type=str, default="", help="Optional HF dataset revision")

    parser.add_argument("--endpoint", type=str, default="http://localhost:8000")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--dry-run", action="store_true", help="Do not call API; just print planned conditions")

    parser.add_argument("--matrix", choices=["default", "full"], default="default")

    # Backend request knobs
    parser.add_argument("--model", type=str, default="gpt-5.4-mini")
    parser.add_argument("--planner-model", type=str, default="gpt-5.4")
    parser.add_argument("--reviewer-model", type=str, default="gpt-5.4")
    parser.add_argument("--use-map", type=str, default="true", help="Base use_map (agent off + map/nomap/original override it)")
    parser.add_argument("--test-mode", type=str, default="false")

    parser.add_argument("--chunk-size-1", type=int, default=16000)
    parser.add_argument("--chunk-overlap-1", type=int, default=4000)
    parser.add_argument("--chunk-size-2", type=int, default=8000)
    parser.add_argument("--chunk-overlap-2", type=int, default=0)
    parser.add_argument("--token-max", type=int, default=16000)
    parser.add_argument("--reduce-temperature", type=float, default=0.0)

    parser.add_argument(
        "--normalize-template",
        action="store_true",
        help="Normalize prediction/reference before metrics (strip common template headings / whitespace)",
    )

    parser.add_argument("--out", type=str, default="", help="Write per-example per-condition JSONL")
    parser.add_argument(
        "--out-dir",
        type=str,
        default="",
        help="Write tree output: one folder per example with per-condition summaries + aggregate.json",
    )

    args = parser.parse_args()

    if args.limit <= 0:
        raise SystemExit("--limit must be > 0")

    test_mode = str(args.test_mode).lower() in {"1", "true", "yes", "y"}
    base_use_map = str(args.use_map).lower() in {"1", "true", "yes", "y"}

    ids = load_ids(args.ids_file) if args.ids_file else None

    records_file = args.records_file.strip()
    if records_file:
        dataset_split: Iterable[Dict[str, Any]] = load_records_file(records_file)
        split_name = "local"
    else:
        if load_dataset is None:
            raise SystemExit("datasets is required for HF mode. Install datasets or use --records-file.")
        load_kwargs: Dict[str, Any] = {}
        if args.revision:
            load_kwargs["revision"] = args.revision
        meetingbank = load_dataset("huuuyeah/meetingbank", **load_kwargs)
        dataset_split = meetingbank[args.split]
        split_name = args.split

    examples = select_examples(dataset_split=dataset_split, split_name=split_name, limit=args.limit, ids=ids)

    if ids is None and args.ids_file:
        save_ids(args.ids_file, [ex.id for ex in examples])

    conditions = build_conditions(args.matrix)

    if args.dry_run:
        plan = {
            "split": split_name,
            "n": len(examples),
            "ids_file": args.ids_file or None,
            "records_file": records_file or None,
            "conditions": [c.__dict__ for c in conditions],
        }
        print(json.dumps(plan, ensure_ascii=False, indent=2))

        if args.out_dir.strip():
            os.makedirs(args.out_dir, exist_ok=True)
            _write_text(
                os.path.join(args.out_dir, "plan.json"),
                json.dumps(
                    {"created_at": datetime.now(timezone.utc).isoformat(), **plan},
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        return 0

    base_payload: Dict[str, Any] = {
        "model": args.model,
        "use_map": base_use_map,
        "test_mode": test_mode,
        "chunk_size_1": args.chunk_size_1,
        "chunk_overlap_1": args.chunk_overlap_1,
        "chunk_size_2": args.chunk_size_2,
        "chunk_overlap_2": args.chunk_overlap_2,
        "token_max": args.token_max,
        "reduce_temperature": args.reduce_temperature,
        "planner_model": args.planner_model,
        "reviewer_model": args.reviewer_model,
    }

    # condition-level aggregates
    aggregates: Dict[str, Dict[str, Any]] = {
        cond.name: {
            "condition": cond.__dict__,
            "n": 0,
            "ok": 0,
            "rouge1": [],
            "rougeL": [],
            "bleu": [],
            "latency": [],
        }
        for cond in conditions
    }

    out_f = None
    if args.out:
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        out_f = open(args.out, "w", encoding="utf-8")

    tree_root = args.out_dir.strip()
    if tree_root:
        os.makedirs(tree_root, exist_ok=True)
    try:
        for ex_idx, ex in enumerate(examples, start=1):
            example_dir = ""
            if tree_root:
                folder = f"{ex_idx:04d}_{_safe_path_component(ex.id)}"
                example_dir = os.path.join(tree_root, folder)
                os.makedirs(example_dir, exist_ok=True)
            for cond in conditions:
                payload = dict(base_payload)
                payload["agent_mode"] = cond.agent_mode
                payload.update(_strategy_to_payload(cond.strategy))

                row: Dict[str, Any] = {
                    "split": split_name,
                    "id": ex.id,
                    "index": ex_idx,
                    "condition": cond.name,
                    "agent_mode": cond.agent_mode,
                    "strategy": cond.strategy,
                    "transcript_len": len(ex.transcript),
                    "model": args.model,
                    "test_mode": test_mode,
                }

                agg = aggregates[cond.name]
                agg["n"] += 1

                try:
                    txt_path = os.path.join(example_dir, f"{cond.name}.txt") if example_dir else ""
                    if txt_path and os.path.exists(txt_path):
                        with open(txt_path, "r", encoding="utf-8") as f:
                            pred = f.read()
                        processing_time = 0.0
                        resp_data = {}
                        print(f"  [Resume] Skipping API call for {cond.name}, loaded from cache")
                    else:
                        pred, processing_time, resp_data = call_summarize(
                            endpoint=args.endpoint,
                            text=ex.transcript,
                            base_payload=payload,
                            timeout_s=args.timeout,
                        )
                    reference_for_eval = ex.reference_summary
                    prediction_for_eval = pred
                    if args.normalize_template:
                        reference_for_eval = normalize_for_eval(reference_for_eval)
                        prediction_for_eval = normalize_for_eval(prediction_for_eval)
                    metrics = compute_metrics(reference=reference_for_eval, prediction=prediction_for_eval)

                    row.update({"ok": True, "processing_time": processing_time, "metrics": metrics})

                    agg["ok"] += 1
                    agg["rouge1"].append(metrics["rouge1_f"])
                    agg["rougeL"].append(metrics["rougeL_f"])
                    agg["bleu"].append(metrics["bleu"])
                    agg["latency"].append(processing_time)

                    if out_f:
                        row["prediction"] = pred
                        row["reference"] = ex.reference_summary

                    if example_dir:
                        _write_text(os.path.join(example_dir, f"{cond.name}.txt"), pred)
                        
                        trace_data = resp_data.get("trace") or resp_data.get("agent_logs") or resp_data.get("steps") or resp_data.get("logs")
                        if trace_data:
                            _write_text(
                                os.path.join(example_dir, f"{cond.name}_trace.json"),
                                json.dumps(trace_data, ensure_ascii=False, indent=2)
                            )

                except Exception as e:
                    err = str(e)
                    row.update({"ok": False, "error": err})
                    if example_dir:
                        _write_text(os.path.join(example_dir, f"{cond.name}.error.txt"), err)

                if out_f:
                    out_f.write(json.dumps(row, ensure_ascii=False) + "\n")

            print(f"[{ex_idx}/{len(examples)}] done")

    finally:
        if out_f:
            out_f.close()

    created_at = datetime.now(timezone.utc).isoformat()

    aggregate_rows: List[Dict[str, Any]] = []
    for _name, agg in aggregates.items():
        aggregate_rows.append(
            {
                "condition": agg["condition"],
                "n": agg["n"],
                "ok": agg["ok"],
                "rouge1_f_mean": sum(agg["rouge1"]) / agg["n"] if agg["n"] > 0 else 0.0,
                "rougeL_f_mean": sum(agg["rougeL"]) / agg["n"] if agg["n"] > 0 else 0.0,
                "bleu_mean": sum(agg["bleu"]) / agg["n"] if agg["n"] > 0 else 0.0,
                "latency_mean": list_mean(agg["latency"]),
            }
        )

    if tree_root:
        aggregate_payload: Dict[str, Any] = {
            "created_at": created_at,
            "split": split_name,
            "n_examples": len(examples),
            "ids_file": args.ids_file or None,
            "records_file": records_file or None,
            "matrix": args.matrix,
            "endpoint": args.endpoint,
            "model": args.model,
            "planner_model": args.planner_model,
            "reviewer_model": args.reviewer_model,
            "aggregate": aggregate_rows,
        }
        _write_text(
            os.path.join(tree_root, "aggregate.json"),
            json.dumps(aggregate_payload, ensure_ascii=False, indent=2),
        )

    print("\n=== Aggregate (per condition) ===")
    for row in aggregate_rows:
        print(json.dumps(row, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
