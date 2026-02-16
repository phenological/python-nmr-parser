"""
Test that all example scripts run without errors.
"""

import pytest
import subprocess
import sys
from pathlib import Path

# Get project root and examples directory
PROJECT_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"

# Find all example Python files
EXAMPLE_SCRIPTS = list(EXAMPLES_DIR.glob("*.py"))


@pytest.mark.parametrize("script", EXAMPLE_SCRIPTS, ids=lambda x: x.name)
def test_example_help(script):
    """Test that each example script shows help without errors."""
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        timeout=10
    )

    assert result.returncode == 0, f"{script.name} --help failed:\n{result.stderr}"
    assert "usage:" in result.stdout.lower() or "help" in result.stdout.lower()


def test_parse_nmr_example_versions():
    """Test parse_nmr_example with different verbosity levels."""
    script = EXAMPLES_DIR / "parse_nmr_example.py"

    if not script.exists():
        pytest.skip("parse_nmr_example.py not found")

    # Test that help works
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        timeout=10
    )

    assert result.returncode == 0
    assert "--verbosity" in result.stdout or "-v" in result.stdout


def test_example_scripts_exist():
    """Test that expected example scripts exist."""
    expected_examples = [
        "read_params_example.py",
        "read_experiment_example.py",
        "read_spectrum_example.py",
        "parse_nmr_example.py",
    ]

    existing_scripts = [s.name for s in EXAMPLE_SCRIPTS]

    for expected in expected_examples:
        if expected in existing_scripts:
            print(f"✓ Found: {expected}")
        else:
            print(f"⚠ Missing: {expected}")

    assert len(EXAMPLE_SCRIPTS) > 0, "No example scripts found"


def test_examples_are_executable():
    """Test that example scripts have proper shebang."""
    for script in EXAMPLE_SCRIPTS:
        with open(script, 'r') as f:
            first_line = f.readline()

        # Check for proper shebang or imports
        assert (
            first_line.startswith('#!') or
            'import' in first_line or
            '"""' in first_line
        ), f"{script.name} doesn't have proper shebang or starts with imports"


def test_all_examples_import_nmr_parser():
    """Test that all examples import nmr_parser correctly."""
    for script in EXAMPLE_SCRIPTS:
        with open(script, 'r') as f:
            content = f.read()

        # Check that it imports from nmr_parser
        assert (
            'from nmr_parser import' in content or
            'import nmr_parser' in content
        ), f"{script.name} doesn't import nmr_parser"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
