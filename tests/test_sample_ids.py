"""Sample ids must be recorded as the instrument wrote them (issue #5)."""

import pandas as pd
import pytest

from nmr_parser.core.parse_nmr import _classify_sample_types


class _Log:
    def debug(self, *a, **k): pass
    def info(self, *a, **k): pass


def _classify(sample_ids):
    loe = pd.DataFrame({"sampleID": list(sample_ids), "sampleType": "sample"})
    return _classify_sample_types(loe, _Log())["sampleType"].tolist()


class TestClassificationIsCaseInsensitive:
    """The reason the ids were being rewritten was to help this. It does not
    need the help, which is what makes removing the rewrite safe."""

    @pytest.mark.parametrize("sample_id,expected", [
        ("SLTR_01", "sltr"), ("sltr_01", "sltr"), ("SlTr_01", "sltr"),
        ("LTR_01", "ltr"), ("ltr_01", "ltr"),
        ("PQC_01", "pqc"), ("pqc_01", "pqc"),
        ("QC_01", "qc"), ("qc_01", "qc"),
        ("COV0001", "sample"), ("cov0001", "sample"),
    ])
    def test_upper_and_lower_classify_the_same(self, sample_id, expected):
        assert _classify([sample_id]) == [expected]

    def test_sltr_wins_over_ltr(self):
        """SLTR contains LTR, so the order of the checks matters."""
        assert _classify(["SLTR_01"]) == ["sltr"]

    def test_a_mixed_run(self):
        assert _classify(["SLTR_01", "LTR_02", "PQC_03", "QC_04", "COV0005"]) == [
            "sltr", "ltr", "pqc", "qc", "sample"]
