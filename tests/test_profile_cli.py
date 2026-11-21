"""A category profile can be selected for a saved-evidence analysis."""

import json
import sys
from pathlib import Path

import pytest

from trongpok.__main__ import main
from trongpok.decisions import save_decision

SAMPLES = Path(__file__).resolve().parent / "fixtures" / "power_bank"


def test_cli_analyzes_sample_with_selected_profile(tmp_path, monkeypatch):
    listing_id = "sample-power-bank-low"
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "flags" / f"{listing_id}.json"
    decisions_db = tmp_path / "decisions.sqlite3"
    monkeypatch.setattr(sys, "argv", [
        "trongpok-analyze",
        "--profile", "power_bank", "--allow-draft",
        "--findings-dir", str(SAMPLES / "findings"),
        "--output-dir", "flags",
        "--decisions-db", str(decisions_db),
        str(SAMPLES / "listings" / f"{listing_id}.json"),
    ])

    main()

    (flag,) = json.loads(output.read_text(encoding="utf-8"))
    assert (flag["colour"], flag["deciding"], flag["verdict"]) == ("RED", "Q3", "unsure")

    decision = save_decision(decisions_db, listing_id, flag["option_id"], "accepted", "Sample data")
    main()

    (reviewed,) = json.loads(output.read_text(encoding="utf-8"))
    assert (reviewed["colour"], reviewed["deciding"], reviewed["verdict"]) == ("RED", "Q3", "mismatch")
    assert reviewed["confidence"] == flag["confidence"]
    assert reviewed["reviewer_decision"] == decision


def test_cli_rejects_live_read_for_power_bank(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [
        "trongpok-analyze", "--profile", "power_bank", "--allow-draft", "--read",
    ])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 2
    assert "--read is available for the storage profile" in capsys.readouterr().err


def test_cli_requires_explicit_draft_opt_in(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["trongpok-analyze", "--profile", "power_bank"])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 2
    assert "pending human review" in capsys.readouterr().err
