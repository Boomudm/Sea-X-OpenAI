"""Publish the pipeline's local option reports for the Seller Guard browser demo."""

import argparse
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import NotRequired, TypedDict

from pydantic import TypeAdapter, ValidationError

from .errors import ReaderInputError
from .paths import within_directory, write_json
from .reviewer_data import load_listings
from .rules import queue_key
from .shapes import Adjustment, Flag, Listing, Number, Question

DEFAULT_OUTPUT = Path("web/seller-guard/public/data/cases.json")
RESULTS_SOURCE = Path("eval/results.md")
RESULTS_OUTPUT = DEFAULT_OUTPUT.with_name("results.md")
PRIORITY = {"RED": "red", "YELLOW": "yellow", "GREEN": "green", "GREY": "unknown"}
SIGNAL = {"Q3": "capacity", "Q2": "unsupported", "Q1": "price", "Q4": "reports", "Q5": "clear"}
_FLAGS = TypeAdapter(list[Flag])


class WebCapture(TypedDict):
    listing_url: NotRequired[str]
    was_thb: NotRequired[Number | None]
    now_thb: NotRequired[Number]
    photo_count: NotRequired[int]


class WebCase(TypedDict):
    listing_id: str
    option_id: str
    title: str | None
    variation_label: str | None
    priority: str
    confidence: int
    base: int
    adjustments: list[Adjustment]
    deciding: Question
    findings: list[str]
    path: list[str]
    reasons: list[str]
    evidence: list[dict]
    missing_evidence: list[str]
    capture: WebCapture


def _web_case(flag: Flag, listing: Listing | None) -> WebCase:
    capture: WebCapture = {}
    title = variation = None
    if listing is not None:
        title = listing["title"] or None
        if listing["url"]:
            capture["listing_url"] = listing["url"]
        option = next(
            (item for item in listing["options"] if item["option_id"] == flag["option_id"]),
            None,
        )
        if option is not None:
            variation = option["variation_label"] or None
            capture["was_thb"] = option["was_thb"]
            capture["now_thb"] = option["now_thb"]
            photos = set(filter(None, listing["listing_images"]))
            # The pipeline counts reviews only when the variation names one exact option.
            if variation and sum(item["variation_label"] == variation for item in listing["options"]) == 1:
                photos.update(
                    photo for review in listing["reviews"]
                    if review["variation_label"] == variation
                    for photo in review["images"] if photo
                )
            capture["photo_count"] = len(photos)

    signal = SIGNAL.get(flag["deciding"])
    score = flag["confidence"]
    return {
        "listing_id": flag["listing_id"],
        "option_id": flag["option_id"],
        "title": title,
        "variation_label": variation,
        "priority": PRIORITY[flag["colour"]],
        "confidence": score["score"],
        "base": score["base"],
        "adjustments": score["adjustments"],
        "deciding": flag["deciding"],
        "findings": [signal] if signal else [],
        "path": flag["path"],
        "reasons": flag["reasons"],
        "evidence": flag["evidence"],
        "missing_evidence": score["missing_evidence"],
        "capture": capture,
    }


def build_cases(flags_dir: Path, listings_dir: Path) -> list[WebCase]:
    """Join existing flags to their option metadata in the pipeline's queue order."""
    listings, issues = load_listings(listings_dir)
    if issues:
        raise ReaderInputError(" ".join(issues))

    flags: dict[tuple[str, str], Flag] = {}
    for path in sorted(flags_dir.glob("*.json")):
        try:
            report = within_directory(path.name, flags_dir)
            records = _FLAGS.validate_json(report.read_bytes(), strict=True)
        except (ValidationError, OSError) as error:
            raise ReaderInputError(f"Could not read flag reports from {path.name}") from error

        for flag in records:
            key = (flag["listing_id"], flag["option_id"])
            if key in flags and flag != flags[key]:
                raise ReaderInputError(f"Conflicting flag reports for {key[0]} / {key[1]}")
            if not 0 <= flag["confidence"]["score"] <= 100:
                raise ReaderInputError(f"Invalid confidence score in {path.name}")
            flags[key] = flag

    return [_web_case(flag, listings.get(flag["listing_id"])) for flag in sorted(flags.values(), key=queue_key)]


def _publish_results() -> None:
    """Publish U5's completed or pending Markdown report as a whole file."""
    root = Path.cwd()
    source = root / RESULTS_SOURCE
    destination = root / RESULTS_OUTPUT
    if source.resolve() != source or destination.resolve() != destination:
        raise ReaderInputError("Evaluation report paths must not use symbolic links")
    try:
        content = source.read_bytes()
    except FileNotFoundError:
        return
    with NamedTemporaryFile(dir=destination.parent, delete=False) as temp:
        temporary = Path(temp.name)
        try:
            temp.write(content)
            temp.close()
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flags-dir", type=Path, default=Path("out/flags"))
    parser.add_argument("--listings-dir", type=Path, default=Path("data/listings"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-results", action="store_true", help="Publish only cases.json.")
    args = parser.parse_args()

    try:
        output = within_directory(args.output, Path.cwd())
        if output.suffix != ".json":
            raise ReaderInputError("The cases output must be a JSON file")
        cases = build_cases(args.flags_dir, args.listings_dir)
        output.parent.mkdir(parents=True, exist_ok=True)
        if not args.no_results and output == Path.cwd() / DEFAULT_OUTPUT:
            _publish_results()
        write_json(output, cases)
    except (ReaderInputError, OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"{output}: {len(cases)} option(s)")


if __name__ == "__main__":
    main()
