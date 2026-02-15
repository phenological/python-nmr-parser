#!/usr/bin/env python3
"""
Example: Scanning folders for Bruker experiments

This script demonstrates how to use scan_folder() to find and filter
NMR experiment folders within a directory tree.

Usage:
    python scan_folder_example.py [folder_path]

Example:
    python scan_folder_example.py /path/to/data/folder
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nmr_parser import scan_folder


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Scan folders for Bruker NMR experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan_folder_example.py /path/to/data/
  python scan_folder_example.py  # Uses default test data
        """
    )
    parser.add_argument(
        'folder_path',
        nargs='?',
        type=str,
        help='Path to folder to scan (default: uses test data)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output CSV file to save experiment list'
    )

    args = parser.parse_args()

    # Determine folder path
    if args.folder_path:
        test_data = Path(args.folder_path)
        print(f"Scanning: {test_data}\n")
    else:
        # Default to test data
        test_data = Path(__file__).parent.parent / "tests" / "data"
        print(f"No path provided, using test data: {test_data}\n")

    if not test_data.exists():
        print(f"Error: Folder not found: {test_data}")
        sys.exit(1)

    print("=" * 60)
    print("Scanning Folders for Bruker Experiments")
    print("=" * 60)

    # Example 1: Scan with automatic detection (no filters)
    print("\n1. Scan All Experiments (Non-Interactive):")
    print("-" * 40)
    print(f"Scanning: {test_data}\n")

    # Use EXP="all" to skip interactive prompt and get all experiments
    all_experiments = scan_folder(test_data, options={"EXP": "all"})

    if len(all_experiments) > 0:
        print(f"\nFound {len(all_experiments)} experiments")
        print("\nExperiment details:")
        print(all_experiments[['file', 'EXP', 'PULPROG']].to_string())

        # Show unique experiment types
        print("\nUnique experiment types:")
        exp_types = all_experiments['EXP'].value_counts()
        for exp_type, count in exp_types.items():
            print(f"  {exp_type}: {count}")

        print("\nUnique pulse programs:")
        pulprogs = all_experiments['PULPROG'].value_counts()
        for pulprog, count in pulprogs.items():
            print(f"  {pulprog}: {count}")

    # Example 2: Filter by specific experiment type
    print("\n2. Filter by Experiment Type:")
    print("-" * 40)

    # Use the already-scanned results from Example 1 (much more efficient!)
    if len(all_experiments) > 0:
        # Get the most common experiment types from the actual data
        exp_types = all_experiments['EXP'].value_counts()

        if len(exp_types) > 0:
            # Use the most common experiment type as an example
            most_common_exp = exp_types.index[0]
            filtered = all_experiments[all_experiments['EXP'] == most_common_exp]

            print(f"\nExample: Filtering for '{most_common_exp}'")
            print(f"Found {len(filtered)} experiments")
            print(filtered[['file', 'EXP']].head(3))

            print(f"\nAll experiment types in your data:")
            for exp_type, count in exp_types.head(10).items():
                print(f"  '{exp_type}': {count} experiments")
        else:
            print("\nNo experiment types found (EXP parameter not set)")
    else:
        print("\nNo experiments found")

    # Example 3: Filter by pulse program
    print("\n3. Filter by Pulse Program:")
    print("-" * 40)

    # Use the already-scanned results (efficient!)
    if len(all_experiments) > 0:
        # Get the most common pulse programs from the actual data
        pulprogs = all_experiments['PULPROG'].value_counts()

        if len(pulprogs) > 0:
            # Use the most common pulse program as an example
            most_common_pulprog = pulprogs.index[0]
            filtered = all_experiments[all_experiments['PULPROG'] == most_common_pulprog]

            print(f"\nExample: Filtering for PULPROG '{most_common_pulprog}'")
            print(f"Found {len(filtered)} experiments")
            print(filtered[['file', 'PULPROG']].head(3))

            print(f"\nAll pulse programs in your data:")
            for pulprog, count in pulprogs.head(10).items():
                print(f"  '{pulprog}': {count} experiments")
        else:
            print("\nNo pulse programs found (PULPROG parameter not set)")
    else:
        print("\nNo experiments found")

    # Example 4: Filter by both EXP and PULPROG
    print("\n4. Filter by Both EXP and PULPROG:")
    print("-" * 40)

    # Use the already-scanned results (efficient!)
    if len(all_experiments) > 0:
        # Try to find a combination that exists in the data
        exp_pulprog_combos = all_experiments.groupby(['EXP', 'PULPROG']).size().reset_index(name='count')
        exp_pulprog_combos = exp_pulprog_combos.sort_values('count', ascending=False)

        if len(exp_pulprog_combos) > 0:
            # Use the most common combination
            example_exp = exp_pulprog_combos.iloc[0]['EXP']
            example_pulprog = exp_pulprog_combos.iloc[0]['PULPROG']

            filtered = all_experiments[
                (all_experiments['EXP'] == example_exp) &
                (all_experiments['PULPROG'] == example_pulprog)
            ]

            print(f"\nExample: Filtering for EXP='{example_exp}' AND PULPROG='{example_pulprog}'")
            print(f"Found {len(filtered)} experiments")
            print(filtered[['file', 'EXP', 'PULPROG']].head(3))
        else:
            print("\nNo valid EXP/PULPROG combinations found")
    else:
        print("\nNo experiments found")

    # Example 5: Get experiment paths for batch processing
    print("\n5. Use Results for Batch Processing:")
    print("-" * 40)

    all_experiments = scan_folder(test_data, options={"EXP": "all"})

    if len(all_experiments) > 0:
        # Extract paths as list
        experiment_paths = [Path(p) for p in all_experiments['file'].tolist()]

        print(f"\nExtracted {len(experiment_paths)} experiment paths")
        print("\nThese paths can be used with read_experiment():")
        print("\nExample code:")
        print("  from nmr_parser import read_experiment")
        print("  for exp_path in experiment_paths:")
        print("      exp_data = read_experiment(exp_path)")
        print("      # Process exp_data...")

        # Show first few paths
        print(f"\nFirst {min(3, len(experiment_paths))} paths:")
        for i, path in enumerate(experiment_paths[:3], 1):
            print(f"  {i}. {path}")

    # Example 6: Check USERA2 parameter
    print("\n6. Access Additional Parameters (USERA2):")
    print("-" * 40)

    all_experiments = scan_folder(test_data, options={"EXP": "all"})

    if len(all_experiments) > 0 and 'USERA2' in all_experiments.columns:
        # Filter experiments with USERA2 set
        with_usera2 = all_experiments[all_experiments['USERA2'] != '']

        if len(with_usera2) > 0:
            print(f"\nFound {len(with_usera2)} experiments with USERA2 parameter set")
            print(with_usera2[['file', 'USERA2']].head())
        else:
            print("\nNo experiments have USERA2 parameter set")

    # Export to CSV if requested
    if args.output:
        print(f"\n{'=' * 60}")
        print("Exporting Data")
        print("=" * 60)

        all_experiments = scan_folder(test_data, options={"EXP": "all"})

        if len(all_experiments) > 0:
            output_path = Path(args.output)
            all_experiments.to_csv(output_path, index=False)
            print(f"✓ Exported {len(all_experiments)} experiments to: {output_path}")
            print(f"  Columns: {list(all_experiments.columns)}")
            print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")

    # Example 8: Scan multiple folders
    print("\n8. Scan Multiple Folders:")
    print("-" * 40)

    # Try to find multiple folders to scan
    # If test_data has subdirectories that look like samples, use those
    # Otherwise, look for subfolders at the test_data level
    if (test_data / "HB-COVID0001").exists():
        # We're at the test data root level
        folders_to_scan = [
            test_data / "HB-COVID0001",
            test_data / "EXTERNAL-comet-nmr-urine-R20",
        ]
        # Filter to existing folders
        existing_folders = [f for f in folders_to_scan if f.exists()]
    else:
        # We might be inside a specific sample folder
        # Look for experiment subfolders (those with acqus files)
        all_subfolders = [f for f in test_data.iterdir() if f.is_dir()]
        existing_folders = [f for f in all_subfolders if (f / "acqus").exists()]
        # Sort and limit to first few for demonstration
        existing_folders = sorted(existing_folders)[:3]

    if len(existing_folders) > 1:
        print(f"\nScanning {len(existing_folders)} folders:")
        for folder in existing_folders:
            print(f"  - {folder.name}")

        # Note: scan_folder takes single folder, so scan each separately
        all_results = []
        for folder in existing_folders:
            result = scan_folder(folder, options={"EXP": "all"})
            if len(result) > 0:
                all_results.append(result)

        # Combine results
        if all_results:
            import pandas as pd
            combined = pd.concat(all_results, ignore_index=True)
            print(f"\nTotal experiments found: {len(combined)}")
        else:
            print("\nNo experiments found in scanned folders")
    else:
        print("\nNot enough folders available for this example")
        print("Tip: Run with the test data root directory or a folder with multiple experiments")

    print("\n" + "=" * 60)
    print("Tip: Remove EXP and PULPROG options for interactive mode")
    print("     (presents a menu to choose experiment type)")
    print("=" * 60)


if __name__ == "__main__":
    main()
