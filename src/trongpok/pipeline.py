"""Analyze saved captures and publish option flags to a durable reviewer queue."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterable
from decimal import Decimal, InvalidOperation
from functools import cache
from pathlib import Path
from uuid import uuid4

from openai import APIConnectionError
from pydantic import BaseModel, ValidationError

from .cache import ReviewCache
from .capture import normalize_marketplace_fields
from .decisions import load_decision
from .errors import InvalidReaderOutput, ReaderInputError
from .paths import listing_filename
from .pipeline_ai import (
    CLAIM_VERSION,
    CONFIDENCE_VERSION,
    REVIEW_VERSION,
    ChallengeAssessment,
    ClaimAssessment,
    PipelineClient,
    PipelineResponsesClient,
    ReviewAssessment,
    challenge_prompt,
    claim_prompt,
    review_prompt,
)
from .pipeline_state import LostJobLease, PipelineState
from .profiles import CategoryProfile, load_profile, require_profile_approval
from .publication import masked_buyer, publish_flag
from .reviews import review_number_units
from .rules import build_flags, queue_key

PROMPT_VERSIONS = (CLAIM_VERSION, REVIEW_VERSION, CONFIDENCE_VERSION)
DEFAULT_BUDGET_MICROUSD = 500_000
DEFAULT_RETRIES = 2
_MAX_OUTPUT_TOKENS = 768
_MAX_CAPTURE_BYTES = 2_000_000


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


def _validated_capture(listing: dict) -> dict:
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
    for review in listing["reviews"]:
        if not isinstance(review.get("text"), str):
            raise ReaderInputError("Captured review text must be a string")
    return {
        **listing,
        "options": [{"now_thb": None, **option} for option in listing["options"]],
        "reviews": [
            {
                **review,
                "buyer_masked": masked_buyer(buyer) if isinstance(buyer := review.get("buyer_masked"), str) else "",
            }
            for review in listing["reviews"]
        ],
    }


def _finite_positive(value: object) -> bool:
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return False
    return number.is_finite() and number > 0


def _exact_quote(quote: str, text: str) -> bool:
    return bool(quote.strip()) and quote in text


def _source_keys(flag: dict, checked_reviews: list[dict]) -> dict[str, str]:
    keys = {item["review_id"]: f"review:{item['review_id']}" for item in checked_reviews}
    quote_owners: dict[str, set[str]] = {}
    for item in flag["evidence"]:
        if review_id := item.get("review_id"):
            key = f"review:{review_id}"
            keys[review_id] = key
            if quote := item.get("quote"):
                quote_owners.setdefault(quote, set()).add(key)
        for name in ("url", "image_ref"):
            if source := item.get(name):
                keys[source] = source
        for source_item in item.get("sources", ()):
            if url := source_item.get("url"):
                keys[url] = url
    for quote, owners in quote_owners.items():
        if len(owners) == 1:
            keys.setdefault(quote, next(iter(owners)))
    return keys


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
        self.kb_rows = tuple(kb_rows)
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
        self._evidence_key = _hash(self.kb_rows)

    def process_listing(self, listing: dict) -> list[dict]:
        if not isinstance(listing, dict):
            raise ReaderInputError("A saved capture must be a listing object")
        for group in ("options", "reviews"):
            records = listing.get(group)
            if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
                raise ReaderInputError(f"Capture must contain a {group} object array")
        listing = _validated_capture(normalize_marketplace_fields(listing, self.profile))
        options = listing["options"]
        variations = Counter(option["variation_label"] for option in options)
        listing_id = listing["listing_id"]
        listing_context = {
            key: value
            for key, value in listing.items()
            if key not in {"options", "reviews"}
        }
        jobs = {}
        for option in options:
            label = option["variation_label"]
            option_id = option["option_id"]
            unambiguous = bool(label) and variations[label] == 1
            reviews = [
                review for review in listing["reviews"]
                if unambiguous and review["variation_label"] == label
            ]
            evidence = _hash((listing_context, option, unambiguous, reviews, self._evidence_key))
            key = _hash((
                listing_id, option_id, evidence, self.profile.version, self._profile_key, PROMPT_VERSIONS,
            ))
            jobs[option_id] = (key, option, reviews)
        self.state.admit(listing_id, {option_id: job[0] for option_id, job in jobs.items()})
        with ReviewCache(self.state.path) as cache:
            for key, option, reviews in jobs.values():
                owner = uuid4().hex
                prior_error = self.state.claim(key, owner)
                if prior_error is not None:
                    try:
                        ai = _JobReader(self, key, owner, prior_error=prior_error)
                        flag = self._analyze(listing, option, reviews, ai, cache)
                        self.state.finish(key, owner, publish_flag(flag))
                    except LostJobLease:
                        continue
        return self._with_decisions(self.state.results(listing_id))

    def process_file(self, path: str | Path) -> list[dict]:
        return self.process_listing(_read_capture_file(Path(path)))

    def process_message(self, message: dict) -> list[dict]:
        """Consume a queue message carrying a saved capture instead of a file path."""
        if not isinstance(message, dict) or set(message) != {"listing"}:
            raise ReaderInputError("A queue message must contain one listing object")
        return self.process_listing(message["listing"])

    def queue(self) -> list[dict]:
        return self._with_decisions(self.state.results())

    def _with_decisions(self, flags: list[dict]) -> list[dict]:
        if self.decisions_db is not None:
            for flag in flags:
                decision = load_decision(self.decisions_db, flag["listing_id"], flag["option_id"])
                if decision:
                    flag["reviewer_decision"] = decision
                    flag["verdict"] = "mismatch" if decision["decision"] == "accepted" else "no_mismatch"
        return sorted((publish_flag(flag) for flag in flags), key=queue_key)

    def _claim(self, listing: dict, option: dict, ai: _JobReader) -> list[dict]:
        profile = self.profile
        storage = profile.category == "storage"
        key = "promise_gb" if storage else "promise_value"
        if profile.measurement_mode != "numeric" or _finite_positive(option.get(key)):
            return []
        label = option["variation_label"]
        captured_text = option.get("capacity_text" if storage else "measurement_text") or label
        result = ai.request(ClaimAssessment, claim_prompt(profile), {
            "title": listing.get("title", ""),
            "variation_label": label,
            "measurement_text": captured_text,
        })
        unit = self._units.get(result.unit.casefold())
        if (
            result.status != "ok" or result.quantity is None or result.quantity <= 0
            or not math.isfinite(result.quantity) or unit is None
            or not (_exact_quote(result.quote, label) or _exact_quote(result.quote, captured_text))
            or unit.casefold() not in review_number_units(result.quote, result.quantity, profile=profile)
        ):
            raise InvalidReaderOutput("The advertised claim lacks a checkable number or unit")
        factor = profile.units[unit].promise_factor
        base = profile.units[profile.promise_unit].promise_factor
        if factor is None or base is None:
            raise InvalidReaderOutput("The advertised unit has no promise conversion")
        value = Decimal(str(result.quantity)) * factor / base
        return [{"option_id": option["option_id"], key: str(value)}]

    def _read_review(
        self, listing_id: str, review: dict, option: dict, ai: _JobReader, cache: ReviewCache,
    ) -> list[dict]:
        profile = self.profile
        payload = {
            "variation_label": option["variation_label"],
            "measurement_text": option.get("measurement_text", option.get("capacity_text")),
            "review_text": review["text"],
        }
        version = f"{REVIEW_VERSION}:{_hash((self._profile_key, listing_id, option['option_id'], payload))}"
        cached = cache.get(review["review_id"], version)
        if cached is None:
            assessment = ai.request(ReviewAssessment, review_prompt(profile), payload)
        else:
            assessment = ReviewAssessment.model_validate(cached)
        if assessment.status != "ok":
            raise InvalidReaderOutput("The review assessment did not check the captured text")

        findings = []
        for observation in assessment.findings:
            role = re.sub(r"[\s/-]+", "_", observation.role.strip().casefold())
            complaint = observation.complaint
            unit = observation.unit.strip().casefold()
            quote = observation.quote
            quantity = observation.quantity
            if (
                role not in profile.review_roles or complaint not in {*profile.mismatch_types, "none"}
                or not _exact_quote(quote, review["text"])
                or (quantity is None and unit != "none")
            ):
                raise InvalidReaderOutput("A finding did not match the category or captured review")
            if quantity is not None:
                canonical_unit = self._units.get(unit)
                written_units = review_number_units(quote, quantity, profile=profile)
                supported = canonical_unit is not None and canonical_unit.casefold() in written_units
                fallback = profile.category == "storage" and "" in written_units
                if (
                    not math.isfinite(quantity) or quantity < 0
                    or not (supported or (fallback and unit == "none"))
                ):
                    raise InvalidReaderOutput("The quoted measurement does not support the given number and unit")
                unit = canonical_unit or "none"
            findings.append({
                "review_id": review["review_id"],
                "option_id": option["option_id"],
                "role": role,
                "complaint": complaint,
                "unit": unit,
                "quantity": quantity,
                "quote": quote,
                "read_status": "ok",
            })
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
        self, listing: dict, option: dict, reviews: list[dict], ai: _JobReader, cache: ReviewCache,
    ) -> dict:
        try:
            claims = self._claim(listing, option, ai)
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
        option_id = option["option_id"]

        def calculate(challenges: list[dict]) -> dict:
            flags = build_flags(
                listing, self.kb_rows, findings, claims,
                profile=self.profile, allow_draft=self.allow_draft, checks_complete=not ai.failed,
                challenges={option_id: challenges},
            )
            return next(flag for flag in flags if flag["option_id"] == option_id)

        accepted = []
        flag = calculate(accepted)
        rounds = 0
        if not ai.failed and (findings or flag["colour"] in {"RED", "YELLOW"}):
            clean = {finding["review_id"] for finding in findings if finding["complaint"] == "none"}
            checked_reviews = [
                {"review_id": review["review_id"], "text": review["text"]}
                for review in reviews if flag["colour"] == "GREEN" and review["review_id"] in clean
            ]
            flag, rounds = self._challenge(flag, checked_reviews, ai, calculate, accepted)
        flag["confidence"]["rounds"] = rounds
        flag["check_status"] = "not checked" if ai.failed else "checked"
        return flag

    def _challenge(
        self,
        flag: dict,
        checked_reviews: list[dict],
        ai: _JobReader,
        calculate: Callable[[list[dict]], dict],
        accepted: list[dict],
    ) -> tuple[dict, int]:
        sources = _source_keys(flag, checked_reviews)
        if not sources:
            return flag, 0
        used = set()
        for round_number in range(1, 4):
            previous_score = flag["confidence"]["score"]
            try:
                result = ai.request(ChallengeAssessment, challenge_prompt(self.profile), {
                    "flag": flag,
                    "checked_reviews": checked_reviews,
                    "eligible_sources": list(sources),
                    "round": round_number,
                    "used_sources": [item["source"] for item in accepted],
                })
                if any(item.source not in sources for item in result.challenges):
                    raise InvalidReaderOutput("A confidence proposal cited unknown evidence")
            except (InvalidReaderOutput, ValidationError):
                ai.record_failure()
                return calculate(accepted), round_number - 1
            if ai.failed:
                return calculate(accepted), round_number
            count_before = len(accepted)
            for proposal in result.challenges:
                source = sources[proposal.source]
                if source in used:
                    continue
                challenge = proposal.model_dump(mode="json")
                trial = calculate([*accepted, challenge])
                if len(trial["confidence"]["adjustments"]) > len(flag["confidence"]["adjustments"]):
                    used.add(source)
                    accepted.append(challenge)
                    flag = trial
            if len(accepted) == count_before or abs(flag["confidence"]["score"] - previous_score) < 5:
                return flag, round_number
        return flag, 3


def _read_capture_file(path: Path) -> dict:
    with path.open("rb") as source:
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
        or (args.watch is not None and not args.watch.is_dir())
        or (args.once and args.watch is None)
    ):
        parser.error("Provide an existing watch directory and positive interval; --once requires --watch")

    try:
        profile = load_profile(args.profile, allow_draft=args.allow_draft)
        kb_rows = _read_capture_file(args.kb) if profile.category == "storage" and args.kb.is_file() else ()
        pipeline = Pipeline(
            args.state_db, client=PipelineResponsesClient(), profile=profile, allow_draft=args.allow_draft,
            kb_rows=kb_rows, decisions_db=args.decisions_db, budget_microusd=args.budget_microusd,
        )
        if args.queue:
            print(_json(pipeline.queue()))
        elif args.message is not None:
            print(_json(pipeline.process_message(_read_capture_file(args.message))))
        else:
            previous = ""
            while True:
                for path in sorted(args.watch.glob("*.json")):
                    if path.is_symlink() or not path.is_file():
                        continue
                    try:
                        pipeline.process_file(path)
                    except (ReaderInputError, ValueError, OSError):
                        print("A watched capture could not be read", file=sys.stderr)
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
