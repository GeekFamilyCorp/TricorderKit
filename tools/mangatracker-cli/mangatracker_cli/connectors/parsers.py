from mangatracker_cli.core.models import Record


def placeholder_record(category: str, action: str, source_key: str, source_meta: dict, notes: str, title: str = "N/A") -> Record:
    return Record(
        category=category,
        action=action,
        title_jp=title,
        source=source_key,
        source_url=source_meta.get("url", "N/A"),
        reliability=source_meta.get("reliability", "incomplete"),
        confidence_label="incomplet",
        notes=notes,
        data={"source_meta": source_meta},
    )
