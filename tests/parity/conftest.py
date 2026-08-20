"""Fixtures for the R/Python parity tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def golden():
    """Values recorded from the R nmr.parser over the same fixtures.

    Regenerate with tests/parity/generate_golden.R when either side moves.
    """
    path = Path(__file__).parent / "golden_r.json"
    if not path.exists():
        pytest.skip("golden_r.json not generated")
    return json.loads(path.read_text())


@pytest.fixture(scope="session", autouse=True)
def golden_is_current(golden):
    """The goldens are a committed artefact, so they can go stale unnoticed.

    This does not re-run R; it only checks the recorded file still describes
    the fixtures the tests are about to read, which is the failure mode that
    would otherwise pass silently.
    """
    data = Path(__file__).parent.parent / "data"
    expected_counts = {
        "read_lipo": 112,
        "extend_lipo": 316,
        "read_pacs": 16,
    }
    for section, count in expected_counts.items():
        assert golden[section]["n"] == count, (
            f"golden_r.json records {golden[section]['n']} rows for {section}, "
            f"expected {count}. Regenerate with tests/parity/generate_golden.R."
        )
    assert (data / "HB-COVID0001" / "10" / "pdata" / "1" / "lipo_results.xml").exists()
