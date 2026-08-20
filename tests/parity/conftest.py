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
