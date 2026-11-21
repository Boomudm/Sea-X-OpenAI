"""Analyze saved captures and publish option flags to a durable reviewer queue."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
import time
from collections import defaultdict
from collections.abc import Callable, Iterable
from contextlib import ExitStack
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from functools import cache
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from openai import APIConnectionError
from pydantic import BaseModel, ValidationError

from .cache import ReviewCache
from .capture import normalize_marketplace_fields
from .decisions import load_decision
from .errors import InvalidReaderOutput, ReaderInputError
from .paths import listing_filename, within_directory
from .pipeline_ai import (
    CLAIM_VERSION,
    CONFIDENCE_VERSION,
    REVIEW_VERSION,
    ChallengeAssessment,
    ClaimAssessment,
    PipelineClient,
    PipelineResponsesClient,
    ReviewAssessment,
    ReviewFinding,
    challenge_prompt,
    claim_prompt,
    review_prompt,
)
from .pipeline_state import LostJobLease, PipelineState
from .profiles import CategoryProfile, load_profile, require_profile_approval
from .publication import masked_buyer, publish_flag
from .references import reference_source_for
from .reviews import (
    advertised_amounts,
    categorical_quote_supported,
    plain_quote_supported,
    quoted_number_units,
)
from .rules import build_option_flag, queue_key, rescore_option_flag

PROMPT_VERSIONS = (CLAIM_VERSION, REVIEW_VERSION, CONFIDENCE_VERSION)
DEFAULT_BUDGET_MICROUSD = 500_000
DEFAULT_RETRIES = 2
_MAX_OUTPUT_TOKENS = 768
_MAX_CAPTURE_BYTES = 2_000_000
_ISO_DATE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}"
    r"(?:[T ][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]{1,6})?)?(?:Z|[+-][0-9]{2}:[0-9]{2}))?"
)
_STORAGE_OPTION_FIELDS = ("capacity_text", "promise_gb", "capacity_unclear", "was_thb", "now_thb")
_CATEGORICAL_OPTION_FIELDS = ("measurement_text", "measurement_unclear")
_REVIEW_FIELDS = ("review_id", "variation_label", "buyer_masked", "date", "text")
_MEASUREMENT_MISMATCHES = {"none", "other", "capacity_short", "capacity_no_number"}


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def _hash(value: object) -> str:
    return hashlib.sha256(_json(value).encode()).hexdigest()


@cache
def _schema_size(schema: type[BaseModel]) -> int:
    return len(_json(schema.model_json_schema()).encode())


class _JobReader:
    def __init__(self, pipeline: Pipeline, key: str, owner: str, *, prior_error: bool) -> None:
        self.pipeline = pipeline
        self.key = key
        self.owner = owner
        self.failed = prior_error
        self.blocked = False

    def record_failure(self) -> None:
        if not self.failed:
            self.pipeline.state.record_error(self.key, self.owner)
            self.failed = True

    def request[T: BaseModel](self, schema: type[T], developer: str, payload: object) -> T:
        user_text = _json(payload)
        # UTF-8 bytes bound text tokens conservatively. Reserve schema and
        # protocol overhead as well as the full output allowance on each attempt.
        input_bound = len(developer.encode()) + len(user_text.encode()) + _schema_size(schema) + 1024
        reservation = 2 * input_bound + 10 * _MAX_OUTPUT_TOKENS
        for attempt in range(self.pipeline.max_retries + 1):
            if self.blocked or not self.pipeline.state.reserve(
                self.key, self.owner, reservation, self.pipeline.budget_microusd,
            ):
                self.blocked = True
                self.record_failure()
                raise InvalidReaderOutput("AI job budget is exhausted")
            try:
                output = self.pipeline.client.generate(
                    schema,
                    developer=developer,
                    user_text=user_text,
                    max_output_tokens=_MAX_OUTPUT_TOKENS,
                )
                raw = output.model_dump() if isinstance(output, BaseModel) else output
                return schema.model_validate(raw)
            except Exception as error:  # noqa: BLE001 - isolate failures from the AI client.
                self.record_failure()
                status = getattr(error, "status_code", None)
                self.blocked = status == 429
                retryable = (
                    isinstance(error, (APIConnectionError, TimeoutError, ConnectionError))
                    or status in (408, 409, 500, 502, 503, 504)
                )
                if self.blocked or not retryable or attempt == self.pipeline.max_retries:
                    raise InvalidReaderOutput("AI examination did not complete") from None
                self.pipeline.sleep(2**attempt)
        raise AssertionError("request attempts exhausted")


def _capture_timestamp(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or _ISO_DATE.fullmatch(value) is None:
        raise ReaderInputError("Capture timestamps must use ISO dates or timezone-qualified datetimes")
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.replace(tzinfo=parsed.tzinfo or UTC).astimezone(UTC).isoformat(timespec="microseconds")
    except (ValueError, OverflowError) as error:
        raise ReaderInputError("Capture timestamps must contain valid ISO dates") from error


def _validated_capture(listing: dict, profile: CategoryProfile) -> dict:
    listing_filename(listing.get("listing_id"))
    for group, identifier in (("options", "option_id"), ("reviews", "review_id")):
        records = listing.get(group)
        if not isinstance(records, list):
            raise ReaderInputError(f"Capture must contain a {group} array")
        seen = set()
        for record in records:
            if not isinstance(record, dict):
                raise ReaderInputError(f"Capture {group} entries must be objects")
            value = record.get(identifier)
            if not isinstance(value, str) or not value.strip() or value in seen:
                raise ReaderInputError(f"Capture {group} must have unique {identifier} values")
            if not isinstance(record.get("variation_label"), str):
                raise ReaderInputError(f"Capture {group} entries must contain a variation label")
            seen.add(value)
    storage = profile.category == "storage"
    numeric = profile.measurement_mode == "numeric"
    text_fields = ("title", "spec_text") if storage else (("title",) if numeric else ())
    option_fields = _STORAGE_OPTION_FIELDS if storage else _CATEGORICAL_OPTION_FIELDS
    if numeric and not storage:
        option_fields += ("promise_value",)
    listing_context = {"listing_id": listing["listing_id"]}
    for field in text_fields:
        value = listing.get(field, "")
        if not isinstance(value, str):
            raise ReaderInputError("Captured listing title and specifications must be text")
        listing_context[field] = value
    options = []
    for option in listing["options"]:
        text_field = option_fields[0]
        if option.get(text_field) is not None and not isinstance(option[text_field], str):
            raise ReaderInputError("Captured option measurement labels must be text")
        options.append({
            field: option.get(field) for field in ("option_id", "variation_label", *option_fields)
        })
    reviews = []
    for review in listing["reviews"]:
        if not isinstance(review.get("text"), str):
            raise ReaderInputError("Captured review text must be a string")
        _capture_timestamp(review.get("date"))
        buyer = review.get("buyer_masked")
        if buyer is not None and not isinstance(buyer, str):
            raise ReaderInputError("Captured buyer must be text")
        reviews.append({
            **{field: review.get(field) for field in _REVIEW_FIELDS},
            "buyer_masked": masked_buyer(buyer or ""),
        })
    return {**listing_context, "options": options, "reviews": reviews}


def _positive_decimal(value: object) -> Decimal | None:
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    return number if number.is_finite() and number > 0 else None


def _bangkok_analysis_date() -> str:
    return datetime.now(ZoneInfo("Asia/Bangkok")).date().isoformat()


def _eligible_sources(flag: dict, checked_reviews: list[dict]) -> dict[str, str]:
    sources = {f"review:{item['review_id']}": item["text"] for item in checked_reviews}
    for item in flag["evidence"]:
        if review_id := item.get("review_id"):
            sources[f"review:{review_id}"] = item["quote"]
        for field, namespace in (("url", "url"), ("image_ref", "image")):
            if locator := item.get(field):
                sources[f"{namespace}:{locator}"] = locator
        for source_item in item.get("sources", ()):
            if url := source_item.get("url"):
                sources[f"url:{url}"] = url
    return sources


class Pipeline:
    """Process saved listing objects, files or broker messages with one flag per option."""

    def __init__(
        self,
        state_db: str | Path,
        *,
        client: PipelineClient,
        profile: CategoryProfile | None = None,
        allow_draft: bool = False,
        kb_rows: Iterable[dict] = (),
        decisions_db: str | Path | None = None,
        budget_microusd: int = DEFAULT_BUDGET_MICROUSD,
        max_retries: int = DEFAULT_RETRIES,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if budget_microusd < 0 or not 0 <= max_retries <= 3:
            raise ValueError("Use a non-negative job budget and zero to three retries")
        source_profile = profile or load_profile()
        self.profile = CategoryProfile.model_validate_json(source_profile.model_dump_json())
        require_profile_approval(self.profile, allow_draft=allow_draft)
        self.allow_draft = allow_draft
        self.client = client
        self.state = PipelineState(state_db)
        self.kb_rows = tuple(kb_rows) if self.profile.category == "storage" else ()
        self.decisions_db = decisions_db
        self.budget_microusd = budget_microusd
        self.max_retries = max_retries
        self.sleep = sleep
        self._profile_key = _hash(self.profile.model_dump(mode="json"))
        self._units = {
            token.casefold(): name
            for name, definition in self.profile.units.items()
            for token in (name, *definition.all_aliases)
        }
        self._references = reference_source_for(self.profile.category, self.kb_rows)

    def process_listing(self, listing: dict) -> list[dict]:
        listing_id = self._process_capture(listing, automatic=False)
        return self._with_decisions(self.state.results(self._profile_key, listing_id))

    def _prepare_capture(self, listing: dict) -> tuple[str | None, dict]:
        if not isinstance(listing, dict):
            raise ReaderInputError("A saved capture must be a listing object")
        for group in ("options", "reviews"):
            records = listing.get(group)
            if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
                raise ReaderInputError(f"Capture must contain a {group} object array")
        revision = _capture_timestamp(listing.get("captured_at"))
        checked = _validated_capture(normalize_marketplace_fields(listing, self.profile), self.profile)
        return revision, checked

    def _process_capture(self, listing: dict, *, automatic: bool) -> str:
        revision, prepared = self._prepare_capture(listing)
        return self._process_prepared_capture(prepared, revision, automatic=automatic)

    def _process_prepared_capture(self, listing: dict, revision: str | None, *, automatic: bool) -> str:
        options = listing["options"]
        options_by_variation = defaultdict(list)
        reviews_by_variation = defaultdict(list)
        for option in options:
            options_by_variation[option["variation_label"]].append(option)
        for review in listing["reviews"]:
            reviews_by_variation[review["variation_label"]].append(review)
        listing_id = listing["listing_id"]
        jobs = {}
        for option in options:
            label = option["variation_label"]
            option_id = option["option_id"]
            unambiguous = bool(label) and len(options_by_variation[label]) == 1
            reviews = reviews_by_variation[label] if unambiguous else []
            promise = self._advertised_promise(listing, option)
            option_context = self._option_context(listing, option, promise)
            evidence = _hash((option_context, unambiguous, reviews))
            key = _hash((
                listing_id, option_id, evidence, self.profile.version, self._profile_key, PROMPT_VERSIONS,
            ))
            jobs[option_id] = (key, option, reviews, promise)
        admitted = self.state.admit(
            self._profile_key, listing_id, {option_id: job[0] for option_id, job in jobs.items()},
            revision=revision, from_message=automatic,
        )
        if not admitted:
            return listing_id
        runnable = self.state.runnable_keys(self._profile_key, listing_id)
        pending = [job for job in jobs.values() if job[0] in runnable]
        if not pending:
            return listing_id
        with ReviewCache(self.state.path) as cache:
            for key, option, reviews, promise in pending:
                owner = uuid4().hex
                prior_error = self.state.claim(key, owner)
                if prior_error is not None:
                    try:
                        ai = _JobReader(self, key, owner, prior_error=prior_error)
                        scoped_listing = {
                            **listing, "reviews": reviews, "options": options_by_variation[option["variation_label"]],
                        }
                        flag = self._analyze(scoped_listing, option, reviews, promise, ai, cache)
                        self.state.finish(key, owner, publish_flag(flag))
                    except LostJobLease:
                        continue
        return listing_id

    def process_file(self, path: str | Path, *, root: Path | None = None) -> list[dict]:
        """Replay a capture inside the current workspace or an explicitly selected root."""
        return self.process_listing(_read_capture_file(Path(path), root=root or Path.cwd()))

    def scan_watch_directory(self, directory: Path) -> None:
        """Admit the newest valid captures before any watched jobs can use the model."""
        directory = directory.resolve()
        latest: dict[str, tuple[str | None, list[dict]]] = {}
        for path in sorted(directory.glob("*.json")):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                revision, listing = self._prepare_capture(_read_capture_file(path, root=directory))
            except (ReaderInputError, ValueError, OSError):
                print("A watched capture could not be read", file=sys.stderr)
                continue
            listing_id = listing["listing_id"]
            previous = latest.get(listing_id)
            if previous is None or (revision or "") > (previous[0] or ""):
                latest[listing_id] = revision, [listing]
            elif revision == previous[0]:
                previous[1].append(listing)
        for revision, captures in latest.values():
            for listing in captures:
                try:
                    self._process_prepared_capture(listing, revision, automatic=True)
                except (ReaderInputError, ValueError, OSError):
                    print("A watched capture could not be read", file=sys.stderr)

    def process_message(self, message: dict) -> list[dict]:
        """Consume a queue message carrying a saved capture instead of a file path."""
        if not isinstance(message, dict) or set(message) != {"listing"}:
            raise ReaderInputError("A queue message must contain one listing object")
        listing_id = self._process_capture(message["listing"], automatic=True)
        return self._with_decisions(self.state.results(self._profile_key, listing_id))

    def queue(self) -> list[dict]:
        return self._with_decisions(self.state.results(self._profile_key))

    def _with_decisions(self, flags: list[dict]) -> list[dict]:
        if self.decisions_db is not None:
            for flag in flags:
                decision = load_decision(self.decisions_db, flag["listing_id"], flag["option_id"])
                if decision:
                    flag["reviewer_decision"] = decision
                    flag["verdict"] = "mismatch" if decision["decision"] == "accepted" else "no_mismatch"
        return sorted((publish_flag(flag) for flag in flags), key=queue_key)

    def _advertised_promise(self, listing: dict, option: dict) -> Decimal | None:
        profile = self.profile
        if profile.measurement_mode != "numeric":
            return None
        storage = profile.category == "storage"
        key = "promise_gb" if storage else "promise_value"
        unclear = "capacity_unclear" if storage else "measurement_unclear"
        label = option["variation_label"]
        captured_text = option.get("capacity_text" if storage else "measurement_text") or label
        option_amounts = advertised_amounts(label, profile) | advertised_amounts(captured_text, profile)
        title_amounts = advertised_amounts(listing["title"], profile) if storage else set()
        supplied = option.get(key)
        if (
            option.get(unclear)
            or len(option_amounts) != 1
            or (storage and len(title_amounts) == 1 and option_amounts != title_amounts)
            or (supplied is not None and _positive_decimal(supplied) not in option_amounts)
        ):
            return None
        advertised = next(iter(option_amounts))
        return advertised if advertised > 0 else None

    def _option_context(self, listing: dict, option: dict, promise: Decimal | None) -> tuple:
        profile = self.profile
        storage = profile.category == "storage"
        ai_claim = promise is not None and option.get("promise_gb" if storage else "promise_value") is None
        title_context = listing.get("title") if ai_claim else None
        captured = {key: value for key, value in option.items() if key not in {"was_thb", "now_thb"}}
        references = self._references.resolve(listing, {}, promise)
        market = references.market
        compatible = market and market.currency == profile.currency and profile.price_per_unit in (None, market.unit)
        market_evidence = market.flag_evidence(promise, option) if compatible and promise is not None else None
        spec = references.official or references.mall
        spec_evidence = spec.flag_evidence(promise) if spec and promise is not None and promise not in spec.values else None
        return (
            captured, str(promise) if promise is not None else None, title_context,
            references.matched, references.thin, market_evidence, spec_evidence,
        )

    def _claim(self, listing: dict, option: dict, promise: Decimal | None, ai: _JobReader) -> list[dict]:
        profile = self.profile
        if profile.measurement_mode != "numeric":
            return []
        storage = profile.category == "storage"
        key = "promise_gb" if storage else "promise_value"
        if promise is None:
            unclear = "capacity_unclear" if storage else "measurement_unclear"
            return [{"option_id": option["option_id"], unclear: True, key: None}]
        if option.get(key) is not None:
            return []
        label = option["variation_label"]
        captured_text = option.get("capacity_text" if storage else "measurement_text") or label
        result = ai.request(ClaimAssessment, claim_prompt(profile), {
            "title": listing["title"],
            "variation_label": label,
            "measurement_text": captured_text,
        })
        unit = self._units.get(result.unit.strip().casefold())
        quantity = result.quantity
        if (
            result.status != "ok" or quantity is None or quantity <= 0
            or not math.isfinite(quantity) or unit is None
            or not any(
                unit.casefold() in quoted_number_units(
                    text, result.quote, quantity, profile=profile, for_measurement=False,
                )
                for text in (label, captured_text)
            )
        ):
            raise InvalidReaderOutput("The advertised claim lacks a checkable number or unit")
        factor = profile.units[unit].promise_factor
        base = profile.units[profile.promise_unit].promise_factor
        if factor is None or base is None:
            raise InvalidReaderOutput("The advertised unit has no promise conversion")
        value = Decimal(str(quantity)) * factor / base
        if value != promise:
            raise InvalidReaderOutput("The advertised claim conflicts with the full option label")
        return [{"option_id": option["option_id"], key: str(value)}]

    def _verified_finding(self, observation: ReviewFinding, review: dict, option: dict) -> dict:
        profile = self.profile
        role = re.sub(r"[\s/-]+", "_", observation.role.strip().casefold())
        complaint = observation.complaint
        unit = observation.unit.strip().casefold()
        quote = observation.quote
        quantity = observation.quantity
        if (
            role not in profile.review_roles or complaint not in {*profile.mismatch_types, "none"}
            or not plain_quote_supported(review["text"], quote)
            or (quantity is None and unit != "none")
        ):
            raise InvalidReaderOutput("A finding did not match the category or captured review")
        if complaint not in _MEASUREMENT_MISMATCHES and not categorical_quote_supported(
            review["text"], quote, mismatch_type=complaint, profile=profile,
        ):
            raise InvalidReaderOutput("The quote does not report the selected categorical mismatch")
        if profile.measurement_mode == "categorical":
            quantity, unit = None, "none"
        if quantity is not None:
            canonical_unit = self._units.get(unit)
            written_units = quoted_number_units(
                review["text"], quote, quantity, profile=profile, for_measurement=role in profile.measured_roles,
            )
            supported = canonical_unit is not None and canonical_unit.casefold() in written_units
            fallback = profile.category == "storage" and "" in written_units
            if (
                not math.isfinite(quantity) or quantity < 0
                or not (supported or (fallback and unit == "none"))
            ):
                raise InvalidReaderOutput("The quoted measurement does not support the given number and unit")
            unit = canonical_unit or "none"
        return {
            "review_id": review["review_id"],
            "option_id": option["option_id"],
            "role": role,
            "complaint": complaint,
            "unit": unit,
            "quantity": quantity,
            "quote": quote,
            "read_status": "ok",
        }

    def _read_review(
        self, listing_id: str, review: dict, option: dict, ai: _JobReader, cache: ReviewCache,
    ) -> list[dict]:
        payload = {
            "variation_label": option["variation_label"],
            "measurement_text": option.get("measurement_text", option.get("capacity_text")),
            "review_text": review["text"],
        }
        version = f"{REVIEW_VERSION}:{_hash((self._profile_key, listing_id, option['option_id'], payload))}"
        cached = cache.get(review["review_id"], version)
        if cached is None:
            assessment = ai.request(ReviewAssessment, review_prompt(self.profile), payload)
        else:
            assessment = ReviewAssessment.model_validate(cached)
        if assessment.status != "ok":
            raise InvalidReaderOutput("The review assessment did not check the captured text")

        findings = []
        complete = True
        for observation in assessment.findings:
            try:
                findings.append(self._verified_finding(observation, review, option))
            except InvalidReaderOutput:
                complete = False
                ai.record_failure()
        if not complete:
            return findings
        if cached is None:
            cache.put(review["review_id"], version, assessment.model_dump(mode="json"))
        if not findings:
            # An empty, successful assessment is checked but supplies no evidence.
            findings.append({
                "review_id": review["review_id"],
                "option_id": option["option_id"],
                "role": "other",
                "complaint": "none",
                "unit": "none",
                "quantity": None,
                "quote": "",
                "read_status": "ok",
            })
        return findings

    def _analyze(
        self, listing: dict, option: dict, reviews: list[dict], promise: Decimal | None,
        ai: _JobReader, cache: ReviewCache,
    ) -> dict:
        as_of = _bangkok_analysis_date()
        try:
            claims = self._claim(listing, option, promise, ai)
        except (InvalidReaderOutput, ValidationError):
            ai.record_failure()
            claims = []
        findings = []
        for review in reviews:
            if review["text"].strip():
                try:
                    findings.extend(self._read_review(listing["listing_id"], review, option, ai, cache))
                except (InvalidReaderOutput, ValidationError):
                    ai.record_failure()

        def calculate() -> dict:
            flag = build_option_flag(
                listing, option, self.kb_rows, findings, claims, as_of=as_of,
                profile=self.profile, allow_draft=self.allow_draft, checks_complete=not ai.failed,
            )
            flag["as_of"] = as_of
            for adjustment in flag["confidence"]["adjustments"]:
                if adjustment["reason"] == "Market range and at least 3 offers captured today":
                    adjustment["reason"] = f"Market range and at least 3 offers captured on {as_of}"
            return flag

        flag = calculate()
        rounds = 0
        if not ai.failed and (findings or flag["colour"] in {"RED", "YELLOW"}):
            clean = {finding["review_id"] for finding in findings if finding["complaint"] == "none"}
            checked_reviews = [
                review for review in reviews if flag["colour"] == "GREEN" and review["review_id"] in clean
            ]
            flag, rounds = self._challenge(flag, checked_reviews, ai)
            if ai.failed and flag["colour"] == "GREEN":
                flag = calculate()
        flag["confidence"]["rounds"] = rounds
        flag["check_status"] = "not checked" if ai.failed else "checked"
        return flag

    def _challenge(self, base_flag: dict, checked_reviews: list[dict], ai: _JobReader) -> tuple[dict, int]:
        sources = _eligible_sources(base_flag, checked_reviews)
        if not sources:
            return base_flag, 0
        accepted = []
        used = set()
        flag = base_flag
        for round_number in range(1, 4):
            previous_score = flag["confidence"]["score"]
            try:
                result = ai.request(ChallengeAssessment, challenge_prompt(self.profile), {
                    "flag": flag,
                    "eligible_sources": sources,
                    "round": round_number,
                    "used_sources": sorted(used),
                })
                if any(item.source not in sources or not item.reason.strip() for item in result.challenges):
                    raise InvalidReaderOutput("A confidence proposal lacks valid support")
            except (InvalidReaderOutput, ValidationError):
                ai.record_failure()
                return flag, round_number - 1
            if ai.failed:
                return flag, round_number
            count_before = len(accepted)
            for proposal in result.challenges:
                if proposal.source in used:
                    continue
                challenge = proposal.model_dump(mode="json")
                trial = rescore_option_flag(
                    base_flag, [*accepted, challenge], eligible_sources=sources, profile=self.profile,
                )
                if len(trial["confidence"]["adjustments"]) > len(flag["confidence"]["adjustments"]):
                    used.add(proposal.source)
                    accepted.append(challenge)
                    flag = trial
            if len(accepted) == count_before or abs(flag["confidence"]["score"] - previous_score) < 5:
                return flag, round_number
        return flag, 3


def _read_capture_file(path: Path, *, root: Path) -> object:
    root = root.resolve()
    candidate = within_directory(path, root)
    if path.suffix.lower() != ".json" or candidate.suffix.lower() != ".json":
        raise ReaderInputError("Capture inputs must be JSON files")
    relative = candidate.relative_to(root)
    # Open each validated component beneath the previous directory descriptor.
    # No component can redirect the read if it is swapped for a symlink.
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with ExitStack() as handles:
        directory_fd = os.open(root, directory_flags)
        handles.callback(os.close, directory_fd)
        for part in relative.parts[:-1]:
            directory_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            handles.callback(os.close, directory_fd)
        file_fd = os.open(relative.name, file_flags, dir_fd=directory_fd)
        handles.callback(os.close, file_fd)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            raise ReaderInputError("Capture inputs must be regular files")
        with os.fdopen(file_fd, "rb", closefd=False) as source:
            raw = source.read(_MAX_CAPTURE_BYTES + 1)
    if len(raw) > _MAX_CAPTURE_BYTES:
        raise ReaderInputError("Captured JSON exceeds the 2 MB pipeline limit")
    return json.loads(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    trigger = parser.add_mutually_exclusive_group(required=True)
    trigger.add_argument("--watch", type=Path, help="Scan saved listing JSON files in this directory")
    trigger.add_argument("--message", type=Path, help="Process a JSON queue message carrying a listing")
    trigger.add_argument("--queue", action="store_true", help="Print the durable queue without requesting AI")
    parser.add_argument("--once", action="store_true", help="Scan the watch directory once and exit")
    parser.add_argument("--interval", type=float, default=2.0, help="Watch interval in seconds")
    parser.add_argument("--state-db", type=Path, default=Path("pipeline.sqlite3"))
    parser.add_argument("--decisions-db", type=Path, default=Path("out/decisions.sqlite3"))
    parser.add_argument("--kb", type=Path, default=Path("data/kb/kb.json"))
    parser.add_argument("--profile", default="storage")
    parser.add_argument("--allow-draft", action="store_true")
    parser.add_argument("--budget-microusd", type=int, default=DEFAULT_BUDGET_MICROUSD)
    args = parser.parse_args()
    if (
        not math.isfinite(args.interval) or args.interval <= 0
        or (args.once and args.watch is None)
    ):
        parser.error("Provide an existing watch directory and positive interval; --once requires --watch")

    try:
        workspace = Path.cwd().resolve()
        watch = within_directory(args.watch, workspace) if args.watch is not None else None
        if watch is not None and not watch.is_dir():
            raise ReaderInputError("Select an existing workspace watch directory")
        state_db = within_directory(args.state_db, workspace)
        decisions_db = within_directory(args.decisions_db, workspace)
        message = _read_capture_file(args.message, root=workspace) if args.message is not None else None
        profile = load_profile(args.profile, allow_draft=args.allow_draft)
        kb_rows = ()
        if profile.category == "storage":
            kb_path = within_directory(args.kb, workspace)
            if kb_path.is_file():
                kb_rows = _read_capture_file(kb_path, root=workspace)
        pipeline = Pipeline(
            state_db, client=PipelineResponsesClient(), profile=profile, allow_draft=args.allow_draft,
            kb_rows=kb_rows, decisions_db=decisions_db, budget_microusd=args.budget_microusd,
        )
        if args.queue:
            print(_json(pipeline.queue()))
        elif args.message is not None:
            print(_json(pipeline.process_message(message)))
        else:
            previous = ""
            while True:
                pipeline.scan_watch_directory(watch)
                snapshot = _json(pipeline.queue())
                if snapshot != previous:
                    print(snapshot, flush=True)
                    previous = snapshot
                if args.once:
                    break
                time.sleep(args.interval)
    except (ReaderInputError, ValueError, OSError):
        parser.exit(2, "Pipeline inputs or profile could not be loaded\n")
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
