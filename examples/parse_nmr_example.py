#!/usr/bin/env python3
"""
Example: Parse NMR Data to Parquet Files

Demonstrates using parse_nmr to convert NMR data to parquet format,
preserving all research decisions from the original R code.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nmr_parser import parse_nmr
from rich.console import Console

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description='Parse NMR data to parquet files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Parse spectra from a folder
  python parse_nmr_example.py data/experiments/ -o output/

  # Parse with metadata
  python parse_nmr_example.py data/ \\
      --project HB \\
      --cohort COVID \\
      --run EXTr01 \\
      --matrix plasma

  # Parse spcglyc biomarkers
  python parse_nmr_example.py data/ --what spcglyc

  # Parse from direct paths (no write)
  python parse_nmr_example.py --paths exp1/10 exp2/10 exp3/10 --no-write

  # Custom spectral parameters
  python parse_nmr_example.py data/ \\
      --ppm-range -0.5 12 \\
      --n-points 50000
        '''
    )

    parser.add_argument(
        'folder',
        nargs='?',
        help='Folder to scan for experiments'
    )

    parser.add_argument(
        '--paths',
        nargs='+',
        help='Direct experiment paths (bypasses folder scanning)'
    )

    parser.add_argument(
        '--what',
        choices=['spec', 'spcglyc', 'brxlipo', 'brxpacs', 'brxsm'],
        default='spec',
        help='Data type to parse (default: spec)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='.',
        help='Output directory for parquet files (default: current directory)'
    )

    parser.add_argument(
        '--project',
        type=str,
        default='',
        help='Project name'
    )

    parser.add_argument(
        '--cohort',
        type=str,
        default='',
        help='Cohort name'
    )

    parser.add_argument(
        '--run',
        type=str,
        default='',
        help='Run name'
    )

    parser.add_argument(
        '--matrix',
        type=str,
        default='',
        help='Sample matrix type (e.g., plasma, serum)'
    )

    parser.add_argument(
        '--method',
        type=str,
        default='',
        help='Method name'
    )

    parser.add_argument(
        '--ppm-range',
        nargs=2,
        type=float,
        default=(-0.1, 10),
        metavar=('MIN', 'MAX'),
        help='PPM range for spectra (default: -0.1 10)'
    )

    parser.add_argument(
        '--n-points',
        type=int,
        default=44079,
        help='Number of spectral points (default: 44079)'
    )

    parser.add_argument(
        '--procno',
        type=int,
        default=1,
        help='Processing number (default: 1)'
    )

    parser.add_argument(
        '--uncalibrate',
        action='store_true',
        help='Remove calibration (read raw spectrum)'
    )

    parser.add_argument(
        '--no-write',
        action='store_true',
        help='Do not write parquet files (return DataFrames only)'
    )

    args = parser.parse_args()

    # Validate input
    if not args.paths and not args.folder:
        parser.error("Either 'folder' or '--paths' must be provided")

    # Prepare input
    if args.paths:
        folder_input = {'dataPath': args.paths}
    else:
        folder_input = args.folder

    # Prepare options
    opts = {
        'what': [args.what],
        'projectName': args.project,
        'cohortName': args.cohort,
        'runName': args.run,
        'method': args.method,
        'sampleMatrixType': args.matrix,
        'specOpts': {
            'procno': args.procno,
            'uncalibrate': args.uncalibrate,
            'fromTo': tuple(args.ppm_range),
            'length_out': args.n_points
        },
        'outputDir': args.output,
        'noWrite': args.no_write
    }

    # Run parse_nmr
    try:
        console.print("\n[bold blue]╔══════════════════════════════════════╗[/bold blue]")
        console.print("[bold blue]║  NMR Parser - Parquet Export       ║[/bold blue]")
        console.print("[bold blue]╚══════════════════════════════════════╝[/bold blue]\n")

        result = parse_nmr(folder_input, opts=opts)

        # Print summary
        console.print("\n[bold green]✓ Parsing complete![/bold green]\n")

        console.print("[bold]Data Summary:[/bold]")
        console.print(f"  • Samples: {len(result['data'])}")
        console.print(f"  • Variables: {len(result['variables'])}")
        console.print(f"  • Data type: {result['metadata']['data_type'].iloc[0]}")
        console.print(f"  • Method: {result['metadata']['method'].iloc[0]}")

        console.print("\n[bold]Sample Types:[/bold]")
        type_counts = result['metadata']['sample_type'].value_counts()
        for stype, count in type_counts.items():
            console.print(f"  • {stype}: {count}")

        if not args.no_write:
            console.print(f"\n[bold]Output files:[/bold]")
            output_dir = Path(args.output)
            for key in ['data', 'metadata', 'params', 'variables']:
                if key in result:
                    console.print(f"  • {output_dir / '...'}{key}.parquet")

        # Show preview of data
        if args.no_write:
            console.print("\n[bold]Data Preview:[/bold]")
            console.print(result['data'].head())

            console.print("\n[bold]Metadata Preview:[/bold]")
            console.print(result['metadata'][['sample_id', 'sample_type', 'data_type']].head())

        # Show spcglyc specific info
        if args.what == 'spcglyc':
            console.print("\n[bold blue]spcglyc Biomarkers Calculated:[/bold blue]")
            biomarkers = result['variables']['var_name'].tolist()
            for bm in biomarkers:
                console.print(f"  • {bm}")

            if 'tsp' in result:
                console.print(f"\n  Additional data: TSP region ({result['tsp'].shape[1]} points)")
            if 'spc_region' in result:
                console.print(f"  Additional data: SPC region ({result['spc_region'].shape[1]} points)")
            if 'glyc_region' in result:
                console.print(f"  Additional data: Glyc region ({result['glyc_region'].shape[1]} points)")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
