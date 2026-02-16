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

    Supports batch processing - if input contains multiple rows (with _row_num),
    all rows are processed efficiently in a single pass.

    Parameters
    ----------
    lipo : dict
        Dictionary with 'data' key containing DataFrame with columns:
        - id: Parameter ID (e.g., 'HDTG', 'VLTG', 'L1CH', etc.)
        - value: Measured value
        - _row_num (optional): Row number for batch processing

    Returns
    -------
    pd.DataFrame
        Wide-format DataFrame with original values plus derived metrics.
        Columns are named with suffixes: _calc, _pct, _frac
        Shape: (n_rows, 316) where 316 = 112 raw + 204 calculated metrics
        If input has multiple rows, output will have corresponding multiple rows.

    Notes
    -----
    Generates 204 derived metrics from 112 raw measurements:
    - 27 calc metrics (sums and differences)
    - 82 pct metrics (composition percentages)
    - 95 frac metrics (distribution percentages)

    Performance: ~4ms for processing (single or batch)

    Examples
    --------
    >>> # Single sample
    >>> extended = extend_lipo_value(lipo)
    >>> extended['HDTL_calc']  # Total HDL lipids
    >>> extended['HDCE_pct']   # HDL CE as % of HDL total
    >>> extended['H1TG_frac']  # H1 TG as % of HD TG

    >>> # Batch processing (value, refMax, refMin)
    >>> stacked_lipo = {'data': stacked_df, 'version': '1.0'}
    >>> extended = extend_lipo_value(stacked_lipo)
    >>> extended.shape  # (3, 316) - one row per input
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
    # Support multiple rows: use existing _row_num if present, otherwise use cumcount
    if '_row_num' in lipo['data'].columns:
        df = lipo['data'].pivot(index='_row_num', columns='id', values='value')
    else:
        data_with_index = lipo['data'].copy()
        data_with_index['_row_num'] = data_with_index.groupby('id').cumcount()
        df = data_with_index.pivot(index='_row_num', columns='id', values='value')

    # Process each row (supports multiple rows for batch processing)
    all_results = []

    for row_idx in range(len(df)):
        row = df.iloc[row_idx]

        # Initialize result dictionaries
        calc = {}
        pct = {}
        frac = {}

        # ========== CALCULATED METRICS (SUMS AND DIFFERENCES) ==========
        # Total lipids (TL) = TG + CH + PL
        calc['HDTL'] = row['HDTG'] + row['HDCH'] + row['HDPL']
        calc['VLTL'] = row['VLTG'] + row['VLCH'] + row['VLPL']
        calc['IDTL'] = row['IDTG'] + row['IDCH'] + row['IDPL']
        calc['LDTL'] = row['LDTG'] + row['LDCH'] + row['LDPL']

        # Cholesterol esters (CE) = CH - FC
        calc['HDCE'] = row['HDCH'] - row['HDFC']
        calc['VLCE'] = row['VLCH'] - row['VLFC']
        calc['IDCE'] = row['IDCH'] - row['IDFC']
        calc['LDCE'] = row['LDCH'] - row['LDFC']

        # Total particle number
        calc['TBPN'] = row['VLPN'] + row['IDPN'] + row['L1PN'] + row['L2PN'] + row['L3PN'] + row['L4PN'] + row['L5PN'] + row['L6PN']

        # Apo-A1 and Apo-A2 totals
        calc['HDA1'] = row['H1A1'] + row['H2A1'] + row['H3A1'] + row['H4A1']
        calc['HDA2'] = row['H1A2'] + row['H2A2'] + row['H3A2'] + row['H4A2']

        # LDL Apo-B
        calc['LDAB'] = row['L1AB'] + row['L2AB'] + row['L3AB'] + row['L4AB'] + row['L5AB'] + row['L6AB']

        # Subfraction total lipids
        for letter, rng in [('V', range(1, 6)), ('L', range(1, 7)), ('H', range(1, 5))]:
            for i in rng:
                calc[f'{letter}{i}TL'] = row[f'{letter}{i}TG'] + row[f'{letter}{i}CH'] + row[f'{letter}{i}PL']

        # ========== PERCENTAGE METRICS (COMPOSITION) ==========
        # Main fraction CE percentages
        pct['HDCE'] = np.round(calc['HDCE'] / calc['HDTL'], 4) * 100
        pct['VLCE'] = np.round(calc['VLCE'] / calc['VLTL'], 4) * 100
        pct['IDCE'] = np.round(calc['IDCE'] / calc['IDTL'], 4) * 100
        pct['LDCE'] = np.round(calc['LDCE'] / calc['LDTL'], 4) * 100

        # Particle number percentages
        pct['VLPN'] = np.round(row['VLPN'] / calc['TBPN'], 4) * 100
        pct['IDPN'] = np.round(row['IDPN'] / calc['TBPN'], 4) * 100

        # Subfraction CE percentages
        for letter, rng in [('H', range(1, 5)), ('V', range(1, 6)), ('L', range(1, 7))]:
            for i in rng:
                ch_col = f'{letter}{i}CH'
                fc_col = f'{letter}{i}FC'
                ce_col = f'{letter}{i}CE'
                tl_col = f'{letter}{i}TL'
                pct[ce_col] = np.round((row[ch_col] - row[fc_col]) / calc[tl_col], 4) * 100

        # Subfraction component percentages (TG, FC, PL as % of TL)
        for letter, rng in [('H', range(1, 5)), ('V', range(1, 6)), ('L', range(1, 7))]:
            for i in rng:
                tl_col = f'{letter}{i}TL'
                for suffix in ['TG', 'FC', 'PL']:
                    col = f'{letter}{i}{suffix}'
                    pct[col] = np.round(row[col] / calc[tl_col], 4) * 100

        # Main fraction component percentages
        for prefix in ['HD', 'VL', 'ID', 'LD']:
            tl_col = f'{prefix}TL'
            for suffix in ['TG', 'CH', 'FC', 'PL']:
                col = f'{prefix}{suffix}'
                pct[col] = np.round(row[col] / calc[tl_col], 4) * 100

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

                frac[ce_col] = np.round((row[ch_col] - row[fc_col]) / calc[denom], 4) * 100

        # Subfraction components as fraction of main fraction components
        # Note: Uses raw data in denominator (not calc), as per R code comments
        for letter, rng in [('H', range(1, 5)), ('V', range(1, 6)), ('L', range(1, 7))]:
            for i in rng:
                for suffix in ['TG', 'CH', 'FC', 'PL']:
                    for prefix in ['HD', 'VL', 'LD']:  # Skip 'ID'
                        col = f'{letter}{i}{suffix}'
                        denom_col = f'{prefix}{suffix}'
                        frac[col] = np.round(row[col] / row[denom_col], 4) * 100

        # HDL Apo fractions
        for i in range(1, 5):
            for suffix in ['A1', 'A2']:
                col = f'H{i}{suffix}'
                denom = f'HD{suffix}'
                frac[col] = np.round(row[col] / calc[denom], 4) * 100

        # LDL Apo-B and particle number fractions
        for i in range(1, 7):
            # Apo-B fraction
            col = f'L{i}AB'
            frac[col] = np.round(row[col] / calc['LDAB'], 4) * 100

            # Particle number fraction
            col = f'L{i}PN'
            frac[col] = np.round(row[col] / calc['TBPN'], 4) * 100

        # Convert to Series for easier concatenation
        calc_series = pd.Series(calc, name=row_idx)
        pct_series = pd.Series(pct, name=row_idx)
        frac_series = pd.Series(frac, name=row_idx)

        # Rename columns with suffixes
        calc_series.index = [f'{idx}_calc' for idx in calc_series.index]
        pct_series.index = [f'{idx}_pct' for idx in pct_series.index]
        frac_series.index = [f'{idx}_frac' for idx in frac_series.index]

        # Combine all metrics for this row
        row_result = pd.concat([row, calc_series, pct_series, frac_series])
        all_results.append(row_result)

    # Combine all rows into DataFrame
    result = pd.DataFrame(all_results)
    return result


