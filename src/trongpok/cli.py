"""Command-line entry point for the narrow U2 path."""

from __future__ import annotations

import argparse
from pathlib import Path

from .errors import ReaderError
from .paths import within_directory
from .readers import process_listing_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read one captured listing into U2 outputs"
    )
    parser.add_argument("listing", help="Path to data/listings/<listing_id>.json")
    parser.add_argument("--output-root", default="out")
    args = parser.parse_args()
    try:
        output_root = within_directory(args.output_root, Path.cwd())
        claims_path, findings_path = process_listing_file(
            args.listing, output_root=output_root, preserve_evidence=True,
        )
    except ReaderError as error:
        parser.exit(1, f"{error}\n")
    print(f"wrote {claims_path}")
    print(f"wrote {findings_path}")


if __name__ == "__main__":
    main()
