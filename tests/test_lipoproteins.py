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
