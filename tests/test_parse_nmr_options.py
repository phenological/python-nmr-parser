"""Option handling in parse_nmr (issues #6 and #7)."""

import pandas as pd
import pytest

from nmr_parser.core.parse_nmr import SUPPORTED_WHAT, parse_nmr


def _run(folder, **opts):
    return parse_nmr(str(folder), opts={"noWrite": True, "verbosity": "error", **opts})


class TestWhatMustNameOneMeasurement:
    """The output carries a single data matrix, variable list and method, so
    a second value has nowhere to go. The if/elif chain used to read
    whichever came first in the chain and ignore the rest."""

    def test_two_values_are_refused(self, test_data_dir):
        with pytest.raises(ValueError, match="single measurement"):
            _run(test_data_dir / "HB-COVID0001", what=["brxlipo", "spec"])

    def test_the_error_shows_what_was_passed(self, test_data_dir):
        with pytest.raises(ValueError, match=r"brxlipo"):
            _run(test_data_dir / "HB-COVID0001", what=["brxlipo", "spec"])

    def test_an_empty_list_is_refused(self, test_data_dir):
        with pytest.raises(ValueError, match="single measurement"):
            _run(test_data_dir / "HB-COVID0001", what=[])

    def test_an_unsupported_value_is_named(self, test_data_dir):
        """This used to surface as "No data was read", which says nothing
        about the input."""
        with pytest.raises(ValueError, match="unsupported what: 'lipo'"):
            _run(test_data_dir / "HB-COVID0001", what=["lipo"])

    def test_the_message_lists_what_is_supported(self, test_data_dir):
        with pytest.raises(ValueError, match="brxpacs"):
            _run(test_data_dir / "HB-COVID0001", what=["nonsense"])

    @staticmethod
    def _validation_error(folder, what):
        """The validation message, or None if it got past validation.

        Reading may still fail afterwards for want of data or because the
        folder branch wants to prompt; what matters here is only whether the
        call was rejected by the `what` check.
        """
        try:
            _run(folder, what=what)
        except Exception as exc:                      # noqa: BLE001
            message = str(exc)
            if "must name a single" in message or "unsupported what" in message:
                return message
        return None

    @pytest.mark.parametrize("value", SUPPORTED_WHAT)
    def test_every_supported_value_passes_validation(self, test_data_dir, value):
        assert self._validation_error(test_data_dir / "HB-COVID0001", [value]) is None

    def test_a_bare_string_is_accepted(self, test_data_dir):
        """what is documented as "str or list of str"."""
        assert self._validation_error(test_data_dir / "HB-COVID0001", "brxlipo") is None

    def test_validation_happens_before_any_reading(self, tmp_path):
        """A bad `what` is reported even when the folder does not exist, so
        the caller is told what is wrong with the argument rather than about
        a downstream symptom."""
        with pytest.raises(ValueError, match="unsupported what"):
            _run(tmp_path / "no_such_folder", what=["lipo"])


class TestQcIsOptIn:
    """The QC report is parsed per sample and feeds only the is_ivdr flag and
    the QC rows in the parameters table, so it should not be read unless it
    was asked for (issue #7)."""

    @staticmethod
    def _qc_calls(monkeypatch, test_data_dir, **opts):
        """Drive parse_nmr past folder scanning and record whether the QC
        read happened. The folder branch wants to prompt, so the sample list
        is supplied directly instead."""
        # nmr_parser.core re-exports parse_nmr, which shadows the submodule
        # of the same name, so the module has to be fetched explicitly.
        import importlib
        module = importlib.import_module("nmr_parser.core.parse_nmr")

        expno = test_data_dir / "HB-COVID0001" / "10"
        loe = pd.DataFrame({
            "dataPath": [str(expno)],
            "sampleID": ["COV0001"],
            "sampleType": ["sample"],
            "experiment": ["noesygppr1d"],
            "USERA2": ["COV0001"],
        })

        calls = []

        def fake_qc(paths, log):
            calls.append(list(paths))
            return None, False

        monkeypatch.setattr(module, "_process_local_folder", lambda *a, **k: loe.copy())
        monkeypatch.setattr(module, "_read_qc_data", fake_qc)

        try:
            _run(test_data_dir / "HB-COVID0001", what=["brxlipo"], **opts)
        except Exception:                              # noqa: BLE001
            pass                                        # reading may still fail
        return calls

    def test_the_default_does_not_read_qc(self, monkeypatch, test_data_dir):
        assert self._qc_calls(monkeypatch, test_data_dir) == []

    def test_tests_true_reads_qc(self, monkeypatch, test_data_dir):
        assert len(self._qc_calls(monkeypatch, test_data_dir, tests=True)) == 1

    def test_tests_defaults_to_false(self):
        """So the saving applies unless it is asked for."""
        import inspect
        source = inspect.getsource(parse_nmr)
        assert "'tests': False," in source
