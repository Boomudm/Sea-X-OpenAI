import sys
from pathlib import Path

import pytest

from trongpok.__main__ import main
from trongpok.decisions import load_decision, save_decision


@pytest.mark.parametrize("argument", ["--output-dir", "--decisions-db", "--reader-output-root"])
def test_analyze_keeps_generated_files_and_database_in_project(
    tmp_path, monkeypatch, capsys, argument,
):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = project / "external"
    link.symlink_to(outside, target_is_directory=True)
    fixture = Path(__file__).parent / "fixtures" / "listing.json"
    monkeypatch.chdir(project)
    monkeypatch.setattr(sys, "argv", [
        "trongpok-analyze", str(fixture), "--read", argument, str(link / "reports"),
    ])

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 1
    assert "Path must stay inside" in capsys.readouterr().err
    assert list(outside.iterdir()) == []
    assert not (project / "out").exists()


def test_sqlite_decision_read_treats_url_punctuation_as_filename(tmp_path):
    database = tmp_path / "decisions # review%25.sqlite3"
    assert load_decision(database, "listing", "option") is None
    assert not database.exists()
    saved = save_decision(database, "listing", "option", "accepted", "Verified")
    assert load_decision(database, "listing", "option") == saved
