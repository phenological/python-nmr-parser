"""Tests for lipoprotein functions."""

import pytest
from nmr_parser.xml_parsers import read_lipo
from nmr_parser.processing import extend_lipo, extend_lipo_value


class TestReadLipo:
    """Tests for read_lipo function."""

    def test_read_lipo_xml(self, lipo_xml):
        """Test reading lipoprotein XML."""
        if not lipo_xml.exists():
            pytest.skip("Test data not available")

        lipo = read_lipo(lipo_xml)
        assert lipo is not None
        assert 'data' in lipo
        assert 'version' in lipo
        assert len(lipo['data']) == 112  # 112 measurements
        assert 'id' in lipo['data'].columns
        assert 'value' in lipo['data'].columns

    def test_nonexistent_file(self):
        """Test reading non-existent file."""
        result = read_lipo("nonexistent.xml")
        assert result is None


class TestExtendLipo:
    """Tests for lipoprotein extension functions."""

    def test_extend_lipo_value(self, lipo_xml):
        """Test extending lipoprotein values."""
        if not lipo_xml.exists():
            pytest.skip("Test data not available")

        lipo = read_lipo(lipo_xml)
        extended = extend_lipo_value(lipo)

        # Should have original + calculated + pct + frac
        assert len(extended.columns) > 112
        assert any('_calc' in col for col in extended.columns)
        assert any('_pct' in col for col in extended.columns)
        assert any('_frac' in col for col in extended.columns)

    def test_extend_lipo_full(self, lipo_xml):
        """Test full lipoprotein extension."""
        if not lipo_xml.exists():
            pytest.skip("Test data not available")

        lipo = read_lipo(lipo_xml)
        extended = extend_lipo(lipo)

        assert 'data' in extended
        assert 'version' in extended
        # Should expand from 112 to ~316 rows
        assert len(extended['data']) > 112
        assert 'tag' in extended['data'].columns
        assert 'refMax' in extended['data'].columns
        assert 'refMin' in extended['data'].columns

    def test_calculated_metrics(self, lipo_xml):
        """Test calculated metrics presence."""
        if not lipo_xml.exists():
            pytest.skip("Test data not available")

        lipo = read_lipo(lipo_xml)
        extended = extend_lipo(lipo)

        calc_ids = extended['data'][extended['data']['id'].str.contains('_calc')]
        assert len(calc_ids) > 0

    def test_percentage_metrics(self, lipo_xml):
        """Test percentage metrics presence."""
        if not lipo_xml.exists():
            pytest.skip("Test data not available")

        lipo = read_lipo(lipo_xml)
        extended = extend_lipo(lipo)

        pct_ids = extended['data'][extended['data']['id'].str.contains('_pct')]
        assert len(pct_ids) > 0

    def test_fractional_metrics(self, lipo_xml):
        """Test fractional metrics presence."""
        if not lipo_xml.exists():
            pytest.skip("Test data not available")

        lipo = read_lipo(lipo_xml)
        extended = extend_lipo(lipo)

        frac_ids = extended['data'][extended['data']['id'].str.contains('_frac')]
        assert len(frac_ids) > 0


class TestExtendLipoValidation:
    """Tests for input validation in extend_lipo functions."""

    def test_invalid_type_not_dict(self):
        """Test that non-dict input raises TypeError."""
        import pandas as pd

        with pytest.raises(TypeError, match="lipo must be a dict"):
            extend_lipo_value("not a dict")

        with pytest.raises(TypeError, match="lipo must be a dict"):
            extend_lipo_value(pd.DataFrame())

    def test_missing_data_key(self):
        """Test that missing 'data' key raises ValueError."""
        lipo = {'version': '1.0'}

        with pytest.raises(ValueError, match="lipo dict must contain 'data' key"):
            extend_lipo_value(lipo)

    def test_data_not_dataframe(self):
        """Test that non-DataFrame 'data' raises TypeError."""
        import pandas as pd

        # Series instead of DataFrame
        lipo = {
            'data': pd.Series([1, 2, 3]),
            'version': '1.0'
        }

        with pytest.raises(TypeError, match="lipo\\['data'\\] must be a DataFrame.*read_lipo.*read_experiment"):
            extend_lipo_value(lipo)

    def test_missing_required_columns(self):
        """Test that missing required columns raises ValueError."""
        import pandas as pd

        # DataFrame but missing 'id' and 'value' columns
        lipo = {
            'data': pd.DataFrame({'foo': [1, 2, 3]}),
            'version': '1.0'
        }

        with pytest.raises(ValueError, match="missing required columns.*\\['id', 'value'\\]"):
            extend_lipo_value(lipo)

    def test_wrong_format_from_read_experiment(self):
        """Test that wide-format data (like from read_experiment) raises error."""
        import pandas as pd

        # Simulate wide-format data from read_experiment
        lipo = {
            'data': pd.DataFrame({
                'path': ['/path/to/exp'],
                'value.HDTG': [1.5],
                'value.LDCH': [2.3]
            }),
            'version': '1.0'
        }

        with pytest.raises(ValueError, match="missing required columns.*long-format.*read_lipo"):
            extend_lipo_value(lipo)

    def test_valid_input_structure(self, lipo_xml):
        """Test that valid input from read_lipo passes validation."""
        if not lipo_xml.exists():
            pytest.skip("Test data not available")

        lipo = read_lipo(lipo_xml)

        # Should not raise any validation errors
        extended = extend_lipo_value(lipo)
        assert extended is not None
        assert len(extended.columns) > 0


