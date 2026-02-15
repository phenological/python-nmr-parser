#!/usr/bin/env python3
"""
Example: Processing NMR spectrum data

This script demonstrates advanced spectrum processing including:
- Reading binary spectrum files
- Calibration and interpolation
- ERETIC correction
- Plotting (requires matplotlib)

Usage:
    python process_spectrum_example.py [experiment_path]

Example:
    python process_spectrum_example.py /path/to/experiment/10
"""

import sys
import argparse
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nmr_parser import read_spectrum, read_experiment


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Process and analyze NMR spectrum data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python process_spectrum_example.py /path/to/experiment/10
  python process_spectrum_example.py  # Uses default test data
        """
    )
    parser.add_argument(
        'experiment_path',
        nargs='?',
        type=str,
        help='Path to experiment folder (default: uses test data)'
    )

    args = parser.parse_args()

    # Determine experiment path
    if args.experiment_path:
        exp_path = Path(args.experiment_path)
        print(f"Processing: {exp_path}\n")
    else:
        # Default to test data
        test_data = Path(__file__).parent.parent / "tests" / "data"
        exp_path = test_data / "HB-COVID0001" / "10"
        print(f"No path provided, using test data: {exp_path}\n")

    if not exp_path.exists():
        print(f"Error: Experiment path not found: {exp_path}")
        sys.exit(1)

    print("=" * 60)
    print("Processing NMR Spectrum Data")
    print("=" * 60)

    # Example 1: Read spectrum with default options
    print("\n1. Read Spectrum (Default Options):")
    print("-" * 40)
    spec = read_spectrum(exp_path, procno=1)
    if spec is not None:
        spec_df = spec.spec
        print(f"Data points: {len(spec_df['x'])}")
        print(f"PPM range: {spec_df['x'].min():.3f} to {spec_df['x'].max():.3f} ppm")
        print(f"Intensity: {spec_df['y'].min():.2e} to {spec_df['y'].max():.2e}")

    # Example 2: Read spectrum with custom PPM range
    print("\n2. Read Spectrum (Custom PPM Range):")
    print("-" * 40)
    opts = {
        'fromTo': (0.5, 9.5),      # Focus on metabolite region
        'length_out': 16384         # Downsample to 16k points
    }
    spec_custom = read_spectrum(exp_path, procno=1, options=opts)
    if spec_custom is not None:
        spec_df = spec_custom.spec
        print(f"Data points: {len(spec_df['x'])}")
        print(f"PPM range: {spec_df['x'].min():.3f} to {spec_df['x'].max():.3f} ppm")

    # Example 3: Apply ERETIC correction
    print("\n3. Apply ERETIC Correction:")
    print("-" * 40)
    # First, get ERETIC factor from experiment
    exp = read_experiment(exp_path, opts={"what": ["eretic", "spec"]})

    if 'eretic' in exp and exp['eretic'] is not None:
        eretic_factor = exp['eretic']['ereticFactor'].iloc[0]
        print(f"ERETIC factor: {eretic_factor:.2f}")

        # Read spectrum with ERETIC correction
        opts = {'eretic': eretic_factor}
        spec_eretic = read_spectrum(exp_path, procno=1, options=opts)
        if spec_eretic is not None:
            print("✓ Spectrum corrected with ERETIC factor")

    # Example 4: Extract specific regions
    print("\n4. Extract Specific Spectral Regions:")
    print("-" * 40)
    spec = read_spectrum(exp_path, procno=1)
    if spec is not None:
        spec_df = spec.spec
        x = np.array(spec_df['x'])
        y = np.array(spec_df['y'])

        # Define regions of interest
        regions = {
            'Aliphatic': (0.5, 3.0),
            'Carbohydrates': (3.0, 6.0),
            'Aromatic': (6.0, 9.0)
        }

        print("\nIntegral by region:")
        for region_name, (low, high) in regions.items():
            mask = (x >= low) & (x <= high)
            integral = np.trapezoid(y[mask], x[mask])
            print(f"  {region_name} ({low}-{high} ppm): {integral:.2e}")

    # Example 5: Find peak positions
    print("\n5. Find Peak Positions:")
    print("-" * 40)
    spec = read_spectrum(exp_path, procno=1)
    if spec is not None:
        spec_df = spec.spec
        x = np.array(spec_df['x'])
        y = np.array(spec_df['y'])

        # Simple peak finding (local maxima)
        # Note: For production use, consider scipy.signal.find_peaks
        threshold = y.max() * 0.1  # 10% of max intensity

        peaks = []
        for i in range(1, len(y) - 1):
            if y[i] > y[i-1] and y[i] > y[i+1] and y[i] > threshold:
                peaks.append((x[i], y[i]))

        print(f"Found {len(peaks)} peaks above threshold")
        print("\nTop 5 peaks:")
        peaks_sorted = sorted(peaks, key=lambda p: p[1], reverse=True)[:5]
        for ppm, intensity in peaks_sorted:
            print(f"  {ppm:.3f} ppm: {intensity:.2e}")

    # Example 6: Plot spectrum (if matplotlib available)
    print("\n6. Plot Spectrum:")
    print("-" * 40)
    try:
        import matplotlib.pyplot as plt

        spec = read_spectrum(exp_path, procno=1, options={'fromTo': (0.5, 9.5)})
        if spec is not None:
            spec_df = spec.spec
            x = spec_df['x']
            y = spec_df['y']

            plt.figure(figsize=(12, 4))
            plt.plot(x, y, linewidth=0.5, color='black')
            plt.xlabel('Chemical Shift (ppm)')
            plt.ylabel('Intensity')
            plt.title('1H NMR Spectrum')
            plt.xlim(x.max(), x.min())  # Reverse x-axis (NMR convention)
            plt.grid(True, alpha=0.3)

            output_file = Path("spectrum_plot.png")
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"✓ Spectrum saved to: {output_file}")
            plt.close()

    except ImportError:
        print("matplotlib not installed - skipping plot")
        print("Install with: pip install matplotlib")

    # Example 7: Export spectrum to CSV
    print("\n7. Export Spectrum Data:")
    print("-" * 40)
    spec = read_spectrum(exp_path, procno=1)
    if spec is not None:
        spec_df = spec.spec

        # Create DataFrame for export
        import pandas as pd
        export_data = pd.DataFrame({
            'ppm': spec_df['x'],
            'intensity': spec_df['y']
        })

        output_file = Path("spectrum_data.csv")
        export_data.to_csv(output_file, index=False)
        print(f"✓ Spectrum exported to: {output_file}")
        print(f"  Rows: {len(export_data)}")


if __name__ == "__main__":
    main()
