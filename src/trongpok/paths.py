"""Filesystem boundaries for locally generated listing reports."""
import json
import re
from pathlib import Path
from tempfile import NamedTemporaryFile

from .errors import ReaderInputError


def within_directory(path: str | Path, directory: Path) -> Path:
    """Resolve a path within an operator-selected directory, including symlinks."""
    root = directory.resolve()
    candidate = (root / path).resolve()
    if not candidate.is_relative_to(root):
        raise ReaderInputError(f"Path must stay inside {root}")
    return candidate


def listing_filename(listing_id: str) -> str:
    if not isinstance(listing_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", listing_id):
        raise ReaderInputError("Listing ID must use letters, digits, hyphens, or underscores")
    return f"{listing_id}.json"


def write_json(path: Path, value) -> None:
    """Publish a complete report without following a destination file symlink."""
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as temp:
        temporary = Path(temp.name)
        try:
            json.dump(value, temp, ensure_ascii=False, indent=2, allow_nan=False)
            temp.write("\n")
            temp.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
