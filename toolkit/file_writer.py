import os
from datetime import datetime

NOTES_DIR = "notes"

def write_file(filename: str, content: str) -> str:
    try:
        os.makedirs(NOTES_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"{timestamp}_{filename}.md"
        path = os.path.join(NOTES_DIR, safe_name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File saved: {path}"
    except Exception as e:
        return f"File write failed: {str(e)}"