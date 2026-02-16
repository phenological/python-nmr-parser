"""Lipoprotein calculation functions for extending raw measurements."""

import pandas as pd
import numpy as np
from typing import Dict, Any


def extend_lipo_value(lipo: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate derived lipoprotein values from raw data.

    Extends lipoprotein measurements by calculating:
    - calc: Total lipids (TL) and cholesterol esters (CE) from sums
    - pct: Percentage composition within each fraction
    - frac: Fractional distribution across fractions

    Parameters
    ----------
    lipo : dict
        Dictionary with 'data' key containing DataFrame with columns:
        - id: Parameter ID (e.g., 'HDTG', 'VLTG', 'L1CH', etc.)
        - value: Measured value

    Returns
    -------
    pd.DataFrame
        DataFrame with original values plus derived metrics.
        Columns are named with suffixes: _calc, _pct, _frac

    Notes
    -----
    Generates 150+ derived metrics from 112 raw measurements:
    - 26 calc metrics (sums and differences)
    - 100+ pct metrics (composition percentages)
    - 100+ frac metrics (distribution percentages)

    Examples
    --------
    >>> extended = extend_lipo_value(lipo)
    >>> extended['HDTL_calc']  # Total HDL lipids
    >>> extended['HDCE_pct']   # HDL CE as % of HDL total
    >>> extended['H1TG_frac']  # H1 TG as % of HD TG
    """
    # Validate input structure
    if not isinstance(lipo, dict):
        raise TypeError(f"lipo must be a dict, got {type(lipo).__name__}")

    if 'data' not in lipo:
        raise ValueError("lipo dict must contain 'data' key")

    if not isinstance(lipo['data'], pd.DataFrame):
        raise TypeError(f"lipo['data'] must be a DataFrame, got {type(lipo['data']).__name__}. "
                       "Note: extend_lipo() only works with read_lipo() output, not read_experiment() output.")

    # Check for required columns
    required_cols = ['id', 'value']
    missing_cols = [col for col in required_cols if col not in lipo['data'].columns]
    if missing_cols:
        raise ValueError(f"lipo['data'] missing required columns: {missing_cols}. "
                        "Note: extend_lipo() expects long-format data from read_lipo(), "
                        "not wide-format data from read_experiment().")

    # Create DataFrame with IDs as columns
    df = lipo['data'].set_index('id')['value'].to_frame().T

    # Initialize result dictionaries
    calc = {}
    pct = {}
    frac = {}

    # ========== CALCULATED METRICS (SUMS AND DIFFERENCES) ==========
    # Total lipids (TL) = TG + CH + PL
    calc['HDTL'] = df['HDTG'] + df['HDCH'] + df['HDPL']
    calc['VLTL'] = df['VLTG'] + df['VLCH'] + df['VLPL']
    calc['IDTL'] = df['IDTG'] + df['IDCH'] + df['IDPL']
    calc['LDTL'] = df['LDTG'] + df['LDCH'] + df['LDPL']

    # Cholesterol esters (CE) = CH - FC
    calc['HDCE'] = df['HDCH'] - df['HDFC']
    calc['VLCE'] = df['VLCH'] - df['VLFC']
    calc['IDCE'] = df['IDCH'] - df['IDFC']
    calc['LDCE'] = df['LDCH'] - df['LDFC']

    # Total particle number
    calc['TBPN'] = df['VLPN'] + df['IDPN'] + df['L1PN'] + df['L2PN'] + df['L3PN'] + df['L4PN'] + df['L5PN'] + df['L6PN']

    # Apo-A1 and Apo-A2 totals
    calc['HDA1'] = df['H1A1'] + df['H2A1'] + df['H3A1'] + df['H4A1']
    calc['HDA2'] = df['H1A2'] + df['H2A2'] + df['H3A2'] + df['H4A2']

    # LDL Apo-B
    calc['LDAB'] = df['L1AB'] + df['L2AB'] + df['L3AB'] + df['L4AB'] + df['L5AB'] + df['L6AB']

    # Subfraction total lipids
    for letter, rng in [('V', range(1, 6)), ('L', range(1, 7)), ('H', range(1, 5))]:
        for i in rng:
            calc[f'{letter}{i}TL'] = df[f'{letter}{i}TG'] + df[f'{letter}{i}CH'] + df[f'{letter}{i}PL']

    # ========== PERCENTAGE METRICS (COMPOSITION) ==========
    # Main fraction CE percentages
    pct['HDCE'] = np.round(calc['HDCE'] / calc['HDTL'], 4) * 100
    pct['VLCE'] = np.round(calc['VLCE'] / calc['VLTL'], 4) * 100
    pct['IDCE'] = np.round(calc['IDCE'] / calc['IDTL'], 4) * 100
    pct['LDCE'] = np.round(calc['LDCE'] / calc['LDTL'], 4) * 100

    # Particle number percentages
    pct['VLPN'] = np.round(df['VLPN'] / calc['TBPN'], 4) * 100
    pct['IDPN'] = np.round(df['IDPN'] / calc['TBPN'], 4) * 100

    # Subfraction CE percentages
    for letter, rng in [('H', range(1, 5)), ('V', range(1, 6)), ('L', range(1, 7))]:
        for i in rng:
            ch_col = f'{letter}{i}CH'
            fc_col = f'{letter}{i}FC'
            ce_col = f'{letter}{i}CE'
            tl_col = f'{letter}{i}TL'
            pct[ce_col] = np.round((df[ch_col] - df[fc_col]) / calc[tl_col], 4) * 100

    # Subfraction component percentages (TG, FC, PL as % of TL)
    for letter, rng in [('H', range(1, 5)), ('V', range(1, 6)), ('L', range(1, 7))]:
        for i in rng:
            tl_col = f'{letter}{i}TL'
            for suffix in ['TG', 'FC', 'PL']:
                col = f'{letter}{i}{suffix}'
                pct[col] = np.round(df[col] / calc[tl_col], 4) * 100

    # Main fraction component percentages
    for prefix in ['HD', 'VL', 'ID', 'LD']:
        tl_col = f'{prefix}TL'
        for suffix in ['TG', 'CH', 'FC', 'PL']:
            col = f'{prefix}{suffix}'
            pct[col] = np.round(df[col] / calc[tl_col], 4) * 100

    # ========== FRACTIONAL METRICS (DISTRIBUTION) ==========
    # Subfraction CE as fraction of main fraction CE
    for letter, rng in [('H', range(1, 5)), ('V', range(1, 6)), ('L', range(1, 7))]:
        for i in rng:
            ch_col = f'{letter}{i}CH'
            fc_col = f'{letter}{i}FC'
            ce_col = f'{letter}{i}CE'

            # Determine denominator
            if letter == 'V':
                denom = 'VLCE'
            elif letter == 'H':
                denom = 'HDCE'
            else:  # letter == 'L'
                denom = 'LDCE'

            frac[ce_col] = np.round((df[ch_col] - df[fc_col]) / calc[denom], 4) * 100

    # Subfraction components as fraction of main fraction components
    # Note: Uses raw data in denominator (not calc), as per R code comments
    for letter, rng in [('H', range(1, 5)), ('V', range(1, 6)), ('L', range(1, 7))]:
        for i in rng:
            for suffix in ['TG', 'CH', 'FC', 'PL']:
                for prefix in ['HD', 'VL', 'LD']:  # Skip 'ID'
                    col = f'{letter}{i}{suffix}'
                    denom_col = f'{prefix}{suffix}'
                    frac[col] = np.round(df[col] / df[denom_col], 4) * 100

    # HDL Apo fractions
    for i in range(1, 5):
        for suffix in ['A1', 'A2']:
            col = f'H{i}{suffix}'
            denom = f'HD{suffix}'
            frac[col] = np.round(df[col] / calc[denom], 4) * 100

    # LDL Apo-B and particle number fractions
    for i in range(1, 7):
        # Apo-B fraction
        col = f'L{i}AB'
        frac[col] = np.round(df[col] / calc['LDAB'], 4) * 100

        # Particle number fraction
        col = f'L{i}PN'
        frac[col] = np.round(df[col] / calc['TBPN'], 4) * 100

    # Convert to Series for easier concatenation
    calc_series = pd.Series(calc, name=0)
    pct_series = pd.Series(pct, name=0)
    frac_series = pd.Series(frac, name=0)

    # Rename columns with suffixes
    calc_series.index = [f'{idx}_calc' for idx in calc_series.index]
    pct_series.index = [f'{idx}_pct' for idx in pct_series.index]
    frac_series.index = [f'{idx}_frac' for idx in frac_series.index]

    # Combine all metrics
    result = pd.concat([df.iloc[0], calc_series, pct_series, frac_series])

    return result.to_frame().T


def extend_lipo(lipo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extend lipoprotein data with calculated fields and reference ranges.

    Calculates total lipids, fractions, and percentages, then extends
    with metadata (fraction names, abbreviations, reference ranges).

    Parameters
    ----------
    lipo : dict
        Dictionary with 'data' and 'version' keys from read_lipo()

    Returns
    -------
    dict
        Dictionary with keys:
        - data: pd.DataFrame with extended metrics (316 rows from 112 raw)
        - version: Version string from input

    Notes
    -----
    Three types of calculated metrics:
    - **calc**: Sums (e.g., HDTL = HDTG + HDCH + HDPL) and differences (CE = CH - FC)
    - **pct**: Composition percentages (e.g., HDCE as % of HDTL)
    - **frac**: Distribution percentages (e.g., H1TG as % of HDTG)

    Examples
    --------
    >>> extended = extend_lipo(lipo)
    >>> len(extended['data'])  # 316 rows
    >>> extended['data']['id'].tolist()  # Includes _calc, _pct, _frac IDs
    >>> extended['data'][['id', 'value', 'unit', 'refMin', 'refMax']].head()
    """
    # Get extended values
    df_extended = extend_lipo_value(lipo)

    # Transpose to long format
    extended_long = df_extended.T.reset_index()
    extended_long.columns = ['id', 'value']

    # Match with original data to get metadata
    original_df = lipo['data'].set_index('id')

    # Initialize result DataFrame
    result = pd.DataFrame()
    result['id'] = extended_long['id']
    result['value'] = extended_long['value']

    # Get metadata from original data where available
    result['fraction'] = result['id'].map(lambda x: original_df.loc[x, 'fraction'] if x in original_df.index else None)
    result['name'] = result['id'].map(lambda x: original_df.loc[x, 'name'] if x in original_df.index else None)
    result['abbr'] = result['id'].map(lambda x: original_df.loc[x, 'abbr'] if x in original_df.index else None)
    result['type'] = result['id'].map(lambda x: original_df.loc[x, 'type'] if x in original_df.index else None)
    result['unit'] = result['id'].map(lambda x: original_df.loc[x, 'unit'] if x in original_df.index else None)
    result['refMax'] = result['id'].map(lambda x: original_df.loc[x, 'refMax'] if x in original_df.index else None)
    result['refMin'] = result['id'].map(lambda x: original_df.loc[x, 'refMin'] if x in original_df.index else None)
    result['refUnit'] = result['id'].map(lambda x: original_df.loc[x, 'refUnit'] if x in original_df.index else None)

    # Calculate reference ranges for derived metrics
    # Create temporary lipo with refMax as values
    lipo_max = {'data': lipo['data'].copy(), 'version': lipo['version']}
    lipo_max['data']['value'] = lipo['data']['refMax']
    ma = extend_lipo_value(lipo_max).T

    # Create temporary lipo with refMin as values
    lipo_min = {'data': lipo['data'].copy(), 'version': lipo['version']}
    lipo_min['data']['value'] = lipo['data']['refMin']
    mi = extend_lipo_value(lipo_min).T

    # Set reference ranges for derived metrics
    for idx in result.index:
        id_val = result.loc[idx, 'id']
        if id_val in ma.index and id_val in mi.index:
            ma_val = ma.loc[id_val, 0]
            mi_val = mi.loc[id_val, 0]

            # Handle case where .loc returns a Series (duplicate indices)
            if isinstance(ma_val, pd.Series):
                ma_val = ma_val.iloc[0]
            if isinstance(mi_val, pd.Series):
                mi_val = mi_val.iloc[0]

            # refMax is the larger value, refMin is the smaller
            result.loc[idx, 'refMax'] = max(ma_val, mi_val)
            result.loc[idx, 'refMin'] = min(ma_val, mi_val)

    # Fill missing metadata for derived metrics
    # Fraction: Try to match from base ID
    for idx in result.index:
        if pd.isna(result.loc[idx, 'fraction']):
            id_val = result.loc[idx, 'id']
            # Try matching with CE->CH replacement
            base_id = id_val.replace('CE', 'CH').replace('_calc', '').replace('_pct', '').replace('_frac', '')
            base_id = base_id[:4] if len(base_id) >= 4 else base_id

            if base_id in original_df.index:
                result.loc[idx, 'fraction'] = original_df.loc[base_id, 'fraction']
            else:
                # Try matching by prefix (first 2 chars)
                prefix = id_val[:2]
                matches = [i for i in original_df.index if i.startswith(prefix)]
                if matches:
                    result.loc[idx, 'fraction'] = original_df.loc[matches[0], 'fraction']

    # Name: Set specific names for CE and TL metrics
    for idx in result.index:
        if pd.isna(result.loc[idx, 'name']):
            id_val = result.loc[idx, 'id']

            # Cholesterol Ester
            if 'CE' in id_val:
                result.loc[idx, 'name'] = "Cholesterol Ester"
            # Total Lipids
            elif 'TL' in id_val:
                result.loc[idx, 'name'] = "Triglycerides, Cholesterol, Phospholipids"
            # Try matching base ID
            else:
                base_id = id_val[:4] if len(id_val) >= 4 else id_val
                if base_id in original_df.index:
                    result.loc[idx, 'name'] = original_df.loc[base_id, 'name']

    # Abbreviation: Match from CE->CH replacement
    for idx in result.index:
        if pd.isna(result.loc[idx, 'abbr']):
            id_val = result.loc[idx, 'id']
            base_id = id_val.replace('CE', 'CH').replace('_calc', '').replace('_pct', '').replace('_frac', '')
            base_id = base_id[:4] if len(base_id) >= 4 else base_id

            if base_id in original_df.index:
                abbr = original_df.loc[base_id, 'abbr']
                if pd.notna(abbr) and 'CE' in id_val:
                    result.loc[idx, 'abbr'] = abbr.replace('-Chol', '-CE')
                else:
                    result.loc[idx, 'abbr'] = abbr
            else:
                # Try TG replacement for TL
                base_id_tg = id_val.replace('TL', 'TG').replace('_calc', '').replace('_pct', '').replace('_frac', '')
                base_id_tg = base_id_tg[:4] if len(base_id_tg) >= 4 else base_id_tg
                if base_id_tg in original_df.index:
                    result.loc[idx, 'abbr'] = original_df.loc[base_id_tg, 'abbr']

    # Type: Set all derived metrics as "prediction"
    result['type'] = result['type'].fillna('prediction')

    # Unit: Set units for calc metrics
    for idx in result.index:
        if pd.isna(result.loc[idx, 'unit']):
            id_val = result.loc[idx, 'id']
            if '_calc' in id_val:
                if id_val == 'TBPN_calc':
                    result.loc[idx, 'unit'] = 'nmol/L'
                else:
                    result.loc[idx, 'unit'] = 'mg/dL'
            else:
                result.loc[idx, 'unit'] = '-/-'

    # RefUnit: Same as unit
    result['refUnit'] = result['unit']

    # Correct typo in XML (row 9 should be Apo-B100 / Apo-A1)
    if len(result) > 8:
        result.loc[8, 'name'] = "Apo-B100 / Apo-A1"

    # Clean abbreviations (remove spaces)
    result['abbr'] = result['abbr'].str.replace(' ', '')

    # Create publication tags
    result['tag'] = result['name'] + ', ' + result['abbr']

    # Special tags for common parameters
    result.loc[result['id'].str.contains('TPTG'), 'tag'] = "Triglycerides, total"
    result.loc[result['id'].str.contains('TPCH'), 'tag'] = "Cholesterol, total"
    result.loc[result['id'].str.contains('LDCH'), 'tag'] = "Cholesterol, LDL"
    result.loc[result['id'].str.contains('HDCH'), 'tag'] = "Cholesterol, HDL"
    result.loc[result['id'].str.contains('TPA1'), 'tag'] = "Apo-A1, total"
    result.loc[result['id'].str.contains('TPA2'), 'tag'] = "Apo-A2, total"
    result.loc[result['id'].str.contains('TPAB'), 'tag'] = "Apo-B100, total"
    result.loc[result['id'].str.contains('LDHD'), 'tag'] = "LDL-Chol/HDL-Chol"
    result.loc[result['id'].str.contains('ABA1'), 'tag'] = "Apo-B100/Apo-A1"
    result.loc[result['id'].str.contains('TBPN'), 'tag'] = "Apo-B100, particle number"
    result.loc[result['id'].str.contains('VLPN'), 'tag'] = "VLDL, particle number"
    result.loc[result['id'].str.contains('IDPN'), 'tag'] = "IDL, particle number"
    result.loc[result['id'].str.contains('LDPN'), 'tag'] = "LDL, particle number"
    result.loc[result['id'].str.contains('L1PN'), 'tag'] = "LD1, particle number"
    result.loc[result['id'].str.contains('L2PN'), 'tag'] = "LD2, particle number"
    result.loc[result['id'].str.contains('L3PN'), 'tag'] = "LD3, particle number"
    result.loc[result['id'].str.contains('L4PN'), 'tag'] = "LD4, particle number"
    result.loc[result['id'].str.contains('L5PN'), 'tag'] = "LD5, particle number"
    result.loc[result['id'].str.contains('L6PN'), 'tag'] = "LD6, particle number"

    # Reorder columns
    result = result[['fraction', 'name', 'abbr', 'id', 'type', 'value',
                     'unit', 'refMax', 'refMin', 'refUnit', 'tag']]

    return {
        'data': result.reset_index(drop=True),
        'version': lipo['version']
    }
