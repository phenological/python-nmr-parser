#!/usr/bin/env python3
"""
Example: Reading quantification XML files

This script demonstrates how to read quantification data from Bruker IVDr
XML files. The parser automatically handles multiple schema versions.

Usage:
    python read_quant_example.py [xml_file]

Example:
    python read_quant_example.py /path/to/plasma_quant_report.xml
"""

import sys
import argparse
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nmr_parser import read_quant


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Read and display quantification XML data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python read_quant_example.py plasma_quant_report.xml
  python read_quant_example.py  # Uses default test data
        """
    )
    parser.add_argument(
        'xml_file',
        nargs='?',
        type=str,
        help='Path to quantification XML file (default: uses test data)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output CSV file to save quantification data'
    )
    parser.add_argument(
        '--show-all',
        action='store_true',
        help='Display all metabolites (not just first 5)'
    )

    args = parser.parse_args()

    # Determine XML file path
    if args.xml_file:
        xml_file = Path(args.xml_file)
        if not xml_file.exists():
            print(f"Error: File not found: {xml_file}")
            sys.exit(1)

        # Use the provided file
        plasma_files = [xml_file]
        urine_files = []
        print(f"Reading: {xml_file}\n")
    else:
        # Default to test data
        test_data = Path(__file__).parent.parent / "tests" / "data"
        plasma_files = [
            test_data / "plasma_quant_report.xml",
            test_data / "plasma_quant_report_2_1_0.xml",
        ]
        urine_files = [
            test_data / "urine_quant_report_b.xml",
            test_data / "urine_quant_report_e.xml",
        ]
        print(f"No file provided, using test data\n")

    print("=" * 60)
    print("Reading Quantification XML Files")
    print("=" * 60)

    # Example 1: Read plasma quantification
    print("\n1. Plasma Quantification:")
    print("-" * 40)
    for xml_file in plasma_files:
        if xml_file.exists():
            print(f"\nReading: {xml_file.name}")
            quant = read_quant(xml_file)

            if quant:
                print(f"  Version: {quant['version']}")
                print(f"  Metabolites: {len(quant['data'])}")
                print(f"  Columns: {list(quant['data'].columns)}")

                if args.show_all:
                    print("\n  All metabolites:")
                    print(quant['data'][['name', 'conc_v', 'concUnit_v']].to_string())
                else:
                    print("\n  First 5 metabolites:")
                    print(quant['data'][['name', 'conc_v', 'concUnit_v']].head())
                    print("\n  Use --show-all to see all data or -o to export to CSV")

                # Store for export if needed
                quant_for_export = quant
                break

    # Example 2: Read urine quantification
    print("\n2. Urine Quantification:")
    print("-" * 40)
    for xml_file in urine_files:
        if xml_file.exists():
            print(f"\nReading: {xml_file.name}")
            quant = read_quant(xml_file)

            if quant:
                print(f"  Version: {quant['version']}")
                print(f"  Metabolites: {len(quant['data'])}")
                print("\n  First 5 metabolites:")
                print(quant['data'][['name', 'conc_v', 'concUnit_v']].head())
                break

    # Example 3: Access specific metabolites
    print("\n3. Access Specific Metabolites:")
    print("-" * 40)
    for xml_file in plasma_files:
        if xml_file.exists():
            quant = read_quant(xml_file)
            if quant:
                data = quant['data']

                # Get specific metabolites
                target_metabolites = ['Glucose', 'Lactate', 'Alanine']
                for met in target_metabolites:
                    row = data[data['name'] == met]
                    if not row.empty:
                        conc = row.iloc[0]['conc_v']
                        unit = row.iloc[0]['concUnit_v']
                        print(f"  {met}: {conc} {unit}")
                break

    # Example 4: Filter by conc_v range
    print("\n4. Filter High Concentration Metabolites:")
    print("-" * 40)
    for xml_file in plasma_files:
        if xml_file.exists():
            quant = read_quant(xml_file)
            if quant:
                data = quant['data'].copy()

                # Convert conc_v to numeric for comparison
                data['conc_v'] = pd.to_numeric(data['conc_v'], errors='coerce')

                # Find metabolites with conc_v > 1 mmol/L
                high_conc = data[data['conc_v'] > 1.0]
                print(f"  Found {len(high_conc)} metabolites > 1.0 mmol/L")
                print("\n  Top 5:")
                print(high_conc.nlargest(5, 'conc_v')[['name', 'conc_v', 'concUnit_v']])
                break

    # Export to CSV if requested
    if args.output:
        print(f"\n{'=' * 60}")
        print("Exporting Data")
        print("=" * 60)

        # Find the first available file and export it
        for xml_file in plasma_files + urine_files:
            if xml_file.exists():
                quant = read_quant(xml_file)
                if quant:
                    output_path = Path(args.output)
                    quant['data'].to_csv(output_path, index=False)
                    print(f"✓ Exported {len(quant['data'])} metabolites to: {output_path}")
                    print(f"  Columns: {list(quant['data'].columns)}")
                    print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")
                    break
                break


if __name__ == "__main__":
    main()
