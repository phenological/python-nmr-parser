"""Functions for reading NMR spectrum data from Bruker files."""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Union, Optional, Dict, Literal, TypedDict
from dataclasses import dataclass
from scipy.interpolate import interp1d
from rich.console import Console

from .parameters import read_param

console = Console()


class SpectrumOptions(TypedDict, total=False):
    """Options for spectrum reading and processing."""
    uncalibrate: bool
    eretic: float
    fromTo: tuple[float, float]
    length_out: int
    im: bool


@dataclass
class SpectrumInfo:
    """Metadata for a processed spectrum."""
    SF: float
    PHC0: float
    PHC1: float
    SR: float
    ereticFactor: Optional[float]
    uncalibrated: int


@dataclass
class SpectrumResult:
    """Result from reading a spectrum."""
    info: SpectrumInfo
    spec: pd.DataFrame  # columns: x, y, [yi if imaginary]


def read_1r(file: Union[str, Path],
            number_of_points: int,
            nc: int = 0,
            endian: Literal["little", "big"] = "little") -> np.ndarray:
    """
    Read binary spectrum file (processed, 1r or 1i).

    Reads 32-bit signed integer binary spectrum data and applies
    the NC power factor scaling (spec * 2^nc).

    Parameters
    ----------
    file : str or Path
        Path to the binary spectrum file (1r or 1i)
    number_of_points : int
        Number of points to read
    nc : int, default=0
        Power factor for scaling (NC_proc parameter)
    endian : {"little", "big"}, default="little"
        Byte order of the binary file

    Returns
    -------
    np.ndarray
        Spectrum data as float64 array

    Examples
    --------
    >>> spec = read_1r("experiment/pdata/1/1r", 131072, nc=0, endian="little")
    >>> len(spec)
    131072
    """
    file = Path(file)

    # Determine dtype based on endianness
    # '<i4' = little-endian 32-bit signed int
    # '>i4' = big-endian 32-bit signed int
    dtype = '<i4' if endian == 'little' else '>i4'

    try:
        # Read binary data
        spec = np.fromfile(str(file), dtype=dtype, count=number_of_points)

        # Apply power factor scaling
        spec = (2 ** nc) * spec

        return spec.astype(np.float64)

    except Exception as e:
        console.print(f"[red]read_1r >> Error reading {file}: {e}[/red]")
        return np.array([])


