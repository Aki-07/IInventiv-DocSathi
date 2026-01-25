import json
from src.data.load_dataset import load_jsonl
from eval.metrics import field_presence_accuracy


def run(path_in: str, path_out: str):
    data = load_jsonl(path_in)
    preds = []
    golds = []
    # For MVP, assume naive baseline: copy golds as preds to show pipeline
    for item in data:
        golds.append(item.get('ground_truth', {}))
        preds.append(item.get('ground_truth', {}))

    acc_complaint = field_presence_accuracy(preds, golds, 'complaints')
    out = {'complaint_presence_accuracy': acc_complaint}
    with open(path_out, 'w') as f:
        json.dump(out, f, indent=2)
    return out


if __name__ == '__main__':
    print(run('src/data/synthetic_notes.jsonl', 'eval/outputs/metrics.json'))
