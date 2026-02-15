#!/usr/bin/env python3
"""
Example: Batch processing multiple NMR experiments

This script demonstrates how to:
- Process multiple experiment folders
- Extract and compile data across samples
- Create summary reports
- Export results to CSV/Excel

Usage:
    python batch_processing_example.py [exp_path1] [exp_path2] ...

Example:
    python batch_processing_example.py exp1/10 exp2/10 exp3/10
    python batch_processing_example.py /path/to/data/*/10
"""

import sys
import argparse
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nmr_parser import read_experiment, read_quant, read_lipo


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Batch process multiple NMR experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_processing_example.py exp1/10 exp2/10 exp3/10
  python batch_processing_example.py /data/sample*/10
  python batch_processing_example.py  # Uses default test data
        """
    )
    parser.add_argument(
        'experiment_paths',
        nargs='*',
        type=str,
        help='Paths to experiment folders (default: uses test data)'
    )

    args = parser.parse_args()

    # Determine experiment folders
    if args.experiment_paths:
        experiment_folders = [Path(p) for p in args.experiment_paths]
        # Filter to existing paths
        experiment_folders = [p for p in experiment_folders if p.exists()]
        if not experiment_folders:
            print("Error: None of the provided paths exist")
            sys.exit(1)
        print(f"Processing {len(experiment_folders)} experiments from command line\n")
    else:
        # Default to test data
        test_data = Path(__file__).parent.parent / "tests" / "data"
        experiment_folders = [
            test_data / "HB-COVID0001" / "10",
            test_data / "HB-COVID0001" / "11",
        ]
        # Filter to existing paths
        experiment_folders = [p for p in experiment_folders if p.exists()]
        if not experiment_folders:
            print(f"Error: Test data not found in: {test_data}")
            sys.exit(1)
        print(f"No paths provided, using test data\n")

    print("=" * 60)
    print("Batch Processing NMR Experiments")
    print("=" * 60)
    print(f"\nFound {len(experiment_folders)} experiments to process")

    # Example 1: Extract acquisition parameters for all samples
    print("\n1. Extract Acquisition Parameters:")
    print("-" * 40)

    acq_params_list = []

    for exp_path in experiment_folders:
        print(f"Processing: {exp_path.name}")

        exp = read_experiment(exp_path, opts={"what": ["acqus"]})

        if 'acqus' in exp and exp['acqus'] is not None:
            acqus = exp['acqus']

            params = {
                'sample': exp_path.parent.name + '/' + exp_path.name,
                'pulse_program': acqus.get('acqus.PULPROG', pd.Series(['N/A'])).iloc[0],
                'num_scans': acqus.get('acqus.NS', pd.Series(['N/A'])).iloc[0],
                'receiver_gain': acqus.get('acqus.RG', pd.Series(['N/A'])).iloc[0],
                'temperature': acqus.get('acqus.TE', pd.Series(['N/A'])).iloc[0],
            }
            acq_params_list.append(params)

    # Create DataFrame
    acq_params_df = pd.DataFrame(acq_params_list)
    print("\nAcquisition Parameters Summary:")
    print(acq_params_df)

    # Example 2: Extract quantification data for all samples
    print("\n2. Extract Quantification Data:")
    print("-" * 40)

    quant_data_list = []

    for exp_path in experiment_folders:
        # Look for quant XML files in pdata/1/
        quant_files = list(exp_path.glob("pdata/1/*quant*.xml"))

        if quant_files:
            # Read the first quant file found
            quant_result = read_quant(quant_files[0])
            if quant_result is not None and 'data' in quant_result:
                quant = quant_result['data'].copy()
                quant['sample'] = exp_path.parent.name + '/' + exp_path.name
                quant_data_list.append(quant)

    if quant_data_list:
        # Combine all quantification data
        all_quant = pd.concat(quant_data_list, ignore_index=True)
        # Convert conc_v to numeric for calculations
        all_quant['conc_v'] = pd.to_numeric(all_quant['conc_v'], errors='coerce')
        print(f"\nTotal measurements: {len(all_quant)}")
        print(f"Samples: {all_quant['sample'].nunique()}")
        print(f"Metabolites: {all_quant['name'].nunique()}")

        # Pivot to wide format (samples as rows, metabolites as columns)
        quant_wide = all_quant.pivot(
            index='sample',
            columns='name',
            values='conc_v'
        )
        print(f"\nQuantification matrix shape: {quant_wide.shape}")
        print(f"(Samples × Metabolites)")

    # Example 3: Calculate summary statistics
    print("\n3. Calculate Summary Statistics:")
    print("-" * 40)

    if quant_data_list:
        # Calculate mean, std, min, max for each metabolite
        stats = all_quant.groupby('name')['conc_v'].agg([
            'count', 'mean', 'std', 'min', 'max'
        ]).round(3)

        print("\nTop 10 metabolites by mean conc_v:")
        print(stats.nlargest(10, 'mean'))

    # Example 4: Compare specific metabolites across samples
    print("\n4. Compare Metabolites Across Samples:")
    print("-" * 40)

    if quant_data_list:
        target_metabolites = ['Glucose', 'Lactate', 'Alanine']

        comparison = all_quant[all_quant['name'].isin(target_metabolites)]
        comparison_wide = comparison.pivot(
            index='name',
            columns='sample',
            values='conc_v'
        )

        if not comparison_wide.empty:
            print("\nMetabolite comparison (mmol/L):")
            print(comparison_wide)

    # Example 5: Extract lipoprotein data
    print("\n5. Extract Lipoprotein Data:")
    print("-" * 40)

    lipo_data_list = []

    for exp_path in experiment_folders:
        # Look for lipo XML files in pdata/1/
        lipo_files = list(exp_path.glob("pdata/1/*lipo*.xml"))

        if lipo_files:
            # Read the first lipo file found
            lipo_result = read_lipo(lipo_files[0])
            if lipo_result is not None and 'data' in lipo_result:
                lipo = lipo_result['data'].copy()
                lipo['sample'] = exp_path.parent.name + '/' + exp_path.name
                lipo_data_list.append(lipo)

    if lipo_data_list:
        all_lipo = pd.concat(lipo_data_list, ignore_index=True)
        # Convert value to numeric for calculations
        all_lipo['value'] = pd.to_numeric(all_lipo['value'], errors='coerce')
        print(f"\nTotal lipoprotein measurements: {len(all_lipo)}")

        # Focus on main fractions
        main_fractions = ['HDCH', 'LDCH', 'VLCH', 'TPCH']
        main_lipo = all_lipo[all_lipo['id'].isin(main_fractions)]

        lipo_wide = main_lipo.pivot(
            index='sample',
            columns='id',
            values='value'
        )
        print("\nMain lipoprotein fractions:")
        print(lipo_wide)

    # Example 6: Export all results
    print("\n6. Export Results:")
    print("-" * 40)

    output_dir = Path("batch_results")
    output_dir.mkdir(exist_ok=True)

    # Export acquisition parameters
    if acq_params_list:
        file_path = output_dir / "acquisition_parameters.csv"
        acq_params_df.to_csv(file_path, index=False)
        print(f"✓ Acquisition parameters: {file_path}")

    # Export quantification data (wide format)
    if quant_data_list:
        file_path = output_dir / "quantification_wide.csv"
        quant_wide.to_csv(file_path)
        print(f"✓ Quantification (wide): {file_path}")

        # Export long format too
        file_path = output_dir / "quantification_long.csv"
        all_quant.to_csv(file_path, index=False)
        print(f"✓ Quantification (long): {file_path}")

        # Export statistics
        file_path = output_dir / "metabolite_statistics.csv"
        stats.to_csv(file_path)
        print(f"✓ Metabolite statistics: {file_path}")

    # Export lipoprotein data
    if lipo_data_list:
        file_path = output_dir / "lipoprotein_fractions.csv"
        lipo_wide.to_csv(file_path)
        print(f"✓ Lipoprotein fractions: {file_path}")

    # Example 7: Create Excel workbook with multiple sheets
    print("\n7. Create Excel Report:")
    print("-" * 40)

    try:
        excel_file = output_dir / "nmr_batch_report.xlsx"

        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            if acq_params_list:
                acq_params_df.to_excel(writer, sheet_name='Acquisition', index=False)

            if quant_data_list:
                quant_wide.to_excel(writer, sheet_name='Quantification')
                stats.to_excel(writer, sheet_name='Statistics')

            if lipo_data_list:
                lipo_wide.to_excel(writer, sheet_name='Lipoproteins')

        print(f"✓ Excel report created: {excel_file}")

    except ImportError:
        print("openpyxl not installed - skipping Excel export")
        print("Install with: pip install openpyxl")

    print(f"\n✓ All results exported to: {output_dir}/")


if __name__ == "__main__":
    main()
