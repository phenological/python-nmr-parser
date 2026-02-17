#!/usr/bin/env python3
"""
Example: Reading lipoprotein profile data

This script demonstrates how to read lipoprotein XML files and extend
them with calculated metrics (percentages, fractions).

Usage:
    python read_lipo_example.py [xml_file]

Example:
    python read_lipo_example.py /path/to/lipo_results.xml
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nmr_parser import read_lipo
from nmr_parser.processing import extend_lipo, extend_lipo_value


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Read and analyze lipoprotein profile data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python read_lipo_example.py lipo_results.xml
  python read_lipo_example.py  # Uses default test data
        """
    )
    parser.add_argument(
        'xml_file',
        nargs='?',
        type=str,
        help='Path to lipoprotein XML file (default: uses test data)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output CSV file to save lipoprotein data'
    )
    parser.add_argument(
        '--show-all',
        action='store_true',
        help='Display all measurements (not just first 10)'
    )

    args = parser.parse_args()

    # Determine file path
    if args.xml_file:
        lipo_file = Path(args.xml_file)
        print(f"Reading: {lipo_file}\n")
    else:
        # Default to sample data from package
        from nmr_parser.reference.tables import DATA_DIR
        lipo_file = DATA_DIR / "lipo_results.xml"
        print(f"No file provided, using sample data: {lipo_file}\n")

    if not lipo_file.exists():
        print(f"Error: File not found: {lipo_file}")
        sys.exit(1)

    print("=" * 60)
    print("Reading Lipoprotein Profile Data")
    print("=" * 60)

    # Example 1: Read basic lipoprotein data
    print("\n1. Read Basic Lipoprotein Data:")
    print("-" * 40)
    lipo = read_lipo(lipo_file)
    if lipo:
        print(f"Version: {lipo['version']}")
        print(f"Measurements: {len(lipo['data'])}")
        print(f"\nColumns: {list(lipo['data'].columns)}")

        if args.show_all:
            print("\nAll measurements:")
            print(lipo['data'][['id', 'value', 'unit']].to_string())
        else:
            print("\nFirst 10 measurements:")
            print(lipo['data'][['id', 'value', 'unit']].head(10))
            print("\nUse --show-all to see all data or -o to export to CSV")

    # Example 2: Access specific lipoprotein fractions
    print("\n2. Access Specific Lipoprotein Fractions:")
    print("-" * 40)
    if lipo:
        data = lipo['data']

        # Total cholesterol in major fractions
        fractions = ['HDCH', 'LDCH', 'VLCH']  # HDL, LDL, VLDL cholesterol
        print("\nCholesterol by fraction:")
        for frac in fractions:
            row = data[data['id'] == frac]
            if not row.empty:
                value = row.iloc[0]['value']
                unit = row.iloc[0]['unit']
                print(f"  {frac}: {value} {unit}")

    # Example 3: Extend with calculated metrics
    print("\n3. Extend with Calculated Metrics:")
    print("-" * 40)
    if lipo:
        # Extend with calculated values only
        extended_values = extend_lipo_value(lipo)
        print(f"Original columns: {len(lipo['data'].columns)}")
        print(f"Extended columns: {len(extended_values.columns)}")
        print(f"\nNew calculated metrics (first 10):")
        calc_cols = [col for col in extended_values.columns if '_calc' in col]
        print(calc_cols[:10])

    # Example 4: Full extension with reference ranges
    print("\n4. Full Extension with Reference Ranges:")
    print("-" * 40)
    if lipo:
        extended = extend_lipo(lipo)
        print(f"Original rows: {len(lipo['data'])}")
        print(f"Extended rows: {len(extended['data'])}")
        print(f"\nColumns: {list(extended['data'].columns)}")

        # Show metrics with reference ranges
        print("\nSample metrics with reference ranges:")
        sample_data = extended['data'].head(5)
        print(sample_data[['id', 'value', 'unit', 'refMin', 'refMax']])

    # Example 5: Calculate lipoprotein ratios
    print("\n5. Calculate Lipoprotein Ratios:")
    print("-" * 40)
    if lipo:
        data = lipo['data']

        # Calculate common clinical ratios
        def get_value(df, id_name):
            row = df[df['id'] == id_name]
            return row.iloc[0]['value'] if not row.empty else None

        hdch = get_value(data, 'HDCH')
        ldch = get_value(data, 'LDCH')
        total_ch = get_value(data, 'TPCH')

        if hdch and ldch and total_ch:
            ldl_hdl_ratio = ldch / hdch
            hdl_total_ratio = hdch / total_ch

            print(f"  LDL/HDL ratio: {ldl_hdl_ratio:.2f}")
            print(f"  HDL/Total ratio: {hdl_total_ratio:.2f}")
            print(f"\n  Clinical interpretation:")
            print(f"    LDL/HDL < 3.0: Desirable")
            print(f"    Your ratio: {ldl_hdl_ratio:.2f} - {'✓ Good' if ldl_hdl_ratio < 3.0 else '⚠ Elevated'}")

    # Export to CSV if requested
    if args.output:
        print(f"\n{'=' * 60}")
        print("Exporting Data")
        print("=" * 60)

        if lipo:
            extended = extend_lipo(lipo)
            output_path = Path(args.output)
            extended['data'].to_csv(output_path, index=False)
            print(f"✓ Exported {len(extended['data'])} lipoprotein measurements to: {output_path}")
            print(f"  Columns: {list(extended['data'].columns)}")
            print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
