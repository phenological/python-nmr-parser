#!/usr/bin/env python3
"""
Example: Reading Bruker parameter files (acqus/procs)

This script demonstrates how to read acquisition and processing parameters
from Bruker NMR experiment folders.

Usage:
    python read_params_example.py [experiment_path]

Example:
    python read_params_example.py /path/to/experiment/10
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nmr_parser import read_param, read_params


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Read and display Bruker parameter files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python read_params_example.py /path/to/experiment/10
  python read_params_example.py  # Uses default test data
        """
    )
    parser.add_argument(
        'experiment_path',
        nargs='?',
        type=str,
        help='Path to experiment folder (default: uses test data)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output CSV file to save all parameters'
    )
    parser.add_argument(
        '--show-all',
        action='store_true',
        help='Display all parameters (not just first 5)'
    )

    args = parser.parse_args()

    # Determine experiment path
    if args.experiment_path:
        exp_path = Path(args.experiment_path)
    else:
        # Default to test data
        test_data = Path(__file__).parent.parent / "tests" / "data"
        exp_path = test_data / "HB-COVID0001" / "10"
        print(f"No path provided, using test data: {exp_path}\n")

    if not exp_path.exists():
        print(f"Error: Experiment path not found: {exp_path}")
        print("\nUsage: python read_params_example.py [experiment_path]")
        sys.exit(1)

    acqus_file = exp_path / "acqus"
    procs_file = exp_path / "pdata" / "1" / "procs"

    print("=" * 60)
    print("Reading Bruker Parameter Files")
    print("=" * 60)

    # Example 1: Read a single parameter
    print("\n1. Read single parameter:")
    print("-" * 40)
    if acqus_file.exists():
        pulprog = read_param(acqus_file, "PULPROG")
        print(f"PULPROG: {pulprog}")

        ns = read_param(acqus_file, "NS")
        print(f"Number of scans (NS): {ns}")

        d1 = read_param(acqus_file, "D 1")
        print(f"Relaxation delay (D1): {d1} seconds")

    # Example 2: Read multiple specific parameters
    print("\n2. Read multiple parameters:")
    print("-" * 40)
    if acqus_file.exists():
        params = read_param(acqus_file, ["PULPROG", "NS", "SW", "O1"])
        print(params)

    # Example 3: Read all acquisition parameters
    print("\n3. Read all acquisition parameters:")
    print("-" * 40)
    if acqus_file.exists():
        all_acqus = read_params(acqus_file)
        print(f"Total parameters: {len(all_acqus)}")

        if args.show_all:
            print("\nAll parameters:")
            print(all_acqus.to_string())
        else:
            print("\nFirst 5 parameters:")
            print(all_acqus.head())
            print("\nParameter names available:")
            print(sorted(all_acqus['name'].unique())[:10], "...")
            print("\nUse --show-all to see all parameters or -o to export to CSV")

    # Example 4: Read processing parameters
    print("\n4. Read processing parameters:")
    print("-" * 40)
    if procs_file.exists():
        all_procs = read_params(procs_file)
        print(f"Total parameters: {len(all_procs)}")
        print("\nProcessing info:")
        print(all_procs[all_procs['name'].isin(['OFFSET', 'SF', 'SI', 'WDW'])][['name', 'value']])

    # Example 5: Practical use - Extract experiment metadata
    print("\n5. Extract experiment metadata:")
    print("-" * 40)
    if acqus_file.exists():
        metadata = {
            'pulse_program': read_param(acqus_file, "PULPROG"),
            'num_scans': read_param(acqus_file, "NS"),
            'spectral_width': read_param(acqus_file, "SW"),
            'receiver_gain': read_param(acqus_file, "RG"),
            'temperature': read_param(acqus_file, "TE"),
        }
        print("Experiment Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

    # Export to CSV if requested
    if args.output:
        print(f"\n{'=' * 60}")
        print("Exporting Data")
        print("=" * 60)

        if acqus_file.exists():
            all_acqus = read_params(acqus_file)
            output_path = Path(args.output)
            all_acqus.to_csv(output_path, index=False)
            print(f"✓ Exported {len(all_acqus)} parameters to: {output_path}")
            print(f"  Columns: {list(all_acqus.columns)}")
            print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
