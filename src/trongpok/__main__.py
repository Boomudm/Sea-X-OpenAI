"""Build option flags from captured JSON without making network requests."""
import argparse
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from .decisions import load_decision
from .errors import ReaderError
from .readers import process_listing_file
from .rules import build_flags


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional(path, default):
    return _read_json(path) if path.is_file() else default


def _write_flags(path, flags):
    # The reviewer UI can read the previous full report while we regenerate it.
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as temp:
        temporary = Path(temp.name)
        try:
            json.dump(flags, temp, ensure_ascii=False, indent=2, allow_nan=False)
            temp.write("\n")
            temp.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("listings", nargs="*", type=Path, help="Listing JSON paths (default: data/listings/*.json)")
    parser.add_argument("--read", action="store_true", help="Run the U2 reader before generating flags")
    parser.add_argument("--reader-output-root", type=Path, default=Path("out"),
                        help="Where to write claims and findings with --read")
    parser.add_argument("--kb", type=Path, default=Path("data/kb/kb.json"))
    parser.add_argument("--claims-dir", type=Path, default=Path("out/claims"))
    parser.add_argument("--findings-dir", type=Path, default=Path("out/findings"))
    parser.add_argument("--challenges-dir", type=Path, help="Optional confidence challenges grouped by option ID")
    parser.add_argument("--output-dir", type=Path, default=Path("out/flags"))
    parser.add_argument("--decisions-db", type=Path, default=Path("out/decisions.sqlite3"))
    args = parser.parse_args()

    listings = args.listings or sorted(Path("data/listings").glob("*.json"))
    if not listings:
        parser.error("No listing JSONs found. Pass a path or add files under data/listings/.")

    kb = _read_optional(args.kb, [])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path in listings:
        listing = _read_json(path)
        listing_id = listing["listing_id"]
        filename = f"{listing_id}.json"
        if Path(filename).name != filename or not listing_id.strip():
            parser.error(f"Invalid listing ID in {path}")
        if args.read:
            try:
                claims_path, findings_path = process_listing_file(
                    path, output_root=args.reader_output_root, preserve_evidence=True,
                )
            except ReaderError as error:
                parser.exit(1, f"{listing_id}: {error}\n")
        else:
            claims_path = args.claims_dir / filename
            findings_path = args.findings_dir / filename
        claims = _read_optional(claims_path, [])
        findings = _read_optional(findings_path, [])
        if isinstance(claims, dict):
            if claims.get("listing_id") != listing_id or not isinstance(claims.get("options"), list):
                parser.error(f"Claims file does not match listing {listing_id}: {claims_path}")
            claims = claims["options"]
        absent = [name for name, values in (("claims", claims), ("findings", findings)) if not values]
        if absent:
            print(f"{listing_id}: no {' or '.join(absent)} supplied; building flags from available evidence")
        challenges = _read_optional(args.challenges_dir / filename, {}) if args.challenges_dir else {}
        flags = build_flags(listing, kb, findings, claims, challenges=challenges)
        for flag in flags:
            decision = load_decision(args.decisions_db, listing_id, flag["option_id"])
            if decision:
                flag["reviewer_decision"] = decision
                flag["verdict"] = "mismatch" if decision["decision"] == "accepted" else "no_mismatch"
        output = args.output_dir / filename
        _write_flags(output, flags)
        print(f"{output}: {len(flags)} option(s)")


if __name__ == "__main__":
    main()
