#!/usr/bin/env python3
"""
Example: Reading urine small molecules (brxsm_uri)

Demonstrates reading urine quantification data and comparing with reference ranges.

Usage:
    python read_brxsm_uri_example.py [xml_file]
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nmr_parser import read_quant


def main():
    parser = argparse.ArgumentParser(
        description="Read urine small molecule quantification data"
    )
    parser.add_argument('xml_file', nargs='?', help='Path to urine XML file')
    parser.add_argument('-o', '--output', help='Output CSV file')
    parser.add_argument('--show-all', action='store_true', help='Display all metabolites')

    args = parser.parse_args()

    # Get file path
    if args.xml_file:
        xml_file = Path(args.xml_file)
    else:
        from nmr_parser.reference.tables import DATA_DIR
        xml_file = DATA_DIR / "urine_quant_report_e.xml"
        print(f"Using sample data: {xml_file}\n")

    if not xml_file.exists():
        print(f"Error: File not found: {xml_file}")
        sys.exit(1)

    print("=" * 60)
    print("Urine Small Molecules (brxsm_uri)")
    print("=" * 60)

    # Read quantification data
    print("\n1. Read Quantification Data:")
    print("-" * 40)
    quant = read_quant(xml_file)
    if quant:
        print(f"Version: {quant['version']}")
        print(f"Metabolites: {len(quant['data'])}")

        if args.show_all:
            print("\nAll metabolites:")
            print(quant['data'][['name', 'conc_v', 'concUnit_v']].to_string(index=False))
        else:
            print("\nFirst 10 metabolites:")
            print(quant['data'][['name', 'conc_v', 'concUnit_v']].head(10).to_string(index=False))

    # Show metabolite summary
    print("\n2. Metabolite Summary:")
    print("-" * 40)
    if quant:
        data = quant['data']
        print(f"Total metabolites: {len(data)}")
        print(f"Non-zero metabolites: {(data['conc_v'] != '0').sum()}")

    # Export if requested
    if args.output and quant:
        output_path = Path(args.output)
        quant['data'].to_csv(output_path, index=False)
        print(f"\n✓ Exported to: {output_path}")


if __name__ == "__main__":
    main()
