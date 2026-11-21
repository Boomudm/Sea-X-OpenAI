"""Publish the pipeline's local option reports for the Seller Guard browser demo."""

import argparse
import re
from collections.abc import Callable
from functools import cache
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal, NotRequired, TypedDict
from urllib.parse import quote, urlsplit

from pydantic import TypeAdapter, ValidationError

from .errors import ReaderInputError
from .paths import within_directory, write_json
from .reviewer_data import load_listings, resolve_thumbnail
from .rules import queue_key
from .shapes import Adjustment, Flag, Listing, Number, Question

DEFAULT_OUTPUT = Path("web/seller-guard/public/data/cases.json")
RESULTS_SOURCE = Path("eval/results.md")
RESULTS_OUTPUT = DEFAULT_OUTPUT.with_name("results.md")
PRIORITY = {"RED": "red", "YELLOW": "yellow", "GREEN": "green", "GREY": "unknown"}
SIGNAL = {"Q3": "capacity", "Q2": "unsupported", "Q1": "price", "Q4": "reports", "Q5": "clear"}
_FLAGS = TypeAdapter(list[Flag])
ImageLink = Callable[[str], str | None]
_LISTING_PATH = re.compile(r"/(?:product/([0-9]+)/[0-9]+|[^/\\\s]+-i\.([0-9]+)\.[0-9]+)/?")
_SHOPEE_HOSTS = {"shopee.co.th", "www.shopee.co.th"}
_REDACTED_WORDS = re.compile(r"\b(?:fake|fraud)\b", re.IGNORECASE | re.ASCII)

type ShopBadge = Literal["mall", "preferred", "none"]


class _CapturedShop(TypedDict):
    shop_id: str
    name: NotRequired[str | None]
    badge: NotRequired[ShopBadge | None]
    ships_from: NotRequired[str | None]


_SHOPS = TypeAdapter(list[_CapturedShop])


class WebShop(TypedDict):
    id: str | None
    name: str
    url: str | None
    badge: ShopBadge | None
    ships_from: str | None


class WebCapture(TypedDict):
    listing_url: NotRequired[str]
    was_thb: NotRequired[Number | None]
    now_thb: NotRequired[Number]
    photo_count: NotRequired[int]
    listing_images: NotRequired[list[str]]
    buyer_images: NotRequired[list[str]]


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
    shop: WebShop


def _load_shops(data_dir: Path) -> dict[str, _CapturedShop]:
    try:
        path = within_directory("shops.json", data_dir)
        records = _SHOPS.validate_json(path.read_bytes(), strict=True)
    except FileNotFoundError:
        return {}
    except (ValidationError, OSError, RuntimeError) as error:
        raise ReaderInputError("Could not read shop captures from shops.json") from error

    shops = {record["shop_id"]: record for record in records}
    if len(shops) != len(records):
        raise ReaderInputError("Duplicate shop IDs in shops.json")
    return shops


def _shop_id(listing_url: str) -> str | None:
    try:
        url = urlsplit(listing_url)
    except ValueError:
        return None
    if url.scheme not in {"http", "https"} or url.netloc.lower() not in _SHOPEE_HOSTS:
        return None
    match = _LISTING_PATH.fullmatch(url.path)
    return (match[1] or match[2]) if match else None


def _public_shop_text(value: str | None) -> str | None:
    return _REDACTED_WORDS.sub("[redacted]", value) if value and value.strip() else None


def _web_shop(listing: Listing | None, shops: dict[str, _CapturedShop]) -> WebShop:
    shop_id = _shop_id(listing["url"]) if listing is not None else None
    shop = shops.get(shop_id) if shop_id is not None else None
    return {
        "id": shop_id,
        "name": (_public_shop_text(shop.get("name")) if shop is not None else None) or "not captured",
        "url": f"https://shopee.co.th/shop/{shop_id}" if shop_id is not None else None,
        "badge": shop.get("badge") if shop is not None else None,
        "ships_from": _public_shop_text(shop.get("ships_from")) if shop is not None else None,
    }


def _web_case(
    flag: Flag, listing: Listing | None, shops: dict[str, _CapturedShop], image_link: ImageLink | None,
) -> WebCase:
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
            listing_images = set(filter(None, listing["listing_images"]))
            buyer_images: set[str] = set()
            # The pipeline counts reviews only when the variation names one exact option.
            if variation and sum(item["variation_label"] == variation for item in listing["options"]) == 1:
                buyer_images.update(
                    photo for review in listing["reviews"]
                    if review["variation_label"] == variation
                    for photo in review["images"] if photo
                )
            capture["photo_count"] = len(listing_images | buyer_images)
            if image_link is not None:
                links = _image_links(listing_images, image_link)
                if links:
                    capture["listing_images"] = links
                links = _image_links(buyer_images, image_link)
                if links:
                    capture["buyer_images"] = links

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
        "shop": _web_shop(listing, shops),
    }


def _image_links(refs: set[str], image_link: ImageLink) -> list[str]:
    return sorted({link for ref in refs if (link := image_link(ref)) is not None})


def _image_link_resolver(listings_dir: Path, destination_dir: Path) -> ImageLink:
    listings_dir = listings_dir.resolve()
    root = Path.cwd()

    @cache
    def image_link(ref: str) -> str | None:
        try:
            url = urlsplit(ref)
        except ValueError:
            return None
        if url.scheme in {"https", "http"}:
            if url.hostname and not url.hostname.endswith(".invalid") and url.username is None:
                return ref
            return None

        source = resolve_thumbnail(ref, listings_dir, root)
        if source is None:
            return None
        relative = source.relative_to(listings_dir)
        destination = destination_dir / relative
        if destination.resolve() != destination:
            raise ReaderInputError("Evidence image destinations must not use symbolic links")
        destination.parent.mkdir(parents=True, exist_ok=True)
        _publish_bytes(destination, source.read_bytes())
        return f"/data/images/{quote(relative.as_posix())}"

    return image_link


def build_cases(flags_dir: Path, listings_dir: Path, *, image_link: ImageLink | None = None) -> list[WebCase]:
    """Join flags to their option metadata and captured shops in queue order."""
    listings, issues = load_listings(listings_dir)
    if issues:
        raise ReaderInputError(" ".join(issues))
    shops = _load_shops(listings_dir.parent)

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

    return [
        _web_case(flag, listings.get(flag["listing_id"]), shops, image_link)
        for flag in sorted(flags.values(), key=queue_key)
    ]


def _publish_bytes(destination: Path, content: bytes) -> None:
    with NamedTemporaryFile(dir=destination.parent, delete=False) as temp:
        temporary = Path(temp.name)
        try:
            temp.write(content)
            temp.close()
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)


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
    _publish_bytes(destination, content)


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
        default_output = output == Path.cwd() / DEFAULT_OUTPUT
        image_link = _image_link_resolver(args.listings_dir, output.parent / "images") if default_output else None
        cases = build_cases(args.flags_dir, args.listings_dir, image_link=image_link)
        output.parent.mkdir(parents=True, exist_ok=True)
        if not args.no_results and default_output:
            _publish_results()
        write_json(output, cases)
    except (ReaderInputError, OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"{output}: {len(cases)} option(s)")


if __name__ == "__main__":
    main()
