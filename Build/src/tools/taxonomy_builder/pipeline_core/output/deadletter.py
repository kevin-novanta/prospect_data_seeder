from pathlib import Path
import json

def append_deadletter(record, out_path="./data/deadletter.jsonl"):
    try:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Warning: Failed to write deadletter record: {e}")
