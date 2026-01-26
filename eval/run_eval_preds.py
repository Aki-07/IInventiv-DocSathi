import argparse
import json
import os
import time
from typing import Any, Dict, List

from src.data.load_dataset import load_jsonl
from src.core.pipeline import run_pipeline

# Reuse existing helper if present
try:
    from eval.metrics import field_presence_accuracy
except Exception:
    field_presence_accuracy = None


def model_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert Pydantic v1/v2 models (or dict) to plain dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):  # pydantic v2
        return obj.model_dump()
    if hasattr(obj, "dict"):  # pydantic v1
        return obj.dict()
    return dict(obj)


def get_nested(d: Dict[str, Any], path: str) -> Any:
    cur: Any = d
    for part in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def presence_accuracy(preds: List[Dict], golds: List[Dict], field: str) -> float:
    """Bool(p[field]) matches Bool(g[field]). Field can be nested like 'vitals.bp'."""
    total = len(golds)
    correct = 0
    for p, g in zip(preds, golds):
        pv = get_nested(p, field) if "." in field else p.get(field)
        gv = get_nested(g, field) if "." in field else g.get(field)
        if bool(pv) == bool(gv):
            correct += 1
    return correct / total if total else 0.0


def flags_contain_any(flags: List[str], needles: List[str]) -> bool:
    s = " ".join([(f or "") for f in flags]).lower()
    return any(n.lower() in s for n in needles)


def compute_flag_metrics(preds: List[Dict], golds: List[Dict]) -> Dict[str, float]:
    """
    Poster-friendly flag metrics:
    - Dx-missing flag recall (when gold diagnosis absent)
    - Med-incomplete flag recall (when any gold med misses dose/freq/duration)
    - Med-incomplete false positive rate (flagged even when gold meds complete)
    """
    dx_needed = 0
    dx_hit = 0

    med_needed = 0
    med_hit = 0
    med_fp = 0
    med_complete_cases = 0

    for p, g in zip(preds, golds):
        pflags = p.get("flags") or []
        if not isinstance(pflags, list):
            pflags = [str(pflags)]

        gdx = g.get("diagnosis") or []
        if not gdx:
            dx_needed += 1
            if flags_contain_any(pflags, ["diagnosis not documented", "not inferred"]):
                dx_hit += 1

        gmeds = g.get("medications") or []
        needs_med_flag = False
        if isinstance(gmeds, list) and gmeds:
            for m in gmeds:
                if not isinstance(m, dict):
                    continue
                if m.get("dose") is None or m.get("frequency") is None or m.get("duration") is None:
                    needs_med_flag = True
                    break

        if needs_med_flag:
            med_needed += 1
            if flags_contain_any(pflags, ["dose", "frequency", "duration"]):
                med_hit += 1
        else:
            if isinstance(gmeds, list) and gmeds:
                med_complete_cases += 1
                if flags_contain_any(pflags, ["dose", "frequency", "duration"]):
                    med_fp += 1

    return {
        "dx_missing_flag_recall": (dx_hit / dx_needed) if dx_needed else 0.0,
        "med_incomplete_flag_recall": (med_hit / med_needed) if med_needed else 0.0,
        "med_incomplete_flag_false_positive_rate": (med_fp / med_complete_cases) if med_complete_cases else 0.0,
    }


def safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run evaluation using real pipeline predictions.")
    parser.add_argument("--input", default="src/data/synthetic_notes.jsonl", help="Path to JSONL dataset")
    parser.add_argument("--outdir", default="eval/outputs", help="Directory to write metrics")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of examples (0 = all)")
    parser.add_argument("--strict", action="store_true", help="Enable strict_mode in pipeline options")
    parser.add_argument("--save_preds", action="store_true", help="Write preds vs gold JSONL for inspection")
    args = parser.parse_args()

    data = load_jsonl(args.input)
    if args.limit and args.limit > 0:
        data = data[: args.limit]

    preds: List[Dict[str, Any]] = []
    golds: List[Dict[str, Any]] = []
    per_note_times: List[float] = []
    errors: List[Dict[str, Any]] = []

    for i, item in enumerate(data):
        note_text = (item.get("note_text") or "").strip()
        gold = item.get("ground_truth") or {}
        golds.append(gold)

        t0 = time.time()
        try:
            res = run_pipeline(note_text, options={"strict_mode": bool(args.strict)})
            structured = model_to_dict(res.get("structured"))
            structured["flags"] = res.get("flags") or structured.get("flags") or []
            preds.append(structured)
        except Exception as e:
            preds.append({"flags": [f"PIPELINE_ERROR: {type(e).__name__}"]})
            errors.append({"index": i, "error": f"{type(e).__name__}: {str(e)}"})
        finally:
            per_note_times.append(time.time() - t0)

    metrics: Dict[str, Any] = {
        "n_examples": len(data),
        "n_errors": len(errors),
        "avg_seconds_per_note": sum(per_note_times) / len(per_note_times) if per_note_times else 0.0,
    }

    if field_presence_accuracy:
        metrics["complaint_presence_accuracy"] = field_presence_accuracy(preds, golds, "complaints")
        metrics["diagnosis_presence_accuracy"] = field_presence_accuracy(preds, golds, "diagnosis")
        metrics["medications_presence_accuracy"] = field_presence_accuracy(preds, golds, "medications")
        metrics["tests_presence_accuracy"] = field_presence_accuracy(preds, golds, "tests")
        metrics["follow_up_presence_accuracy"] = field_presence_accuracy(preds, golds, "follow_up")
        metrics["vitals_presence_accuracy"] = field_presence_accuracy(preds, golds, "vitals")
    else:
        metrics["complaint_presence_accuracy"] = presence_accuracy(preds, golds, "complaints")
        metrics["diagnosis_presence_accuracy"] = presence_accuracy(preds, golds, "diagnosis")
        metrics["medications_presence_accuracy"] = presence_accuracy(preds, golds, "medications")
        metrics["tests_presence_accuracy"] = presence_accuracy(preds, golds, "tests")
        metrics["follow_up_presence_accuracy"] = presence_accuracy(preds, golds, "follow_up")
        metrics["vitals_presence_accuracy"] = presence_accuracy(preds, golds, "vitals")

    metrics["bp_presence_accuracy"] = presence_accuracy(preds, golds, "vitals.bp")
    metrics["hr_presence_accuracy"] = presence_accuracy(preds, golds, "vitals.hr")
    metrics["spo2_presence_accuracy"] = presence_accuracy(preds, golds, "vitals.spo2")
    metrics["temp_presence_accuracy"] = presence_accuracy(preds, golds, "vitals.temp")

    metrics.update(compute_flag_metrics(preds, golds))

    safe_mkdir(args.outdir)

    path_json = os.path.join(args.outdir, "metrics_preds.json")
    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    path_csv = os.path.join(args.outdir, "metrics_preds.csv")
    with open(path_csv, "w", encoding="utf-8") as f:
        f.write("metric,value\n")
        for k, v in metrics.items():
            f.write(f"{k},{v}\n")

    if args.save_preds:
        path_preds = os.path.join(args.outdir, "preds_vs_gold.jsonl")
        with open(path_preds, "w", encoding="utf-8") as f:
            for item, p, g in zip(data, preds, golds):
                f.write(json.dumps({"note_text": item.get("note_text"), "pred": p, "gold": g}, ensure_ascii=False) + "\n")

    if errors:
        path_err = os.path.join(args.outdir, "errors.json")
        with open(path_err, "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2, ensure_ascii=False)

    print(f"Wrote: {path_json}")
    print(f"Wrote: {path_csv}")
    if args.save_preds:
        print(f"Wrote: {os.path.join(args.outdir, 'preds_vs_gold.jsonl')}")
    if errors:
        print(f"Wrote: {os.path.join(args.outdir, 'errors.json')}")


if __name__ == "__main__":
    main()
