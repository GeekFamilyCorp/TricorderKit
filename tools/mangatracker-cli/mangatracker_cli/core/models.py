from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List

@dataclass
class Record:
    category: str
    action: str
    title_jp: str = "N/A"
    title_en: str = "N/A"
    title_fr: str = "N/A"
    source: str = "N/A"
    source_url: str = "N/A"
    reliability: str = "incomplete"
    confidence_label: str = "incomplet"
    notes: str = ""
    data: Dict[str, Any] | None = None
    last_checked: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not d["last_checked"]:
            d["last_checked"] = datetime.now(timezone.utc).isoformat()
        if d["data"] is None:
            d["data"] = {}
        return d
