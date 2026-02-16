#!/usr/bin/env python3
"""
Example: Extending Lipoprotein Data with Calculated Metrics

This example demonstrates how to use extend_lipo() and extend_lipo_value()
to calculate derived metrics from raw B.I.QUANT-PS lipoprotein measurements.

Usage:
    python extend_lipo_example.py <path_to_lipo.xml>
    python extend_lipo_example.py <experiment_folder>  # Finds lipo.xml in pdata/1/

The extend_lipo functions calculate 200+ derived metrics including:
- Total lipids (TL = TG + CH + PL)
- Cholesterol esters (CE = CH - FC)
- Composition percentages (e.g., CE as % of TL)
- Subfraction distributions (e.g., H1 TG as % of HD TG)
- Particle sizes and reference ranges

IMPORTANT: extend_lipo() only works with read_lipo() output (single experiment),
not with read_experiment() output (multiple experiments in wide format).
"""

import sys
from pathlib import Path
import pandas as pd
from rich.console import Console
from rich.table import Table

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nmr_parser import read_lipo, extend_lipo, extend_lipo_value

console = Console()


def find_lipo_xml(path: Path) -> Path:
    """Find lipo.xml file in experiment folder or return path if it's already a file."""
    if path.is_file() and path.name.endswith('.xml'):
        return path

    # Try pdata/1/ subdirectory
    lipo_path = path / "pdata" / "1" / "lipo.xml"
    if lipo_path.exists():
        return lipo_path

    # Try finding any lipo xml
    lipo_files = list(path.rglob("*lipo*.xml"))
    if lipo_files:
        return lipo_files[0]

    raise FileNotFoundError(f"No lipo XML file found in {path}")


def show_data_structure(lipo: dict):
    """Display the structure of lipo data."""
    console.print("\n[bold cyan]Data Structure:[/bold cyan]")
    console.print(f"  • Keys: {list(lipo.keys())}")
    console.print(f"  • Version: {lipo['version']}")
    console.print(f"  • Data shape: {lipo['data'].shape}")
    console.print(f"  • Columns: {', '.join(lipo['data'].columns)}")


def show_raw_measurements(lipo: dict, n: int = 10):
    """Display sample of raw measurements."""
    console.print(f"\n[bold cyan]Raw Measurements (first {n}):[/bold cyan]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan")
    table.add_column("Fraction", style="green")
    table.add_column("Name", style="white")
    table.add_column("Value", justify="right", style="yellow")
    table.add_column("Unit", style="dim")

    for _, row in lipo['data'].head(n).iterrows():
        table.add_row(
            row['id'],
            row.get('fraction', ''),
            row.get('name', ''),
            f"{row['value']:.4f}" if pd.notna(row['value']) else "N/A",
            row.get('unit', '')
        )

    console.print(table)


def show_calculated_metrics(extended: pd.DataFrame):
    """Display calculated metrics (_calc suffix)."""
    console.print("\n[bold cyan]Calculated Metrics (sums & differences):[/bold cyan]")
    console.print("  Examples: HDTL = HDTG + HDCH + HDPL, HDCE = HDCH - HDFC")

    calc_cols = [col for col in extended.columns if '_calc' in col]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="yellow")
    table.add_column("Description", style="dim")

    descriptions = {
        'HDTL_calc': 'HDL Total Lipids',
        'VLTL_calc': 'VLDL Total Lipids',
        'IDTL_calc': 'IDL Total Lipids',
        'LDTL_calc': 'LDL Total Lipids',
        'HDCE_calc': 'HDL Cholesterol Esters',
        'VLCE_calc': 'VLDL Cholesterol Esters',
        'IDCE_calc': 'IDL Cholesterol Esters',
        'LDCE_calc': 'LDL Cholesterol Esters',
        'TBPN_calc': 'Total Particle Number',
        'HDA1_calc': 'HDL Apo-A1',
        'HDA2_calc': 'HDL Apo-A2',
        'LDAB_calc': 'LDL Apo-B',
    }

    for col in calc_cols[:12]:  # Show first 12
        val = extended[col].iloc[0]
        # Handle nested Series structure
        value = float(val.iloc[0] if isinstance(val, pd.Series) else val)
        desc = descriptions.get(col, '')
        value_str = f"{value:.4f}" if not pd.isna(value) else "N/A"
        table.add_row(col, value_str, desc)

    console.print(table)
    console.print(f"  ... and {len(calc_cols) - 12} more calculated metrics")


