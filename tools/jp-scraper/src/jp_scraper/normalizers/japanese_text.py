import re
import unicodedata

def normalize_japanese_text(text: str | None) -> str | None:
    if text is None:
        return None
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def normalize_record(record: dict) -> dict:
    out = dict(record)
    for key in ("title", "summary", "text", "author"):
        if key in out:
            out[key] = normalize_japanese_text(out[key])
    title = out.get("title") or ""
    out["signals"] = {
        "new_series": any(x in title for x in ["新連載", "連載開始", "新作"]),
        "chapter_1": any(x in title for x in ["第1話", "第１話", "1話"]),
        "one_shot": any(x in title for x in ["読切", "読み切り"]),
        "anime_adaptation": any(x in title for x in ["アニメ化", "TVアニメ", "アニメ決定"]),
    }
    return out