class TestFracDenominators:
    """Each subfraction must divide by its own parent class (issue #1).

    An inner loop over all prefixes used to rebuild the denominator but not
    the column it wrote to, so only the last prefix survived and every H*
    and V* subfraction was divided by the LDL parent.
    """

    @staticmethod
    def _values(lipo_file):
        lipo = read_lipo(lipo_file)
        raw = dict(zip(lipo["data"]["id"], lipo["data"]["value"]))
        ext = extend_lipo(lipo)
        data = ext["data"] if isinstance(ext, dict) else ext
        return raw, dict(zip(data["id"], data["value"]))

    @pytest.mark.parametrize("col,parent", [
        ("H1PL", "HDPL"), ("H2FC", "HDFC"), ("H4TG", "HDTG"),
        ("V1TG", "VLTG"), ("V3CH", "VLCH"), ("V5PL", "VLPL"),
        ("L1TG", "LDTG"), ("L6CH", "LDCH"),
    ])
    def test_subfraction_divides_by_its_own_parent(self, lipo_xml, col, parent):
        raw, val = self._values(lipo_xml)
        expected = round(raw[col] / raw[parent], 4) * 100
        assert val[f"{col}_frac"] == pytest.approx(expected)

    def test_every_component_frac_uses_its_own_class(self, lipo_xml):
        """All 60 of them, not just the sampled ones."""
        raw, val = self._values(lipo_xml)
        parent = {"H": "HD", "V": "VL", "L": "LD"}
        ranges = {"H": range(1, 5), "V": range(1, 6), "L": range(1, 7)}
        wrong = []
        for letter, rng in ranges.items():
            for i in rng:
                for suffix in ("TG", "CH", "FC", "PL"):
                    col = f"{letter}{i}{suffix}"
                    expected = round(raw[col] / raw[f"{parent[letter]}{suffix}"], 4) * 100
                    if val[f"{col}_frac"] != pytest.approx(expected):
                        wrong.append(col)
        assert wrong == []

    def test_ce_frac_uses_its_own_class(self, lipo_xml):
        raw, val = self._values(lipo_xml)
        parent = {"H": "HD", "V": "VL", "L": "LD"}
        ranges = {"H": range(1, 5), "V": range(1, 6), "L": range(1, 7)}
        for letter, rng in ranges.items():
            for i in rng:
                p = parent[letter]
                expected = round(
                    (raw[f"{letter}{i}CH"] - raw[f"{letter}{i}FC"])
                    / (raw[f"{p}CH"] - raw[f"{p}FC"]), 4) * 100
                assert val[f"{letter}{i}CE_frac"] == pytest.approx(expected), f"{letter}{i}CE"


class TestLipoClosure:
    """Sums that must come to 100% by construction.

    These hold regardless of the data, so they guard the arithmetic rather
    than a golden value.
    """

    @staticmethod
    def _values(lipo_file):
        ext = extend_lipo(read_lipo(lipo_file))
        data = ext["data"] if isinstance(ext, dict) else ext
        return dict(zip(data["id"], data["value"]))

    @pytest.mark.parametrize("particle", ["HD", "VL", "ID", "LD"])
    def test_pct_composition_closes_at_100(self, lipo_xml, particle):
        """TL is defined as TG + CH + PL, so the composition must sum to 100."""
        val = self._values(lipo_xml)
        total = sum(val[f"{particle}{s}_pct"] for s in ("TG", "CH", "PL"))
        assert total == pytest.approx(100, abs=0.05)

    @pytest.mark.parametrize("particle", [f"H{i}" for i in range(1, 5)]
                             + [f"V{i}" for i in range(1, 6)]
                             + [f"L{i}" for i in range(1, 7)])
    def test_pct_closes_for_every_subfraction(self, lipo_xml, particle):
        """Subfractions carry no CH column, so CE + FC stands in for it."""
        val = self._values(lipo_xml)
        total = sum(val[f"{particle}{s}_pct"] for s in ("TG", "CE", "FC", "PL"))
        assert total == pytest.approx(100, abs=0.05)

    def test_frac_closes_where_the_denominator_is_a_calculated_total(self, lipo_xml):
        """HDA1, HDA2, LDAB and TBPN are summed from the subfractions, so
        these fractions are exact by construction."""
        val = self._values(lipo_xml)
        assert sum(val[f"H{i}A1_frac"] for i in range(1, 5)) == pytest.approx(100, abs=0.05)
        assert sum(val[f"H{i}A2_frac"] for i in range(1, 5)) == pytest.approx(100, abs=0.05)
        assert sum(val[f"L{i}AB_frac"] for i in range(1, 7)) == pytest.approx(100, abs=0.05)
        particle_number = (sum(val[f"L{i}PN_frac"] for i in range(1, 7))
                           + val["VLPN_pct"] + val["IDPN_pct"])
        assert particle_number == pytest.approx(100, abs=0.05)
