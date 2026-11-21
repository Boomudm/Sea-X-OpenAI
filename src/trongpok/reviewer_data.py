"""Load locally generated evidence and the current decisions for the queue."""

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from .decisions import load_decision
from .errors import ReaderInputError
from .paths import within_directory
from .rules import queue_key
from .shapes import Flag, Listing

DECISION_READ_ERROR = "Saved decisions are temporarily unavailable. Reload before reviewing an option."
_FLAG = TypeAdapter(Flag)
_LISTING = TypeAdapter(Listing)
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def _json_reports(
    directory: Path, label: str, issues: list[str]
) -> Iterator[tuple[Path, object]]:
    try:
        files = sorted(path for path in directory.iterdir() if path.suffix == ".json")
    except FileNotFoundError:
        return
    except OSError:
        issues.append(f"Could not open the {label} folder.")
        return

    for path in files:
        try:
            report = within_directory(path.name, directory)
            if not report.is_file():
                raise OSError
            payload = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, ReaderInputError, RuntimeError, ValueError):
            issues.append(f"Could not read {label} file {path.name}.")
            continue
        yield path, payload


def _renderable(flag: Flag) -> bool:
    confidence = flag["confidence"]
    if not (
        flag["listing_id"].strip()
        and flag["option_id"].strip()
        and flag["reasons"]
        and 0 <= confidence["score"] <= 100
        and 0 <= confidence["base"] <= 100
        and confidence["rounds"] >= 0
    ):
        return False
    # The shared Flag shape leaves the heterogeneous evidence items open.
    for item in flag["evidence"]:
        if not isinstance(item.get("source"), str):
            return False
        if "sources" in item and (
            not isinstance(item["sources"], list)
            or not all(isinstance(source, dict) for source in item["sources"])
        ):
            return False
        if "capacities_gb" in item and not isinstance(item["capacities_gb"], list):
            return False
        if item.get("promise_gb") is not None and not isinstance(item["promise_gb"], (int, float)):
            return False
    return True


def load_queue(flags_dir: Path, decisions_db: Path) -> tuple[list[Flag], list[str]]:
    """Load valid flag rows once per option and overlay the SQLite decisions."""
    issues = []
    options = {}
    for path, payload in _json_reports(flags_dir, "flag", issues):
        if not isinstance(payload, list):
            issues.append(f"Flag file {path.name} must contain a list of options.")
            continue
        skipped = 0
        for record in payload:
            try:
                flag = _FLAG.validate_python(record, strict=True)
            except ValidationError:
                skipped += 1
                continue
            if not _renderable(flag):
                skipped += 1
                continue

            # The database wins over the decision snapshot embedded by the analyzer.
            flag["reviewer_decision"] = None
            flag["verdict"] = "unsure"
            key = flag["listing_id"], flag["option_id"]
            previous = options.get(key)
            canonical = path.name == f"{flag['listing_id']}.json"
            if previous is None:
                options[key] = (canonical, flag)
            else:
                previous_canonical, previous_flag = previous
                if flag != previous_flag:
                    issues.append(f"Multiple flag records found in {path.name} for one option.")
                if canonical and not previous_canonical:
                    options[key] = (canonical, flag)
        if skipped:
            issues.append(f"Could not load {skipped} option record(s) in {path.name}.")

    flags = sorted((flag for _, flag in options.values()), key=queue_key)
    try:
        decisions = [
            load_decision(decisions_db, flag["listing_id"], flag["option_id"]) for flag in flags
        ]
    except (OSError, RuntimeError, sqlite3.Error):
        issues.append(DECISION_READ_ERROR)
    else:
        for flag, decision in zip(flags, decisions, strict=True):
            if decision is not None:
                flag["reviewer_decision"] = decision
                flag["verdict"] = "mismatch" if decision["decision"] == "accepted" else "no_mismatch"
    return flags, issues


def load_listings(listings_dir: Path) -> tuple[dict[str, Listing], list[str]]:
    """Load optional captured listing details for display alongside flag rows."""
    issues = []
    listings = {}
    for path, payload in _json_reports(listings_dir, "listing", issues):
        try:
            listing = _LISTING.validate_python(payload, strict=True)
        except ValidationError:
            issues.append(f"Could not load listing details from {path.name}.")
            continue
        listing_id = listing["listing_id"]
        if listing_id not in listings or path.name == f"{listing_id}.json":
            # Retain captured fields beyond the shared shape, such as a displayed shop rating.
            listings[listing_id] = payload
    return listings, issues


def resolve_thumbnail(
    image_ref: str | None, listings_dir: Path, repo_root: Path
) -> Path | None:
    """Return only raster evidence files inside the configured capture directory."""
    if not isinstance(image_ref, str) or not image_ref or "://" in image_ref:
        return None
    reference = Path(image_ref)
    if reference.suffix.lower() not in _IMAGE_EXTENSIONS:
        return None

    capture_prefix = Path("data/listings")
    candidates = [repo_root / reference, listings_dir / reference]
    if reference.is_relative_to(capture_prefix):
        candidates.append(listings_dir / reference.relative_to(capture_prefix))

    for candidate in candidates:
        try:
            image = within_directory(candidate.absolute(), listings_dir)
            if image.suffix.lower() in _IMAGE_EXTENSIONS and image.is_file():
                return image
        except (OSError, ReaderInputError, RuntimeError, ValueError):
            continue
    return None