def read_spectrum(expno: Union[str, Path],
                  procno: int = 1,
                  procs: Union[bool, str, Path] = True,
                  options: Optional[SpectrumOptions] = None) -> Optional[SpectrumResult]:
    """
    Read a processed spectrum from a Bruker expno folder.

    Reads binary spectrum files (1r/1i), constructs the ppm axis,
    handles calibration, and optionally applies ERETIC correction
    and interpolation to a common grid.

    Parameters
    ----------
    expno : str or Path
        Path to the experiment number folder
    procno : int, default=1
        Processing number to read from (subfolder in pdata/)
    procs : bool or str or Path, default=True
        If True, reads procs file from standard location.
        Can also be a path to a specific procs file.
    options : dict, optional
        Processing options with keys:

        - uncalibrate : bool, default=False
            Remove calibration offset (SR)
        - eretic : float, optional
            ERETIC correction factor to apply
        - fromTo : tuple[float, float], optional
            PPM range for interpolation (from_ppm, to_ppm)
        - length_out : int, optional
            Number of points in interpolated spectrum
        - im : bool, default=False
            Read imaginary part from 1i file

    Returns
    -------
    SpectrumResult or None
        Dataclass containing:

        - info : SpectrumInfo
            Metadata (SF, PHC0, PHC1, SR, ereticFactor, uncalibrated)
        - spec : pd.DataFrame
            Spectrum data with columns 'x' (ppm), 'y' (intensity),
            and optionally 'yi' (imaginary) if im=True

        Returns None if file not found or parameters invalid.

    Examples
    --------
    >>> spec = read_spectrum("experiment/10")
    >>> print(spec.spec[['x', 'y']].head())
    """
    expno = Path(expno)
    options = options or {}

    # Build file paths
    file_1r = expno / "pdata" / str(procno) / "1r"
    file_1i = expno / "pdata" / str(procno) / "1i"

    if isinstance(procs, bool) and procs:
        file_procs = expno / "pdata" / str(procno) / "procs"
    else:
        file_procs = Path(procs)

    file_acqus = expno / "acqus"

    # Check files exist and are not empty
    if not file_procs.exists():
        console.print(f"[yellow]readSpectrum >> procs file not found for {expno}[/yellow]")
        return None

    nc_proc = read_param(file_procs, "NC_proc")
    if nc_proc is None:
        console.print(f"[yellow]readSpectrum >> empty procs file for {expno}[/yellow]")
        return None

    if not file_acqus.exists():
        console.print(f"[yellow]readSpectrum >> acqus file not found for {expno}[/yellow]")
        return None

    bf1 = read_param(file_acqus, "BF1")
    if bf1 is None:
        console.print(f"[yellow]readSpectrum >> empty acqus for {expno}[/yellow]")
        return None

    if not file_1r.exists():
        console.print(f"[yellow]readSpectrum >> data not found for {expno}[/yellow]")
        return None

    # Check for imaginary part if requested
    im = options.get('im', False)
    if im and not file_1i.exists():
        console.print(f"[yellow]readSpectrum >> imaginary data not found for {expno}[/yellow]")
        return None

    uncalibrate = options.get('uncalibrate', False)

    # Read important parameters
    bytordp = read_param(file_procs, "BYTORDP")
    endian = "little" if bytordp == 0 else "big"

    nc = read_param(file_procs, "NC_proc")
    size = read_param(file_procs, "FTSIZE")
    sf = read_param(file_procs, "SF")
    sw_p = read_param(file_procs, "SW_p")
    offset = read_param(file_procs, "OFFSET")
    phc0 = read_param(file_procs, "PHC0")
    phc1 = read_param(file_procs, "PHC1")

    # Check for empty parameters
    params = [endian, nc, size, sf, sw_p, offset, phc0, phc1, bf1]
    if any(p is None for p in params):
        console.print(f"[yellow]readSpectrum >> empty parameter for {expno}[/yellow]")
        return None

    if phc1 != 0:
        console.print(f"[yellow]readSpectrum >> phc1 is expected to be 0 in IVDr experiments. Found: {phc1}[/yellow]")

    # Compute spectral width and SR
    sw = sw_p / sf
    SR_p = (sf - bf1) * 1e6 / sf
    SR = (sf - bf1) * 1e6

    if uncalibrate:
        offset = offset + SR_p
        # Removed verbose per-spectrum logging
        # console.print(f"[blue]readSpectrum >> calibration (SR) removed: {SR_p} ppm {SR} Hz[/blue]")

    # Read spectrum
    y = read_1r(file_1r, size, nc, endian)
    y = y[::-1]  # Reverse array

    # Compute ppm axis
    inc = sw / (len(y) - 1)
    x = np.arange(offset, offset - sw - inc/2, -inc)
    x = x[::-1]  # Reverse

    # Ensure x and y have same length
    min_len = min(len(x), len(y))
    x = x[:min_len]
    y = y[:min_len]

    # Read imaginary if requested
    yi = None
    if im:
        yi = read_1r(file_1i, size, nc, endian)
        yi = yi[::-1]
        yi = yi[:min_len]

        if len(yi) != len(y):
            console.print(f"[yellow]readSpectrum >> Im and Re have different dimensions {expno}[/yellow]")
            return None

    # Apply ERETIC correction if provided
    eretic_factor = options.get('eretic')
    if eretic_factor is not None:
        y = y / eretic_factor
        if yi is not None:
            yi = yi / eretic_factor
        # Removed verbose per-spectrum logging
        # console.print(f"[blue]readSpectrum >> spectra corrected for eretic: {eretic_factor}[/blue]")

    # Interpolation if fromTo is specified
    if 'fromTo' in options:
        from_ppm, to_ppm = options['fromTo']

        if from_ppm > to_ppm:
            console.print("[blue]readSpectrum >> from should be smaller than to[/blue]")

        # Determine output length
        if 'length_out' in options:
            length_out = options['length_out']
        else:
            # Use trimmed size
            mask = (x > from_ppm) & (x < to_ppm)
            length_out = mask.sum()

        new_x = np.linspace(from_ppm, to_ppm, length_out)

        if len(x) == len(y):
            # Interpolate using cubic spline
            f = interp1d(x, y, kind='cubic', bounds_error=False, fill_value='extrapolate')
            y = f(new_x)

            if yi is not None:
                f_i = interp1d(x, yi, kind='cubic', bounds_error=False, fill_value='extrapolate')
                yi = f_i(new_x)
        else:
            console.print(f"[red]readSpectrum >> x and y are of different length[/red]")
            console.print(f"[blue]readSpectrum >> {expno}[/blue]")
            console.print(f"[blue]readSpectrum >> length(x) {len(x)}[/blue]")
            console.print(f"[blue]readSpectrum >> length(y) {len(y)}[/blue]")
            return None

        x = new_x
        # Removed verbose per-spectrum logging - this was printing for EVERY spectrum!
        # Only print once per batch in parse_nmr instead
        # console.print(f"[blue]readSpectrum >> spectra in common grid (from: {from_ppm} to: {to_ppm} dim: {length_out} orig.size: {size})[/blue]")

    # Build info dict
    info = SpectrumInfo(
        SF=sf,
        PHC0=phc0,
        PHC1=phc1,
        SR=SR,
        ereticFactor=eretic_factor,
        uncalibrated=1 if uncalibrate else 0
    )

    # Build spectrum DataFrame
    if yi is not None:
        spec_df = pd.DataFrame({'x': x, 'y': y, 'yi': yi})
    else:
        spec_df = pd.DataFrame({'x': x, 'y': y})

    return SpectrumResult(info=info, spec=spec_df)
