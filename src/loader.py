import json
from pathlib import Path

ARCHIVE_PATH = Path(__file__).parent.parent / "data" / "archives.json"

def load_archives():
    if not ARCHIVE_PATH.exists():
        raise FileNotFoundError(f"Archive file not found: {ARCHIVE_PATH}")

    with open(ARCHIVE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("entries", [])
