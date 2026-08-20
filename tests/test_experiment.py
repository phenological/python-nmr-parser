"""Tests for read_experiment function."""

from pathlib import Path

import pytest

from nmr_parser.core.experiment import _select_report
from nmr_parser import read_experiment


class TestReadExperiment:
    """Tests for read_experiment function."""

    def test_read_single_experiment(self, covid_sample_10):
        """Test reading a single experiment."""
        if not covid_sample_10.exists():
            pytest.skip("Test data not available")

        result = read_experiment(covid_sample_10)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_read_multiple_experiments(self, covid_sample_10, covid_sample_11):
        """Test reading multiple experiments."""
        if not covid_sample_10.exists() or not covid_sample_11.exists():
            pytest.skip("Test data not available")

        result = read_experiment([covid_sample_10, covid_sample_11])
        assert isinstance(result, dict)

    def test_read_with_options(self, covid_sample_10):
        """Test reading with specific options."""
        if not covid_sample_10.exists():
            pytest.skip("Test data not available")

        opts = {"what": ["acqus", "procs"]}
        result = read_experiment(covid_sample_10, opts=opts)

        if 'acqus' in result:
            assert len(result['acqus']) > 0
        if 'procs' in result:
            assert len(result['procs']) > 0

    def test_read_spectrum_only(self, covid_sample_10):
        """Test reading spectrum only."""
        if not covid_sample_10.exists():
            pytest.skip("Test data not available")

        opts = {"what": ["spec"]}
        result = read_experiment(covid_sample_10, opts=opts)
        assert 'spec' in result

    def test_nonexistent_folder(self, test_data_dir):
        """Test reading non-existent folder."""
        result = read_experiment(test_data_dir / "nonexistent")
        assert isinstance(result, dict)

    def test_read_with_spec_options(self, covid_sample_10):
        """Test reading with spectrum options."""
        if not covid_sample_10.exists():
            pytest.skip("Test data not available")

        opts = {
            "what": ["spec"],
            "specOpts": {
                "fromTo": (-0.1, 10),
                "length_out": 44079
            }
        }
        result = read_experiment(covid_sample_10, opts=opts)
        assert 'spec' in result


class TestReportSelection:
    """Which report version is read must not depend on directory order (#14).

    Path.glob yields entries in os.scandir order, which is filesystem
    dependent, so taking [0] made the same data read differently on
    different machines.
    """

    @staticmethod
    def _expno_with(tmp_path, source_report, names):
        expno = tmp_path / "10"
        pdata = expno / "pdata" / "1"
        pdata.mkdir(parents=True)
        for name in names:
            (pdata / name).write_bytes(Path(source_report).read_bytes())
        return expno

    def test_the_latest_version_wins_over_the_bare_name(self, test_data_dir, tmp_path):
        source = next(test_data_dir.rglob("lipo_results.xml"))
        expno = self._expno_with(
            tmp_path, source,
            ["plasma_lipo_report.xml", "plasma_lipo_report_2_0_0.xml"])

        chosen = _select_report(expno / "pdata" / "1", "*lipo*.xml", "1_1_0")

        assert chosen.name == "plasma_lipo_report_2_0_0.xml"

    def test_the_preferred_version_still_wins(self, test_data_dir, tmp_path):
        source = next(test_data_dir.rglob("lipo_results.xml"))
        expno = self._expno_with(
            tmp_path, source,
            ["plasma_lipo_report.xml", "plasma_lipo_report_1_1_0.xml",
             "plasma_lipo_report_2_0_0.xml"])

        chosen = _select_report(expno / "pdata" / "1", "*lipo*.xml", "1_1_0")

        assert chosen.name == "plasma_lipo_report_1_1_0.xml"

    def test_the_choice_does_not_depend_on_creation_order(self, test_data_dir, tmp_path):
        """Same set of files, written in the opposite order, same answer."""
        source = next(test_data_dir.rglob("lipo_results.xml"))
        names = ["plasma_lipo_report.xml", "plasma_lipo_report_2_0_0.xml"]

        forward = self._expno_with(tmp_path / "a", source, names)
        backward = self._expno_with(tmp_path / "b", source, list(reversed(names)))

        assert (_select_report(forward / "pdata" / "1", "*lipo*.xml", "1_1_0").name
                == _select_report(backward / "pdata" / "1", "*lipo*.xml", "1_1_0").name)

    def test_no_report_gives_none(self, tmp_path):
        pdata = tmp_path / "10" / "pdata" / "1"
        pdata.mkdir(parents=True)
        assert _select_report(pdata, "*lipo*.xml", "1_1_0") is None
