from typing import List, Dict


def field_presence_accuracy(preds: List[Dict], golds: List[Dict], field: str) -> float:
    total = len(golds)
    correct = 0
    for p, g in zip(preds, golds):
        if bool(p.get(field)) == bool(g.get(field)):
            correct += 1
    return correct / total if total else 0.0
