def search_by_tag(entries, tag):
    tag = tag.lower()
    return [
        entry for entry in entries
        if tag in (t.lower() for t in entry.get("tags", []))
    ]
