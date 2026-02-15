"""
Tests for parse_nmr function.

Focus on verifying critical research decisions from parseNMR.R are preserved.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from nmr_parser.core.parse_nmr import (
    _classify_sample_types,
    _make_unique,
    _calculate_spcglyc,
    _generate_sample_keys,
)


class TestSampleTypeClassification:
    """Test sample type classification (lines 98-108 in parseNMR.R)."""

    def test_sltr_detection(self):
        """Test SLTR (serum long-term reference) detection."""
        loe = pd.DataFrame({
            'dataPath': ['path1', 'path2', 'path3'],
            'sampleID': ['sltr001', 'SLTR002', 'sample_sltr_03'],
            'sampleType': ['sample', 'sample', 'sample'],
            'experiment': ['exp'] * 3
        })

        result = _classify_sample_types(loe)

        assert result.loc[0, 'sampleType'] == 'sltr'
        assert result.loc[1, 'sampleType'] == 'sltr'
        assert result.loc[2, 'sampleType'] == 'sltr'

    def test_ltr_detection(self):
        """Test LTR (long-term reference) detection."""
        loe = pd.DataFrame({
            'dataPath': ['path1', 'path2'],
            'sampleID': ['ltr001', 'LTR002'],
            'sampleType': ['sample', 'sample'],
            'experiment': ['exp'] * 2
        })

        result = _classify_sample_types(loe)

        assert result.loc[0, 'sampleType'] == 'ltr'
        assert result.loc[1, 'sampleType'] == 'ltr'

    def test_pqc_detection(self):
        """Test PQC (pooled QC) detection."""
        loe = pd.DataFrame({
            'dataPath': ['path1', 'path2'],
            'sampleID': ['pqc001', 'PQC002'],
            'sampleType': ['sample', 'sample'],
            'experiment': ['exp'] * 2
        })

        result = _classify_sample_types(loe)

        assert result.loc[0, 'sampleType'] == 'pqc'
        assert result.loc[1, 'sampleType'] == 'pqc'

    def test_qc_detection(self):
        """Test QC detection."""
        loe = pd.DataFrame({
            'dataPath': ['path1', 'path2'],
            'sampleID': ['qc001', 'QC002'],
            'sampleType': ['sample', 'sample'],
            'experiment': ['exp'] * 2
        })

        result = _classify_sample_types(loe)

        assert result.loc[0, 'sampleType'] == 'qc'
        assert result.loc[1, 'sampleType'] == 'qc'

    def test_priority_order(self):
        """Test that sltr has priority over ltr."""
        loe = pd.DataFrame({
            'dataPath': ['path1', 'path2'],
            'sampleID': ['sltr_ltr', 'ltr_sltr'],
            'sampleType': ['sample', 'sample'],
            'experiment': ['exp'] * 2
        })

        result = _classify_sample_types(loe)

        # Both should be classified as 'sltr' because sltr is checked first
        assert result.loc[0, 'sampleType'] == 'sltr'
        assert result.loc[1, 'sampleType'] == 'sltr'

    def test_regular_samples(self):
        """Test that regular samples stay as 'sample'."""
        loe = pd.DataFrame({
            'dataPath': ['path1', 'path2', 'path3'],
            'sampleID': ['sample001', 'patient_123', 'control_01'],
            'sampleType': ['sample', 'sample', 'sample'],
            'experiment': ['exp'] * 3
        })

        result = _classify_sample_types(loe)

        assert result.loc[0, 'sampleType'] == 'sample'
        assert result.loc[1, 'sampleType'] == 'sample'
        assert result.loc[2, 'sampleType'] == 'sample'


class TestMakeUnique:
    """Test unique name generation."""

    def test_unique_names_unchanged(self):
        """Test that unique names are not modified."""
        names = ['sample1', 'sample2', 'sample3']
        result = _make_unique(names)
        assert result == names

    def test_duplicate_names_numbered(self):
        """Test that duplicates get numbered."""
        names = ['sample1', 'sample1', 'sample2', 'sample1']
        result = _make_unique(names)
        assert result == ['sample1', 'sample1_1', 'sample2', 'sample1_2']

    def test_empty_list(self):
        """Test empty list."""
        names = []
        result = _make_unique(names)
        assert result == []


class TestSpcglycCalculations:
    """Test spcglyc biomarker calculations (lines 280-359 in parseNMR.R)."""

    def create_test_spectrum(self, n_samples=10):
        """Create synthetic test spectrum."""
        # PPM range: -0.1 to 10 ppm, 44079 points
        ppm = np.linspace(-0.1, 10, 44079)

        # Create synthetic spectra
        spectra = np.random.randn(n_samples, len(ppm)) * 0.1

        # Add peaks in specific regions
        for i in range(n_samples):
            # SPC region (3.18-3.32 ppm)
            mask = (ppm >= 3.18) & (ppm <= 3.32)
            spectra[i, mask] += 2.0

            # Glyc region (2.050-2.118 ppm)
            mask = (ppm >= 2.050) & (ppm <= 2.118)
            spectra[i, mask] += 1.5

            # Alb1 region (0.2-0.7 ppm)
            mask = (ppm >= 0.2) & (ppm <= 0.7)
            spectra[i, mask] += 0.8

            # Alb2 region (6.0-10.0 ppm)
            mask = (ppm >= 6.0) & (ppm <= 10.0)
            spectra[i, mask] += 0.5

        return spectra, ppm

    def test_ppm_trimming(self):
        """Test that correct PPM regions are excluded."""
        spectra, ppm = self.create_test_spectrum()

        loe = pd.DataFrame({
            'dataPath': ['path'] * len(spectra)
        })

        data_matrix, var_names, extra = _calculate_spcglyc(spectra, ppm, loe)

        # Check that we get the correct biomarkers
        assert len(var_names) == 11
        assert var_names == [
            'SPC_All', 'SPC3', 'SPC2', 'SPC1',
            'Glyc_All', 'GlycA', 'GlycB',
            'Alb1', 'Alb2',
            'SPC3_2', 'SPC_Glyc'
        ]

    def test_flip_detection(self):
        """Test 180° flip detection and correction."""
        spectra, ppm = self.create_test_spectrum(n_samples=2)

        # Make second spectrum negative in the 3.2-3.3 region
        mask = (ppm >= 3.2) & (ppm <= 3.3)
        spectra[1, mask] = -np.abs(spectra[1, mask])

        # Also make the rest negative
        spectra[1, :] = -np.abs(spectra[1, :])

        loe = pd.DataFrame({
            'dataPath': ['path1', 'path2']
        })

        data_matrix, var_names, extra = _calculate_spcglyc(spectra, ppm, loe)

        # After flip correction, all values should be positive
        assert np.all(data_matrix >= 0), "Some values are negative after flip correction"

    def test_biomarker_ranges(self):
        """Test that biomarkers are calculated from correct PPM ranges."""
        spectra, ppm = self.create_test_spectrum(n_samples=1)

        loe = pd.DataFrame({
            'dataPath': ['path1']
        })

        data_matrix, var_names, extra = _calculate_spcglyc(spectra, ppm, loe)

        # All biomarkers should be positive
        assert np.all(data_matrix > 0), "Some biomarkers are not positive"

        # Ratios should be reasonable (not NaN or Inf)
        spc3_2_idx = var_names.index('SPC3_2')
        spc_glyc_idx = var_names.index('SPC_Glyc')

        assert not np.isnan(data_matrix[0, spc3_2_idx]), "SPC3_2 ratio is NaN"
        assert not np.isnan(data_matrix[0, spc_glyc_idx]), "SPC_Glyc ratio is NaN"
        assert not np.isinf(data_matrix[0, spc3_2_idx]), "SPC3_2 ratio is Inf"
        assert not np.isinf(data_matrix[0, spc_glyc_idx]), "SPC_Glyc ratio is Inf"

    def test_3mm_tube_correction(self):
        """Test that 3mm tube correction is applied."""
        spectra, ppm = self.create_test_spectrum(n_samples=2)

        # Create loe with one 3mm tube
        loe = pd.DataFrame({
            'dataPath': ['path1/5mm', 'path2/3mm']
        })

        data_matrix, var_names, extra = _calculate_spcglyc(spectra, ppm, loe)

        # The second sample (3mm) should have values ~half of first (5mm)
        # (allowing for some variation due to random noise)
        # Just check that 3mm values are smaller
        for i in range(9):  # First 9 biomarkers (not ratios)
            assert data_matrix[1, i] < data_matrix[0, i], \
                f"3mm tube correction not applied for {var_names[i]}"

    def test_extra_regions(self):
        """Test that extra regions (TSP, SPC, Glyc) are saved."""
        spectra, ppm = self.create_test_spectrum()

        loe = pd.DataFrame({
            'dataPath': ['path'] * len(spectra)
        })

        data_matrix, var_names, extra = _calculate_spcglyc(spectra, ppm, loe)

        # Check that extra data is present
        assert 'tsp' in extra
        assert 'spc_region' in extra
        assert 'glyc_region' in extra

        # Check shapes
        assert extra['tsp'].shape[0] == len(spectra)
        assert extra['spc_region'].shape[0] == len(spectra)
        assert extra['glyc_region'].shape[0] == len(spectra)

        # Check that columns are PPM values
        tsp_ppm = [float(col) for col in extra['tsp'].columns]
        assert all(p <= 0.5 for p in tsp_ppm), "TSP region has wrong PPM range"

        spc_ppm = [float(col) for col in extra['spc_region'].columns]
        assert all(3.18 < p < 3.32 for p in spc_ppm), "SPC region has wrong PPM range"

        glyc_ppm = [float(col) for col in extra['glyc_region'].columns]
        assert all(2.050 < p < 2.118 for p in glyc_ppm), "Glyc region has wrong PPM range"


class TestSampleKeys:
    """Test sample key generation."""

    def test_unique_keys(self):
        """Test that sample keys are unique."""
        loe = pd.DataFrame({
            'dataPath': ['path1', 'path2', 'path3'],
            'sampleID': ['sample1', 'sample2', 'sample1']  # Duplicate sampleID
        })

        keys = _generate_sample_keys(loe)

        assert len(keys) == 3
        assert len(set(keys)) == 3, "Sample keys are not unique"

    def test_key_format(self):
        """Test that keys have correct format (sampleID_hash)."""
        loe = pd.DataFrame({
            'dataPath': ['path1'],
            'sampleID': ['sample1']
        })

        keys = _generate_sample_keys(loe)

        assert len(keys) == 1
        assert '_' in keys[0], "Key doesn't have underscore separator"
        parts = keys[0].split('_')
        assert len(parts) >= 2, "Key doesn't have hash part"
        assert len(parts[-1]) == 8, "Hash is not 8 characters"


class TestIntegration:
    """Integration tests for full pipeline (when test data available)."""

    @pytest.mark.skip(reason="Requires test data")
    def test_full_pipeline(self):
        """Test full parseNMR pipeline with real data."""
        # This would test the full pipeline with actual Bruker data
        # Skip for now until test data is available
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
