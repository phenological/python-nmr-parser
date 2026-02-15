#!/usr/bin/env python3
"""
Example: Reading complete NMR experiment folders

This script demonstrates how to use read_experiment() to read all data
from a Bruker NMR experiment folder in one go.

Usage:
    python read_experiment_example.py [experiment_path] [experiment_path2...]

Example:
    python read_experiment_example.py /path/to/experiment/10
    python read_experiment_example.py /path/exp1/10 /path/exp2/10  # Multiple
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nmr_parser import read_experiment


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Read complete NMR experiment folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python read_experiment_example.py /path/to/experiment/10
  python read_experiment_example.py exp1/10 exp2/10  # Multiple experiments
  python read_experiment_example.py  # Uses default test data
        """
    )
    parser.add_argument(
        'experiment_paths',
        nargs='*',
        type=str,
        help='Path(s) to experiment folder(s) (default: uses test data)'
    )

    args = parser.parse_args()

    # Determine experiment paths
    if args.experiment_paths:
        exp_paths = [Path(p) for p in args.experiment_paths]
        for path in exp_paths:
            if not path.exists():
                print(f"Error: Experiment path not found: {path}")
                sys.exit(1)
        exp_path = exp_paths[0]  # Use first for single examples
        print(f"Reading: {', '.join(str(p) for p in exp_paths)}\n")
    else:
        # Default to test data
        test_data = Path(__file__).parent.parent / "tests" / "data"
        exp_path = test_data / "HB-COVID0001" / "10"
        exp_paths = [exp_path]
        print(f"No path provided, using test data: {exp_path}\n")

    if not exp_path.exists():
        print(f"Error: Experiment path not found: {exp_path}")
        sys.exit(1)

    print("=" * 60)
    print("Reading Complete NMR Experiment")
    print("=" * 60)

    # Example 1: Read everything
    print("\n1. Read All Data Types:")
    print("-" * 40)
    print(f"Reading from: {exp_path}")

    exp = read_experiment(exp_path)

    print(f"\nAvailable data types: {list(exp.keys())}")
    for key in exp.keys():
        if exp[key] is not None:
            print(f"  ✓ {key}")

    # Example 2: Access acquisition parameters
    print("\n2. Access Acquisition Parameters:")
    print("-" * 40)
    if 'acqus' in exp and exp['acqus'] is not None:
        acqus = exp['acqus']
        print(f"Shape: {acqus.shape}")
        print("\nKey parameters:")
        key_params = ['PULPROG', 'NS', 'SW', 'O1', 'TE']
        for param in key_params:
            col = f'acqus.{param}'
            if col in acqus.columns:
                print(f"  {param}: {acqus[col].iloc[0]}")

    # Example 3: Access spectrum data
    print("\n3. Access Spectrum Data:")
    print("-" * 40)
    if 'spec' in exp and exp['spec'] is not None:
        spec_info = exp['spec']
        if 'spec' in spec_info:
            # Get the SpectrumResult from the list in the first row
            spec_result = spec_info['spec'].iloc[0][0]
            # Access the DataFrame from the SpectrumResult
            spec_df = spec_result.spec
            print(f"Number of points: {len(spec_df['x'])}")
            print(f"PPM range: {spec_df['x'].min():.2f} to {spec_df['x'].max():.2f}")
            print(f"Intensity range: {spec_df['y'].min():.2e} to {spec_df['y'].max():.2e}")

    # Example 4: Access quantification data
    print("\n4. Access Quantification Data:")
    print("-" * 40)
    if 'quant' in exp and exp['quant'] is not None and not exp['quant'].empty:
        quant = exp['quant']
        # Quant is in wide format with columns like 'value.{metabolite_name}'
        value_cols = [col for col in quant.columns if col.startswith('value.')]
        print(f"Metabolites quantified: {len(value_cols)}")
        if value_cols:
            print(f"\nFirst 5 metabolites and their values:")
            for col in value_cols[:5]:
                metabolite_name = col.replace('value.', '')
                value = quant[col].iloc[0]
                print(f"  {metabolite_name}: {value}")

    # Example 5: Read with selective options
    print("\n5. Read Only Specific Components:")
    print("-" * 40)
    opts = {
        "what": ["acqus", "procs", "spec"]
    }
    exp_subset = read_experiment(exp_path, opts=opts)
    print(f"Requested: {opts['what']}")
    print(f"Available: {list(exp_subset.keys())}")

    # Example 6: Read spectrum with custom options
    print("\n6. Read Spectrum with Custom Options:")
    print("-" * 40)
    opts = {
        "what": ["spec"],
        "specOpts": {
            "fromTo": (-0.5, 10.0),     # PPM range
            "length_out": 32768,         # Number of points
            "uncalibrate": False         # Keep calibration
        }
    }
    exp_custom = read_experiment(exp_path, opts=opts)
    if 'spec' in exp_custom and exp_custom['spec'] is not None and not exp_custom['spec'].empty:
        # Get the SpectrumResult from the list in the first row
        spec_result = exp_custom['spec']['spec'].iloc[0][0]
        # Access the DataFrame from the SpectrumResult
        spec_df = spec_result.spec
        print(f"Custom PPM range: {spec_df['x'].min():.2f} to {spec_df['x'].max():.2f}")
        print(f"Number of points: {len(spec_df['x'])}")

    # Example 7: Read multiple experiments
    print("\n7. Read Multiple Experiments:")
    print("-" * 40)

    # Use command-line paths if multiple provided, otherwise use test data
    if len(exp_paths) > 1:
        multi_exp_paths = exp_paths
    elif not args.experiment_paths:
        # Default: try to find multiple test experiments
        multi_exp_paths = [
            test_data / "HB-COVID0001" / "10",
            test_data / "HB-COVID0001" / "11",
        ]
        multi_exp_paths = [p for p in multi_exp_paths if p.exists()]
    else:
        multi_exp_paths = exp_paths

    if len(multi_exp_paths) > 1:
        print(f"Reading {len(multi_exp_paths)} experiments...")
        multi_exp = read_experiment(multi_exp_paths)
        print(f"Available data types: {list(multi_exp.keys())}")

        if 'acqus' in multi_exp and multi_exp['acqus'] is not None:
            print(f"\nAcquisition parameters shape: {multi_exp['acqus'].shape}")
            print(f"Experiments: {len(multi_exp['acqus'])}")

    # Example 8: Create experiment summary
    print("\n8. Create Experiment Summary:")
    print("-" * 40)
    exp = read_experiment(exp_path)

    summary = {
        'path': str(exp_path),
        'components': len([k for k in exp.keys() if exp[k] is not None]),
    }

    if 'acqus' in exp and exp['acqus'] is not None:
        acqus = exp['acqus']
        summary['pulse_program'] = acqus.get('acqus.PULPROG', ['N/A']).iloc[0]
        summary['num_scans'] = acqus.get('acqus.NS', ['N/A']).iloc[0]

    if 'quant' in exp and exp['quant'] is not None and not exp['quant'].empty:
        # Count columns that start with 'value.' to get number of metabolites
        value_cols = [col for col in exp['quant'].columns if col.startswith('value.')]
        summary['metabolites'] = len(value_cols)

    print("\nExperiment Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
