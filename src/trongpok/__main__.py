"""Build option flags from captured JSON and optional live reader output."""
import argparse
import json
from pathlib import Path

from .capture import normalize_marketplace_fields
from .decisions import load_decision
from .errors import ReaderError, ReaderInputError
from .paths import listing_filename, within_directory, write_json
from .profiles import load_profile
from .publication import publish_flag
from .readers import process_listing_file
from .rules import build_flags


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional(path, default):
    return _read_json(path) if path.is_file() else default


def _load_evidence(args, path, listing_id, filename):
    if args.read:
        claims_path, findings_path = process_listing_file(
            path, output_root=args.reader_output_root, preserve_evidence=True,
        )
    else:
        claims_path = args.claims_dir / filename
        findings_path = args.findings_dir / filename

    claims = _read_optional(claims_path, [])
    if isinstance(claims, dict):
        if claims.get("listing_id") != listing_id or not isinstance(claims.get("options"), list):
            raise ReaderInputError(f"Claims file does not match listing {listing_id}: {claims_path}")
        claims = claims["options"]
    return claims, _read_optional(findings_path, [])


def _analyze_listing(args, path, kb, profile):
    listing = normalize_marketplace_fields(_read_json(path), profile)
    listing_id = listing["listing_id"]
    filename = listing_filename(listing_id)
    claims, findings = _load_evidence(args, path, listing_id, filename)
    absent = [name for name, values in (("claims", claims), ("findings", findings)) if not values]
    if absent:
        print(f"{listing_id}: no {' or '.join(absent)} supplied; building flags from available evidence")
    challenges = _read_optional(args.challenges_dir / filename, {}) if args.challenges_dir else {}
    flags = build_flags(listing, kb, findings, claims, challenges=challenges,
                        profile=profile, allow_draft=args.allow_draft)
    for flag in flags:
        decision = load_decision(args.decisions_db, listing_id, flag["option_id"])
        if decision:
            flag["reviewer_decision"] = decision
            flag["verdict"] = "mismatch" if decision["decision"] == "accepted" else "no_mismatch"
    output = args.output_dir / filename
    write_json(output, [publish_flag(flag) for flag in flags])
    print(f"{output}: {len(flags)} option(s)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("listings", nargs="*", type=Path, help="Listing JSON paths (default: data/listings/*.json)")
    parser.add_argument("--profile", default="storage", help="Category profile ID (default: storage)")
    parser.add_argument("--allow-draft", action="store_true", help="Use a profile pending human review")
    parser.add_argument("--read", action="store_true", help="Run the storage reader before generating flags")
    parser.add_argument("--reader-output-root", type=Path, default=Path("out"),
                        help="Where to write claims and findings with --read")
    parser.add_argument("--kb", type=Path, default=Path("data/kb/kb.json"))
    parser.add_argument("--claims-dir", type=Path, default=Path("out/claims"))
    parser.add_argument("--findings-dir", type=Path, default=Path("out/findings"))
    parser.add_argument("--challenges-dir", type=Path, help="Optional confidence challenges grouped by option ID")
    parser.add_argument("--output-dir", type=Path, help="Flag directory (storage default: out/flags)")
    parser.add_argument("--decisions-db", type=Path, default=Path("out/decisions.sqlite3"))
    args = parser.parse_args()
    try:
        profile = load_profile(args.profile, allow_draft=args.allow_draft)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    if profile.category != "storage":
        if args.read:
            parser.error("--read is available for the storage profile. Supply saved findings for this category.")
        if not args.listings or args.output_dir is None:
            parser.error("Supply listing paths and --output-dir when using a non-storage profile.")
    args.output_dir = args.output_dir or Path("out/flags")

    listings = args.listings or sorted(Path("data/listings").glob("*.json"))
    if not listings:
        parser.error("No listing JSONs found. Pass a path or add files under data/listings/.")

    kb = _read_optional(args.kb, [])
    project_root = Path.cwd()
    try:
        args.output_dir = within_directory(args.output_dir, project_root)
        args.decisions_db = within_directory(args.decisions_db, project_root)
        if args.read:
            args.reader_output_root = within_directory(args.reader_output_root, project_root)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for path in listings:
            _analyze_listing(args, path, kb, profile)
    except ReaderError as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
