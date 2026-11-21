"""Build option flags from captured JSON without making network requests."""
import argparse
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from .decisions import load_decision
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
        claims = _read_optional(args.claims_dir / filename, [])
        findings = _read_optional(args.findings_dir / filename, [])
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
