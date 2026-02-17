#!/usr/bin/env python3
"""
Example: Reading PACS (Phenotypic Assessment and Clinical Screening) data

This script demonstrates how to read PACS XML files, access reference ranges,
and validate measurements against clinical thresholds.

Usage:
    python read_pacs_example.py [xml_file]

Example:
    python read_pacs_example.py /path/to/plasma_pacs_report.xml
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nmr_parser import read_pacs, get_pacs_table


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Read and analyze PACS data with reference ranges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python read_pacs_example.py plasma_pacs_report.xml
  python read_pacs_example.py  # Uses default test data
        """
    )
    parser.add_argument(
        'xml_file',
        nargs='?',
        type=str,
        help='Path to PACS XML file (default: uses test data)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output CSV file to save PACS data'
    )
    parser.add_argument(
        '--show-all',
        action='store_true',
        help='Display all parameters (not just summary)'
    )
    parser.add_argument(
        '--reference',
        action='store_true',
        help='Display reference table only'
    )

    args = parser.parse_args()

    # Example 0: Show reference table only
    if args.reference:
        print("=" * 70)
        print("PACS Reference Table")
        print("=" * 70)
        ref_table = get_pacs_table()
        print(f"\nTotal parameters: {len(ref_table)}")
        print("\nReference ranges for all PACS parameters:")
        print(ref_table.to_string(index=False))
        return

    # Determine file path
    if args.xml_file:
        pacs_file = Path(args.xml_file)
        print(f"Reading: {pacs_file}\n")
    else:
        # Default to test data
        test_data = Path(__file__).parent.parent / "tests" / "data"
        pacs_file = test_data / "plasma_pacs_report.xml"
        print(f"No file provided, using test data: {pacs_file}\n")

    if not pacs_file.exists():
        print(f"Error: File not found: {pacs_file}")
        sys.exit(1)

    print("=" * 70)
    print("Reading PACS Data")
    print("=" * 70)

    # Example 1: Read basic PACS data
    print("\n1. Read Basic PACS Data:")
    print("-" * 50)
    pacs = read_pacs(pacs_file)
    if pacs:
        print(f"Version: {pacs['version']}")
        print(f"Parameters: {len(pacs['data'])}")
        print(f"\nColumns: {list(pacs['data'].columns)}")

        if args.show_all:
            print("\nAll parameters:")
            print(pacs['data'].to_string(index=False))
        else:
            print("\nFirst 5 parameters:")
            print(pacs['data'].head(5).to_string(index=False))
            print("\nUse --show-all to see all data or -o to export to CSV")

    # Example 2: Get reference table
    print("\n2. PACS Reference Table:")
    print("-" * 50)
    ref_table = get_pacs_table()
    print(f"Reference parameters: {len(ref_table)}")
    print("\nParameter categories:")
    print("  • Clinical chemistry: Glucose, Creatinine")
    print("  • Lipoproteins: TG, Chol, LDL-Chol, HDL-Chol, LDL-Phos, HDL-Phos")
    print("  • Apolipoproteins: Apo-A1, Apo-B100, Apo-B100/Apo-A1")
    print("  • Glycoproteins: GlycA, GlycB, Glyc, SPC, Glyc/SPC")

    print("\nSample reference ranges:")
    print(ref_table[['name', 'unit', 'refMin', 'refMax']].head(5).to_string(index=False))

    # Example 3: Compare measurements with reference ranges
    print("\n3. Validate Against Reference Ranges:")
    print("-" * 50)
    if pacs:
        import pandas as pd

        # Merge actual data with reference ranges
        data = pacs['data'].copy()
        data.columns = ['name', 'conc', 'unit', 'refMax', 'refMin', 'refUnit']

        # Convert to numeric for comparison
        data['conc_num'] = pd.to_numeric(data['conc'], errors='coerce')
        data['refMin_num'] = pd.to_numeric(data['refMin'], errors='coerce')
        data['refMax_num'] = pd.to_numeric(data['refMax'], errors='coerce')

        # Check if values are within range
        data['in_range'] = (
            (data['conc_num'] >= data['refMin_num']) &
            (data['conc_num'] <= data['refMax_num'])
        )
        data['status'] = data['in_range'].map({True: '✓ Normal', False: '⚠ Out of range'})

        print("\nValidation results:")
        validation = data[['name', 'conc', 'unit', 'refMin', 'refMax', 'status']]

        if args.show_all:
            print(validation.to_string(index=False))
        else:
            print(validation.head(8).to_string(index=False))

        # Summary
        in_range_count = data['in_range'].sum()
        total_count = len(data)
        print(f"\nSummary: {in_range_count}/{total_count} parameters within normal range")

        # Show out-of-range parameters
        out_of_range = data[~data['in_range']]
        if not out_of_range.empty:
            print("\n⚠ Parameters outside reference range:")
            for _, row in out_of_range.iterrows():
                print(f"  • {row['name']}: {row['conc']} {row['unit']} (ref: {row['refMin']}-{row['refMax']})")
        else:
            print("\n✓ All parameters within normal reference ranges")

    # Example 4: Clinical lipid panel
    print("\n4. Clinical Lipid Panel:")
    print("-" * 50)
    if pacs:
        lipid_params = ['TG', 'Chol', 'LDL-Chol', 'HDL-Chol', 'Apo-A1', 'Apo-B100']
        lipid_data = data[data['name'].isin(lipid_params)]

        print("\nLipid profile:")
        print(lipid_data[['name', 'conc', 'unit', 'refMin', 'refMax', 'status']].to_string(index=False))

        # Calculate additional ratios if data available
        def get_value(df, param_name):
            row = df[df['name'] == param_name]
            return float(row['conc'].iloc[0]) if not row.empty else None

        chol = get_value(data, 'Chol')
        hdl = get_value(data, 'HDL-Chol')
        ldl = get_value(data, 'LDL-Chol')

        if chol and hdl and ldl:
            print("\nCalculated ratios:")
            total_hdl_ratio = chol / hdl
            ldl_hdl_ratio = ldl / hdl
            print(f"  Total Cholesterol/HDL: {total_hdl_ratio:.2f}")
            print(f"  LDL/HDL: {ldl_hdl_ratio:.2f}")
            print("\n  Clinical interpretation:")
            print(f"    Total/HDL < 5.0: Desirable")
            print(f"    Your ratio: {total_hdl_ratio:.2f} - {'✓ Good' if total_hdl_ratio < 5.0 else '⚠ Elevated'}")

    # Example 5: Glycoprotein markers (inflammatory)
    print("\n5. Glycoprotein Inflammatory Markers:")
    print("-" * 50)
    if pacs:
        glyco_params = ['GlycA', 'GlycB', 'Glyc', 'SPC', 'Glyc/SPC']
        glyco_data = data[data['name'].isin(glyco_params)]

        if not glyco_data.empty:
            print("\nInflammatory markers:")
            print(glyco_data[['name', 'conc', 'unit', 'refMin', 'refMax', 'status']].to_string(index=False))
            print("\nNote: GlycA and GlycB are novel inflammatory biomarkers")
        else:
            print("\nNo glycoprotein markers found in this dataset")

    # Example 6: Clinical chemistry basics
    print("\n6. Clinical Chemistry Parameters:")
    print("-" * 50)
    if pacs:
        chem_params = ['Glucose', 'Creatinine']
        chem_data = data[data['name'].isin(chem_params)]

        if not chem_data.empty:
            print("\nBasic chemistry:")
            print(chem_data[['name', 'conc', 'unit', 'refMin', 'refMax', 'status']].to_string(index=False))

    # Export to CSV if requested
    if args.output:
        print(f"\n{'=' * 70}")
        print("Exporting Data")
        print("=" * 70)

        if pacs:
            output_path = Path(args.output)
            # Export validation results
            validation_data = data[['name', 'conc', 'unit', 'refMin', 'refMax', 'refUnit', 'status']]
            validation_data.to_csv(output_path, index=False)
            print(f"✓ Exported {len(validation_data)} PACS parameters to: {output_path}")
            print(f"  Columns: {list(validation_data.columns)}")
            print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
