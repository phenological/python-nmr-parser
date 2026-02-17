#!/usr/bin/env python3
"""
Example: Reading urine quality control data (brxqc_uri)

Demonstrates reading urine QC report and checking test results.

Usage:
    python read_brxqc_uri_example.py [xml_file]
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nmr_parser import read_qc


def main():
    parser = argparse.ArgumentParser(
        description="Read urine quality control data"
    )
    parser.add_argument('xml_file', nargs='?', help='Path to urine QC XML file')
    parser.add_argument('-o', '--output', help='Output CSV file')

    args = parser.parse_args()

    # Get file path
    if args.xml_file:
        xml_file = Path(args.xml_file)
    else:
        from nmr_parser.reference.tables import DATA_DIR
        xml_file = DATA_DIR / "urine_qc_report.xml"
        print(f"Using sample data: {xml_file}\n")

    if not xml_file.exists():
        print(f"Error: File not found: {xml_file}")
        sys.exit(1)

    print("=" * 60)
    print("Urine Quality Control (brxqc_uri)")
    print("=" * 60)

    # Read QC data
    print("\n1. Read QC Data:")
    print("-" * 40)
    qc = read_qc(xml_file)
    if qc:
        print(f"Version: {qc['version']}")
        print(f"QC Tests: {len(qc['data'])}")
        print("\nQC Test Results:")
        for key, value in qc['data'].items():
            print(f"  {key}: {value}")

    # Export if requested
    if args.output and qc:
        import pandas as pd
        output_path = Path(args.output)
        # Combine infos and tests into single DataFrame
        df_infos = pd.DataFrame(qc['data']['infos'])
        df_tests = pd.DataFrame(qc['data']['tests'])
        df_combined = pd.concat([df_infos, df_tests], ignore_index=True)
        df_combined.to_csv(output_path, index=False)
        print(f"\n✓ Exported {len(df_combined)} tests to: {output_path}")


if __name__ == "__main__":
    main()