def show_percentage_metrics(extended: pd.DataFrame):
    """Display percentage metrics (_pct suffix)."""
    console.print("\n[bold cyan]Percentage Metrics (composition %):[/bold cyan]")
    console.print("  Examples: HDCE as % of HDTL, VLPN as % of total particles")

    pct_cols = [col for col in extended.columns if '_pct' in col]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value (%)", justify="right", style="yellow")
    table.add_column("Description", style="dim")

    descriptions = {
        'HDCE_pct': 'HDL CE as % of HDL total lipids',
        'VLCE_pct': 'VLDL CE as % of VLDL total lipids',
        'IDCE_pct': 'IDL CE as % of IDL total lipids',
        'LDCE_pct': 'LDL CE as % of LDL total lipids',
        'VLPN_pct': 'VLDL particles as % of total',
        'IDPN_pct': 'IDL particles as % of total',
    }

    for col in pct_cols[:10]:  # Show first 10
        val = extended[col].iloc[0]
        # Handle nested Series structure
        value = float(val.iloc[0] if isinstance(val, pd.Series) else val)
        desc = descriptions.get(col, '')
        value_str = f"{value:.2f}" if not pd.isna(value) else "N/A"
        table.add_row(col, value_str, desc)

    console.print(table)
    console.print(f"  ... and {len(pct_cols) - 10} more percentage metrics")


def show_fractional_metrics(extended: pd.DataFrame):
    """Display fractional distribution metrics (_frac suffix)."""
    console.print("\n[bold cyan]Fractional Metrics (subfraction distribution %):[/bold cyan]")
    console.print("  Examples: H1TG as % of HDTG, L1CH as % of LDCH")

    frac_cols = [col for col in extended.columns if '_frac' in col]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value (%)", justify="right", style="yellow")
    table.add_column("Description", style="dim")

    descriptions = {
        'H1TG_frac': 'HDL1 TG as % of HDL TG',
        'H2TG_frac': 'HDL2 TG as % of HDL TG',
        'H3TG_frac': 'HDL3 TG as % of HDL TG',
        'H4TG_frac': 'HDL4 TG as % of HDL TG',
        'L1CH_frac': 'LDL1 CH as % of LDL CH',
        'L2CH_frac': 'LDL2 CH as % of LDL CH',
    }

    for col in frac_cols[:10]:  # Show first 10
        val = extended[col].iloc[0]
        # Handle nested Series structure
        value = float(val.iloc[0] if isinstance(val, pd.Series) else val)
        desc = descriptions.get(col, '')
        value_str = f"{value:.2f}" if not pd.isna(value) else "N/A"
        table.add_row(col, value_str, desc)

    console.print(table)
    console.print(f"  ... and {len(frac_cols) - 10} more fractional metrics")


def demonstrate_extend_lipo_value(lipo: dict):
    """Demonstrate extend_lipo_value() which returns wide-format DataFrame."""
    console.print("\n[bold green]═══ Using extend_lipo_value() ═══[/bold green]")
    console.print("Returns a wide-format DataFrame with all metrics as columns")

    extended = extend_lipo_value(lipo)

    console.print(f"\n  • Input: {len(lipo['data'])} raw measurements")
    console.print(f"  • Output: {len(extended.columns)} total metrics")
    console.print(f"  • Added: {len(extended.columns) - 112} calculated metrics")

    # Count by type
    n_calc = sum('_calc' in col for col in extended.columns)
    n_pct = sum('_pct' in col for col in extended.columns)
    n_frac = sum('_frac' in col for col in extended.columns)
    n_size = sum('_size' in col for col in extended.columns)
    n_raw = len(extended.columns) - n_calc - n_pct - n_frac - n_size

    console.print(f"\n  • Raw measurements: {n_raw}")
    console.print(f"  • Calculated (_calc): {n_calc}")
    console.print(f"  • Percentages (_pct): {n_pct}")
    console.print(f"  • Fractions (_frac): {n_frac}")
    console.print(f"  • Sizes (_size): {n_size}")

    show_calculated_metrics(extended)
    show_percentage_metrics(extended)
    show_fractional_metrics(extended)

    return extended


