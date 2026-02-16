"""Main orchestrator function for reading complete NMR experiments."""

from pathlib import Path
from typing import Union, List, Optional, Dict, Any, Literal
import pandas as pd
from rich.console import Console

from .parameters import read_param, read_params
from .spectrum import read_spectrum
from ..xml_parsers import (
    read_qc, read_title, read_eretic, read_eretic_f80,
    read_lipo, read_pacs, read_quant
)

console = Console()


def merge_options(defaults: dict, provided: Optional[dict]) -> dict:
    """
    Deep merge provided options with defaults.

    Parameters
    ----------
    defaults : dict
        Default options dictionary
    provided : dict or None
        User-provided options to merge

    Returns
    -------
    dict
        Merged options dictionary
    """
    if provided is None:
        return defaults.copy()

    result = defaults.copy()

    for key, value in provided.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursive merge for nested dicts
            result[key] = merge_options(result[key], value)
        else:
            result[key] = value

    return result


def read_experiment(expname: Union[str, Path, List[Union[str, Path]]],
                   opts: Optional[Dict[str, Any]] = None) -> Dict[str, pd.DataFrame]:
    """
    Read experiment from Bruker folder(s) (expno).

    Main orchestrator function that coordinates reading all data types from
    NMR experiment folders. Supports reading multiple experiments at once.

    Parameters
    ----------
    expname : str, Path, or list
        Path or list of paths to experiment folder(s)
    opts : dict, optional
        Processing options with keys:

        - what : list of str
            Components to read. Options: "acqus", "procs", "qc", "title",
            "eretic", "spec", "lipo", "quant", "pacs", "all", "specOnly"
        - procno : int, default=1
            Processing number to read
        - specOpts : dict
            Options for spectrum reading (uncalibrate, fromTo, length_out, eretic)

    Returns
    -------
    dict
        Dictionary with keys corresponding to requested data types,
        each containing a pandas DataFrame:

        - acqus: Acquisition parameters
        - procs: Processing parameters
        - qc: Quality control data
        - title: Experiment titles
        - eretic: ERETIC factors
        - spec: Spectrum data
        - lipo: Lipoprotein profiles
        - quant: Quantification data
        - pacs: PACS data

    Examples
    --------
    >>> # Read all data from single experiment
    >>> exp = read_experiment("data/experiment/10")
    >>> exp['acqus'].head()

    >>> # Read multiple experiments
    >>> exps = read_experiment(["exp/10", "exp/11", "exp/12"])

    >>> # Read only specific components
    >>> exp = read_experiment("exp/10", opts={"what": ["acqus", "spec"]})

    >>> # Read spectrum with options
    >>> opts = {
    ...     "what": ["spec"],
    ...     "specOpts": {
    ...         "fromTo": (-0.1, 10),
    ...         "length_out": 44079
    ...     }
    ... }
    >>> exp = read_experiment("exp/10", opts=opts)
    """
    # Default options
    default_options = {
        'what': ["acqus", "procs", "qc", "title", "eretic", "spec",
                 "lipo", "quant", "pacs", "all", "specOnly"],
        'procno': 1,
        'specOpts': {
            'uncalibrate': False,
            'fromTo': (-0.1, 10),
            'length_out': 44079
        }
    }

    # Merge options
    opts = merge_options(default_options, opts)
    what = opts['what']

    # Convert single path to list
    if isinstance(expname, (str, Path)):
        expname = [expname]

    expname = [Path(p) for p in expname]

    res = {}

    # Read acqus
    if "acqus" in what or "all" in what:
        lst = []
        for i, exp_path in enumerate(expname):
            # Removed verbose per-experiment progress print
            # console.print(f"Reading: {i+1} / {len(expname)}", end="\r")

            path = exp_path / "acqus"
            if path.exists():
                parms = read_params(path)

                if parms is not None:
                    parms['path'] = str(exp_path)
                    # Reshape from long to wide
                    parms_wide = parms.pivot(index='path', columns='name', values='value')
                    parms_wide.columns = [f'acqus.{col}' for col in parms_wide.columns]
                    parms_wide = parms_wide.reset_index()
                    lst.append(parms_wide)

        if lst:
            # Find common columns
            common_cols = set(lst[0].columns)
            for df in lst[1:]:
                common_cols &= set(df.columns)
            common_cols = sorted(common_cols)

            # Concatenate with common columns
            res['acqus'] = pd.concat([df[common_cols] for df in lst], ignore_index=True)
        else:
            res['acqus'] = pd.DataFrame()

        if len(res['acqus']) == 0:
            console.print("[yellow]readExperiment >> 0 found acqus params[/yellow]")
        else:
            console.print(f"[blue]readExperiment >> {len(res['acqus'])} found acqus params[/blue]")

    # Read procs
    if "procs" in what or "all" in what:
        lst = []
        for i, exp_path in enumerate(expname):
            # Removed verbose per-experiment progress print
            # console.print(f"Reading: {i+1} / {len(expname)}", end="\r")

            path = exp_path / "pdata" / "1" / "procs"
            if path.exists():
                parms = read_params(path)

                if parms is not None:
                    parms['path'] = str(exp_path)
                    # Reshape from long to wide
                    parms_wide = parms.pivot(index='path', columns='name', values='value')
                    parms_wide.columns = [f'procs.{col}' for col in parms_wide.columns]
                    parms_wide = parms_wide.reset_index()
                    lst.append(parms_wide)

        if lst:
            # Find common columns
            common_cols = set(lst[0].columns)
            for df in lst[1:]:
                common_cols &= set(df.columns)
            common_cols = sorted(common_cols)

            res['procs'] = pd.concat([df[common_cols] for df in lst], ignore_index=True)
        else:
            res['procs'] = pd.DataFrame()

        if len(res['procs']) == 0:
            console.print("[yellow]readExperiment >> 0 found procs[/yellow]")
        else:
            console.print(f"[blue]readExperiment >> {len(res['procs'])} found procs params[/blue]")

    # Read QC
    if "qc" in what or "all" in what:
        lst = []
        for i, exp_path in enumerate(expname):
            # Removed verbose per-experiment progress print
            # console.print(f"Reading: {i+1} / {len(expname)}", end="\r")

            folder_path = exp_path / "pdata" / "1"
            # Find QC report files
            qc_files = list(folder_path.glob("*qc_report*.xml"))

            # Prefer 1_1_0 version if available
            if any("1_1_0.xml" in str(f) for f in qc_files):
                qc_files = [f for f in qc_files if "1_1_0.xml" in str(f)]

            if qc_files:
                qc = read_qc(qc_files[0])
                if qc is not None:
                    qc_data = qc['data']
                    # Create a flat dictionary from QC data
                    qc_dict = {'path': str(exp_path)}
                    lst.append(qc_dict)

        res['qc'] = pd.DataFrame(lst) if lst else pd.DataFrame()

        if len(res['qc']) == 0:
            console.print("[yellow]readExperiment >> 0 found qc[/yellow]")
        else:
            console.print(f"[blue]readExperiment >> {len(res['qc'])} found qc[/blue]")

    # Read title
    if "title" in what or "all" in what:
        lst = []
        for exp_path in expname:
            path = exp_path / "pdata" / "1" / "title"
            if path.exists():
                title_data = read_title(path)
                if title_data:
                    lst.append({'path': str(exp_path), 'title': title_data['value']})

        res['title'] = pd.DataFrame(lst)

        if len(res['title']) == 0:
            console.print("[yellow]readExperiment >> 0 found titles[/yellow]")
        else:
            console.print(f"[blue]readExperiment >> {len(res['title'])} found titles[/blue]")

    # Read ERETIC
    if "eretic" in what or "all" in what:
        lst = []
        for exp_path in expname:
            eretic_factor = None

            # Check for QuantFactorSample.xml
            eretic_path = exp_path / "QuantFactorSample.xml"
            if eretic_path.exists():
                eretic = read_eretic(eretic_path)
                if eretic is not None:
                    eretic_factor = eretic['ereticFactor'].iloc[0]

            # Check for F80 eretic_file.xml
            elif (exp_path / "pdata" / "1" / "eretic_file.xml").exists():
                eretic = read_eretic_f80(exp_path / "pdata" / "1" / "eretic_file.xml")
                if eretic is not None:
                    eretic_factor = eretic['samOneMolInt'].iloc[0]

            if eretic_factor is not None:
                lst.append({'path': str(exp_path), 'ereticFactor': eretic_factor})

        res['eretic'] = pd.DataFrame(lst)

        if len(res['eretic']) == 0:
            console.print("[yellow]readExperiment >> 0 found ereticFactors[/yellow]")
        else:
            console.print(f"[blue]readExperiment >> {len(res['eretic'])} found ereticFactors[/blue]")

    # Read spectrum
    procno = opts.get('procno', 1)

    if "spec" in what or "all" in what or "specOnly" in what:
        lst = []
        for exp_path in expname:
            spec_opts = opts.get('specOpts', {}).copy()

            # Find ERETIC factor if not provided
            if 'eretic' not in spec_opts:
                # Look in expno + 0 folder (ANPC structure)
                exp_str = str(exp_path)
                eretic_path = Path(exp_str[:-1] + "0")

                eretic_factor = 1

                if (eretic_path / "QuantFactorSample.xml").exists():
                    eretic = read_eretic(eretic_path / "QuantFactorSample.xml")
                    if eretic is not None:
                        eretic_factor = eretic['ereticFactor'].iloc[0]

                elif (eretic_path / "pdata" / "1" / "eretic_file.xml").exists():
                    eretic = read_eretic_f80(eretic_path / "pdata" / "1" / "eretic_file.xml")
                    if eretic is not None:
                        eretic_factor = eretic['samOneMolInt'].iloc[0]

                spec_opts['eretic'] = eretic_factor

                # Removed verbose per-experiment logging
                # if eretic_factor == 1:
                #     console.print(f"[red]readExperiment >> ereticFactor set to 1: {eretic_path}[/red]")

            spec = read_spectrum(exp_path, procno, procs=True, options=spec_opts)

            if spec is not None:
                lst.append({'path': str(exp_path), 'spec': [spec]})

        res['spec'] = pd.DataFrame(lst)

        # Removed verbose summary - parse_nmr handles the summary now
        # if len(res['spec']) == 0:
        #     console.print("[yellow]readExperiment >> 0 found spectrum(a)[/yellow]")
        # else:
        #     console.print(f"[blue]readExperiment >> {len(res['spec'])} found spectrum(a)[/blue]")

    # Read lipo
    if "lipo" in what or "all" in what:
        lst = []
        for exp_path in expname:
            folder_path = exp_path / "pdata" / "1"
            lipo_files = list(folder_path.glob("*lipo*.xml"))

            # Prefer 1_1_0 version
            if any("1_1_0" in str(f) for f in lipo_files):
                lipo_files = [f for f in lipo_files if "1_1_0" in str(f)]

            if lipo_files:
                lipoproteins = read_lipo(lipo_files[0])
                if lipoproteins is not None:
                    lipo_data = lipoproteins['data'].copy()
                    lipo_data['path'] = str(exp_path)
                    lst.append({'data': lipo_data})

        if lst:
            # Reshape lipo data from long to wide
            lipo_dfs = []
            for item in lst:
                df = item['data']
                # Pivot to wide format
                df_wide = df.pivot(index='path', columns='id', values='value')
                df_wide.columns = [f'value.{col}' for col in df_wide.columns]
                df_wide = df_wide.reset_index()
                lipo_dfs.append(df_wide)

            res['lipo'] = pd.concat(lipo_dfs, ignore_index=True) if lipo_dfs else pd.DataFrame()
        else:
            res['lipo'] = pd.DataFrame()

        if len(res['lipo']) == 0:
            console.print("[yellow]readExperiment >> 0 found lipo[/yellow]")
        else:
            console.print(f"[blue]readExperiment >> {len(res['lipo'])} found lipo[/blue]")

    # Read PACS
    if "pacs" in what or "all" in what:
        lst = []
        for exp_path in expname:
            folder_path = exp_path / "pdata" / "1"
            pacs_files = list(folder_path.glob("*pacs*.xml"))

            # Prefer 1_1_0 version
            if any("1_1_0" in str(f) for f in pacs_files):
                pacs_files = [f for f in pacs_files if "1_1_0" in str(f)]

            if pacs_files:
                pacs = read_pacs(pacs_files[0])
                if pacs is not None:
                    pacs_data = pacs['data'].copy()
                    pacs_data['path'] = str(exp_path)
                    lst.append({'data': pacs_data})

        if lst:
            # Reshape PACS data from long to wide
            pacs_dfs = []
            for item in lst:
                df = item['data']
                # Pivot to wide format
                df_wide = df.pivot(index='path', columns='name', values='conc_v')
                df_wide.columns = [f'value.{col}' for col in df_wide.columns]
                df_wide = df_wide.reset_index()
                pacs_dfs.append(df_wide)

            res['pacs'] = pd.concat(pacs_dfs, ignore_index=True) if pacs_dfs else pd.DataFrame()
        else:
            res['pacs'] = pd.DataFrame()

        if len(res['pacs']) == 0:
            console.print("[yellow]readExperiment >> 0 found pacs[/yellow]")
        else:
            console.print(f"[blue]readExperiment >> {len(res['pacs'])} found pacs[/blue]")

    # Read quant
    if "quant" in what or "all" in what:
        lst = []
        for exp_path in expname:
            folder_path = exp_path / "pdata" / "1"

            # Priority order for quant files
            priority = [
                "plasma_quant_report_2_1_0.xml",
                "plasma_quant_report.xml",
                "urine_quant_report_e_1_2_0.xml",
                "urine_quant_report_e_ver_1_0.xml",
                "urine_quant_report_e.xml",
                "urine_quant_report_b_ver_1_0.xml",
                "urine_quant_report_b.xml",
                "urine_quant_report_ne_ver_1_0.xml",
                "urine_quant_report_ne.xml"
            ]

            # Find all quant files
            quant_files = list(folder_path.glob("*quant*.xml"))

            # Pick highest priority match
            chosen = None
            for priority_file in priority:
                matches = [f for f in quant_files if priority_file in str(f)]
                if matches:
                    chosen = matches[0]
                    break

            if chosen:
                quant = read_quant(chosen)
                if quant is not None:
                    quant_data = quant['data'].copy()
                    quant_data['path'] = str(exp_path)
                    lst.append({'data': quant_data})

        if lst:
            # Reshape quant data from long to wide
            quant_dfs = []
            for item in lst:
                df = item['data']
                # Pivot to wide format
                df_wide = df.pivot(index='path', columns='name', values='rawConc')
                df_wide.columns = [f'value.{col}' for col in df_wide.columns]
                df_wide = df_wide.reset_index()
                quant_dfs.append(df_wide)

            res['quant'] = pd.concat(quant_dfs, ignore_index=True) if quant_dfs else pd.DataFrame()
        else:
            res['quant'] = pd.DataFrame()

        if len(res['quant']) == 0:
            console.print("[yellow]readExperiment >> 0 found quant[/yellow]")
        else:
            console.print(f"[blue]readExperiment >> {len(res['quant'])} found quant[/blue]")

    return res
