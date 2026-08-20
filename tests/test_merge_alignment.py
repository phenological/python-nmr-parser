"""Merging must align sources by path, never by position (issue #4)."""

import numpy as np
import pandas as pd
import pytest

from nmr_parser.core.parse_nmr import _merge_data_sources, _create_params_df


class _Log:
    def __init__(self): self.warnings = []
    def debug(self, *a, **k): pass
    def info(self, *a, **k): pass
    def detail(self, *a, **k): pass
    def step(self, *a, **k): pass
    def warning(self, msg, *a, **k): self.warnings.append(str(msg))


PATHS = ["/data/s1/10", "/data/s2/10", "/data/s3/10"]


def _loe(paths=PATHS):
    return pd.DataFrame({"dataPath": list(paths),
                         "sampleID": [p.split("/")[2] for p in paths]})


def _acqus(paths, marker="acq"):
    return pd.DataFrame({"path": list(paths),
                         "PULPROG": [f"{marker}-{p.split('/')[2]}" for p in paths]})


class TestMergeOrdering:
    def test_acqus_in_a_different_order_is_realigned(self):
        loe = _loe()
        shuffled = [PATHS[2], PATHS[0], PATHS[1]]
        matrix = np.arange(9, dtype=float).reshape(3, 3)

        _, out_loe, out_acqus, _ = _merge_data_sources(
            matrix, loe, _acqus(shuffled), None, _Log())

        assert out_acqus["path"].tolist() == out_loe["dataPath"].tolist()
        # and each row still carries its own value
        for path, pulprog in zip(out_acqus["path"], out_acqus["PULPROG"]):
            assert pulprog.endswith(path.split("/")[2])

    def test_qc_in_a_different_order_is_realigned(self):
        loe = _loe()
        shuffled = [PATHS[1], PATHS[2], PATHS[0]]
        qc = pd.DataFrame({"path": shuffled,
                           "LineWidth": [1.1, 2.2, 3.3]})
        expected = dict(zip(shuffled, [1.1, 2.2, 3.3]))
        matrix = np.zeros((3, 2))

        _, out_loe, _, out_qc = _merge_data_sources(matrix, loe, pd.DataFrame(), qc, _Log())

        assert out_qc["path"].tolist() == out_loe["dataPath"].tolist()
        for path, width in zip(out_qc["path"], out_qc["LineWidth"]):
            assert width == expected[path]

    def test_a_path_missing_from_acqus_drops_the_sample_from_all_sources(self):
        loe = _loe()
        matrix = np.arange(9, dtype=float).reshape(3, 3)

        out_matrix, out_loe, out_acqus, _ = _merge_data_sources(
            matrix, loe, _acqus(PATHS[:2]), None, _Log())

        assert out_loe["dataPath"].tolist() == PATHS[:2]
        assert out_acqus["path"].tolist() == PATHS[:2]
        assert out_matrix.shape[0] == 2
        # the surviving spectra are the right ones
        np.testing.assert_array_equal(out_matrix, matrix[:2, :])

    def test_a_duplicated_path_is_reported_and_reduced(self):
        loe = _loe()
        duplicated = _acqus(PATHS + [PATHS[0]])
        log = _Log()

        _, out_loe, out_acqus, _ = _merge_data_sources(
            np.zeros((3, 2)), loe, duplicated, None, log)

        assert out_acqus["path"].tolist() == out_loe["dataPath"].tolist()
        assert any("more than one row per path" in w for w in log.warnings)


class TestParamsKeyedOnPath:
    def test_parameters_follow_their_own_sample(self):
        keys = ["s1_key", "s2_key", "s3_key"]
        # acqus deliberately in a different order from the keys
        acqus = _acqus([PATHS[2], PATHS[0], PATHS[1]])

        params = _create_params_df(keys, acqus, None, paths=PATHS)
        flat = params.reset_index()

        for _, row in flat.iterrows():
            sample = row["sample_key"].split("_")[0]
            assert row["param_value"].endswith(sample), (
                f"{row['sample_key']} got {row['param_value']}")

    def test_a_stray_path_is_dropped_rather_than_mislabelled(self):
        keys = ["s1_key", "s2_key", "s3_key"]
        acqus = _acqus(PATHS[:2] + ["/data/not_in_loe/10"])

        params = _create_params_df(keys, acqus, None, paths=PATHS)
        flat = params.reset_index()

        assert set(flat["sample_key"]) == {"s1_key", "s2_key"}