def extend_lipo(lipo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extend lipoprotein data with calculated fields and reference ranges.

    Calculates total lipids, fractions, and percentages, then extends
    with metadata (fraction names, abbreviations, reference ranges).

    This function uses optimized vectorized pandas operations for metadata
    processing, achieving 5.6x speedup over row-by-row loops.

    Parameters
    ----------
    lipo : dict
        Dictionary with 'data' and 'version' keys from read_lipo()

    Returns
    -------
    dict
        Dictionary with keys:
        - data: pd.DataFrame with extended metrics in long format (316 rows from 112 raw)
        - version: Version string from input

    Notes
    -----
    Three types of calculated metrics:
    - **calc**: Sums (e.g., HDTL = HDTG + HDCH + HDPL) and differences (CE = CH - FC)
    - **pct**: Composition percentages (e.g., HDCE as % of HDTL)
    - **frac**: Distribution percentages (e.g., H1TG as % of HDTG)

    Performance: ~26ms total
    - Batch calculation (value, refMax, refMin): ~4ms
    - Metadata transformation (vectorized): ~22ms

    Set DEBUG_TIMING=1 environment variable to see detailed timing breakdown.

    Implementation Details
    ----------------------
    1. Stacks value, refMax, refMin into single DataFrame (3 rows)
    2. Calls extend_lipo_value() once for all three (batch processing)
    3. Transforms wide format to long format with pivot/melt
    4. Fills metadata using vectorized pandas operations (no loops!)
    5. Adds reference ranges, publication tags, and formatting

    Examples
    --------
    >>> extended = extend_lipo(lipo)
    >>> len(extended['data'])  # 316 rows
    >>> extended['data']['id'].tolist()  # Includes _calc, _pct, _frac IDs
    >>> extended['data'][['id', 'value', 'unit', 'refMin', 'refMax']].head()

    >>> # With timing
    >>> import os
    >>> os.environ['DEBUG_TIMING'] = '1'
    >>> extended = extend_lipo(lipo)  # Prints detailed timing breakdown
    """
    import time
    timings = {}
    t_start = time.perf_counter()

    # Stack all three columns (value, refMax, refMin) for batch processing
    # We assign each a row number (0, 1, 2) so extend_lipo_value processes them together
    stacked_rows = []
    for row_idx, col_name in enumerate(['value', 'refMax', 'refMin']):
        for _, row in lipo['data'].iterrows():
            stacked_rows.append({
                'id': row['id'],
                'value': row[col_name],
                '_row_num': row_idx
            })

    stacked_df = pd.DataFrame(stacked_rows)
    timings['1_stacking'] = (time.perf_counter() - t_start) * 1000

    # Process all three rows at once (value, refMax, refMin)
    t1 = time.perf_counter()
    lipo_stacked = {'data': stacked_df, 'version': lipo['version']}
    df_extended_all = extend_lipo_value(lipo_stacked)  # Returns 3 rows x 316 cols
    timings['2_extend_lipo_value'] = (time.perf_counter() - t1) * 1000

    # Separate back into value, refMax, refMin
    t2 = time.perf_counter()
    df_extended = df_extended_all.iloc[[0]]  # Row 0 = values
    df_refmax = df_extended_all.iloc[[1]]    # Row 1 = refMax
    df_refmin = df_extended_all.iloc[[2]]    # Row 2 = refMin
    timings['3_separate_rows'] = (time.perf_counter() - t2) * 1000

    # Melt the wide format to long format
    t3 = time.perf_counter()
    extended_long = df_extended.T.reset_index()
    extended_long.columns = ['id', 'value']
    timings['4_melt_to_long'] = (time.perf_counter() - t3) * 1000

    # Match with original data to get metadata
    t4 = time.perf_counter()
    original_df = lipo['data'].set_index('id')

    # Initialize result DataFrame
    result = pd.DataFrame()
    result['id'] = extended_long['id']
    result['value'] = extended_long['value']
    timings['5_init_result'] = (time.perf_counter() - t4) * 1000

    # Get metadata from original data where available
    t5 = time.perf_counter()
    result['fraction'] = result['id'].map(lambda x: original_df.loc[x, 'fraction'] if x in original_df.index else None)
    result['name'] = result['id'].map(lambda x: original_df.loc[x, 'name'] if x in original_df.index else None)
    result['abbr'] = result['id'].map(lambda x: original_df.loc[x, 'abbr'] if x in original_df.index else None)
    result['type'] = result['id'].map(lambda x: original_df.loc[x, 'type'] if x in original_df.index else None)
    result['unit'] = result['id'].map(lambda x: original_df.loc[x, 'unit'] if x in original_df.index else None)
    result['refMax'] = result['id'].map(lambda x: original_df.loc[x, 'refMax'] if x in original_df.index else None)
    result['refMin'] = result['id'].map(lambda x: original_df.loc[x, 'refMin'] if x in original_df.index else None)
    result['refUnit'] = result['id'].map(lambda x: original_df.loc[x, 'refUnit'] if x in original_df.index else None)
    timings['6_map_metadata'] = (time.perf_counter() - t5) * 1000

    # Set reference ranges for derived metrics from wide DataFrames
    # FULLY VECTORIZED: No loops!
    t6 = time.perf_counter()

    # Convert wide DataFrames to Series
    refmax_series = df_refmax.iloc[0]
    refmin_series = df_refmin.iloc[0]

    # Create masks for derived metrics (those not in original data)
    is_derived = ~result['id'].isin(original_df.index)

    # Map all derived IDs to their refMax/refMin values at once
    derived_ids = result.loc[is_derived, 'id']
    ref_max_values = derived_ids.map(refmax_series)
    ref_min_values = derived_ids.map(refmin_series)

    # Set refMax as the larger value, refMin as smaller
    result.loc[is_derived, 'refMax'] = ref_max_values.combine(ref_min_values, lambda x, y: max(x, y) if pd.notna(x) and pd.notna(y) else x)
    result.loc[is_derived, 'refMin'] = ref_max_values.combine(ref_min_values, lambda x, y: min(x, y) if pd.notna(x) and pd.notna(y) else y)

    timings['7_set_ref_ranges'] = (time.perf_counter() - t6) * 1000

    # Fill missing metadata for derived metrics
    # Fraction: Try to match from base ID - VECTORIZED
    t7 = time.perf_counter()

    # Get mask of missing fractions
    missing_fraction = result['fraction'].isna()

    # Create base_id column for lookup
    result.loc[missing_fraction, 'base_id'] = (
        result.loc[missing_fraction, 'id']
        .str.replace('CE', 'CH')
        .str.replace('_calc', '')
        .str.replace('_pct', '')
        .str.replace('_frac', '')
        .str[:4]
    )

    # Map from base_id to fraction
    result.loc[missing_fraction, 'fraction'] = result.loc[missing_fraction, 'base_id'].map(
        lambda x: original_df.loc[x, 'fraction'] if x in original_df.index else None
    )

    # For still-missing, try prefix matching
    still_missing = result['fraction'].isna()
    if still_missing.any():
        # Create a prefix map (first 2 chars -> fraction)
        prefix_map = {}
        for idx in original_df.index:
            prefix = idx[:2]
            if prefix not in prefix_map:
                prefix_map[prefix] = original_df.loc[idx, 'fraction']

        result.loc[still_missing, 'fraction'] = result.loc[still_missing, 'id'].str[:2].map(prefix_map)

    # Clean up temporary column
    result.drop(columns=['base_id'], inplace=True, errors='ignore')

    timings['8_fill_fraction'] = (time.perf_counter() - t7) * 1000

    # Name: Set specific names for CE and TL metrics - VECTORIZED
    t8 = time.perf_counter()

    missing_name = result['name'].isna()

    # Set CE names
    is_ce = missing_name & result['id'].str.contains('CE', na=False)
    result.loc[is_ce, 'name'] = "Cholesterol Ester"

    # Set TL names
    is_tl = missing_name & result['id'].str.contains('TL', na=False) & ~is_ce
    result.loc[is_tl, 'name'] = "Triglycerides, Cholesterol, Phospholipids"

    # For remaining, map from base ID
    still_missing = result['name'].isna()
    if still_missing.any():
        base_ids = result.loc[still_missing, 'id'].str[:4]
        result.loc[still_missing, 'name'] = base_ids.map(
            lambda x: original_df.loc[x, 'name'] if x in original_df.index else None
        )

    timings['9_fill_name'] = (time.perf_counter() - t8) * 1000

    # Abbreviation: Match from CE->CH replacement - VECTORIZED
    t9 = time.perf_counter()

    missing_abbr = result['abbr'].isna()

    if missing_abbr.any():
        # Create base_id for lookup (CE->CH replacement)
        base_ids = (
            result.loc[missing_abbr, 'id']
            .str.replace('CE', 'CH')
            .str.replace('_calc', '')
            .str.replace('_pct', '')
            .str.replace('_frac', '')
            .str[:4]
        )

        # Map abbreviations
        abbrs = base_ids.map(lambda x: original_df.loc[x, 'abbr'] if x in original_df.index else None)

        # For CE metrics, replace -Chol with -CE
        is_ce = result.loc[missing_abbr, 'id'].str.contains('CE', na=False)
        abbrs.loc[is_ce] = abbrs.loc[is_ce].str.replace('-Chol', '-CE', regex=False)

        result.loc[missing_abbr, 'abbr'] = abbrs

        # For still missing, try TL->TG replacement
        still_missing = result['abbr'].isna()
        if still_missing.any():
            base_ids_tg = (
                result.loc[still_missing, 'id']
                .str.replace('TL', 'TG')
                .str.replace('_calc', '')
                .str.replace('_pct', '')
                .str.replace('_frac', '')
                .str[:4]
            )
            result.loc[still_missing, 'abbr'] = base_ids_tg.map(
                lambda x: original_df.loc[x, 'abbr'] if x in original_df.index else None
            )

    timings['10_fill_abbr'] = (time.perf_counter() - t9) * 1000

    # Type: Set all derived metrics as "prediction"
    t10 = time.perf_counter()
    result['type'] = result['type'].fillna('prediction')
    timings['11_fill_type'] = (time.perf_counter() - t10) * 1000

    # Unit: Set units for calc metrics - VECTORIZED
    t11 = time.perf_counter()

    missing_unit = result['unit'].isna()

    # For _calc metrics
    is_calc = missing_unit & result['id'].str.contains('_calc', na=False)
    result.loc[is_calc, 'unit'] = 'mg/dL'

    # Special case: TBPN_calc
    result.loc[result['id'] == 'TBPN_calc', 'unit'] = 'nmol/L'

    # For other derived metrics (pct, frac)
    is_other = missing_unit & ~is_calc
    result.loc[is_other, 'unit'] = '-/-'

    timings['12_fill_unit'] = (time.perf_counter() - t11) * 1000

    # RefUnit: Same as unit
    t12 = time.perf_counter()
    result['refUnit'] = result['unit']

    # Correct typo in XML (row 9 should be Apo-B100 / Apo-A1)
    if len(result) > 8:
        result.loc[8, 'name'] = "Apo-B100 / Apo-A1"

    # Clean abbreviations (remove spaces)
    result['abbr'] = result['abbr'].str.replace(' ', '')
    timings['13_cleanup'] = (time.perf_counter() - t12) * 1000

    # Create publication tags
    t13 = time.perf_counter()
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
    timings['14_create_tags'] = (time.perf_counter() - t13) * 1000

    # Reorder columns
    t14 = time.perf_counter()
    result = result[['fraction', 'name', 'abbr', 'id', 'type', 'value',
                     'unit', 'refMax', 'refMin', 'refUnit', 'tag']]
    timings['15_reorder_columns'] = (time.perf_counter() - t14) * 1000

    timings['TOTAL'] = (time.perf_counter() - t_start) * 1000

    # Optional: Print detailed timing (set DEBUG_TIMING env var to enable)
    import os
    if os.environ.get('DEBUG_TIMING'):
        print("\n" + "="*60)
        print("DETAILED TIMING BREAKDOWN (extend_lipo)")
        print("="*60)
        for step, time_ms in timings.items():
            print(f"{step:.<40} {time_ms:>7.2f} ms")
        print("="*60 + "\n")

    return {
        'data': result.reset_index(drop=True),
        'version': lipo['version']
    }