def demonstrate_extend_lipo(lipo: dict):
    """Demonstrate extend_lipo() which returns dict with long-format data + metadata."""
    console.print("\n[bold green]═══ Using extend_lipo() ═══[/bold green]")
    console.print("Returns dict with long-format data including metadata and reference ranges")

    extended = extend_lipo(lipo)

    console.print(f"\n  • Input: {len(lipo['data'])} rows (raw measurements)")
    console.print(f"  • Output: {len(extended['data'])} rows (raw + calculated)")
    console.print(f"  • Version: {extended['version']}")

    # Show metadata columns
    console.print(f"\n  • Columns: {', '.join(extended['data'].columns)}")

    # Show sample with metadata
    console.print("\n[bold cyan]Sample Extended Data (with metadata):[/bold cyan]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan")
    table.add_column("Value", justify="right", style="yellow")
    table.add_column("Unit", style="dim")
    table.add_column("Ref Min", justify="right", style="green")
    table.add_column("Ref Max", justify="right", style="red")
    table.add_column("Tag", style="dim")

    # Show mix of raw and calculated
    sample_ids = ['HDTG', 'HDTL_calc', 'HDCE_calc', 'HDCE_pct', 'H1TG_frac']
    sample_data = extended['data'][extended['data']['id'].isin(sample_ids)]

    for _, row in sample_data.iterrows():
        # Handle possible nested Series in values
        val = row['value']
        if isinstance(val, pd.Series):
            value = float(val.iloc[0]) if len(val) > 0 and not pd.isna(val.iloc[0]) else None
        else:
            value = float(val) if not pd.isna(val) else None

        ref_min = row.get('refMin', '')
        ref_max = row.get('refMax', '')

        table.add_row(
            str(row['id']),
            f"{value:.4f}" if value is not None else "N/A",
            str(row.get('unit', '')),
            f"{ref_min:.2f}" if pd.notna(ref_min) and ref_min != '' else "",
            f"{ref_max:.2f}" if pd.notna(ref_max) and ref_max != '' else "",
            str(row.get('tag', ''))
        )

    console.print(table)

    return extended


def show_comparison(lipo_value: pd.DataFrame, lipo_full: dict):
    """Compare the two output formats."""
    console.print("\n[bold yellow]═══ Comparison ═══[/bold yellow]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Feature", style="cyan")
    table.add_column("extend_lipo_value()", style="green")
    table.add_column("extend_lipo()", style="blue")

    table.add_row(
        "Output format",
        "Wide DataFrame",
        "Dict with long DataFrame"
    )
    table.add_row(
        "Shape",
        f"{lipo_value.shape}",
        f"{lipo_full['data'].shape}"
    )
    table.add_row(
        "Use case",
        "Analysis, ML input",
        "Database storage, joining"
    )
    table.add_row(
        "Includes metadata",
        "No (values only)",
        "Yes (units, refs, tags)"
    )
    table.add_row(
        "Easy to merge",
        "Yes (wide format)",
        "Yes (long format with keys)"
    )

    console.print(table)


def main():
    if len(sys.argv) < 2:
        console.print("[red]Error: Please provide path to lipo XML or experiment folder[/red]")
        console.print(f"\nUsage: {sys.argv[0]} <path_to_lipo.xml>")
        console.print(f"       {sys.argv[0]} <experiment_folder>")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        console.print(f"[red]Error: Path not found: {input_path}[/red]")
        sys.exit(1)

    console.print("[bold]Extending Lipoprotein Data Example[/bold]\n")

    # Find and read lipo XML
    try:
        lipo_file = find_lipo_xml(input_path)
        console.print(f"[blue]Reading: {lipo_file}[/blue]")

        lipo = read_lipo(lipo_file)

        if lipo is None:
            console.print("[red]Error: Failed to read lipo file[/red]")
            sys.exit(1)

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    # Show structure and raw data
    show_data_structure(lipo)
    show_raw_measurements(lipo)

    # Demonstrate both functions
    console.print("\n" + "="*80)
    lipo_value = demonstrate_extend_lipo_value(lipo)

    console.print("\n" + "="*80)
    lipo_full = demonstrate_extend_lipo(lipo)

    console.print("\n" + "="*80)
    show_comparison(lipo_value, lipo_full)

    # Show common usage patterns
    console.print("\n[bold cyan]═══ Common Usage Patterns ═══[/bold cyan]")
    console.print("""
[bold]1. For machine learning / data analysis:[/bold]
   extended = extend_lipo_value(lipo)  # Wide format, easy to use
   df = pd.DataFrame(extended)

[bold]2. For database storage:[/bold]
   extended = extend_lipo(lipo)  # Long format with metadata
   extended['data'].to_parquet('lipo_extended.parquet')

[bold]3. Accessing specific metrics:[/bold]
   extended = extend_lipo_value(lipo)
   hdl_total = extended['HDTL_calc'].iloc[0]
   hdl_ce_pct = extended['HDCE_pct'].iloc[0]

[bold]4. With read_experiment() (multiple samples):[/bold]
   # DON'T do this:
   exp = read_experiment(folder, what='lipo')
   extended = extend_lipo(exp['lipo'])  # ERROR! Wrong format

   # Instead, read individual files:
   lipo = read_lipo(folder / 'pdata/1/lipo.xml')
   extended = extend_lipo(lipo)  # OK!
""")

    console.print("\n[bold green]✓ Example complete![/bold green]")


if __name__ == '__main__':
    main()
