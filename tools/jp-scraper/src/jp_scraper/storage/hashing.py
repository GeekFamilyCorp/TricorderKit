import hashlib
import json

def stable_hash(obj) -> str:
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]
