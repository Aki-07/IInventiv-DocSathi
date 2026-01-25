import json
from typing import List, Dict

def load_jsonl(path: str) -> List[Dict]:
    out = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out
