"""Folder scanning utilities for finding Bruker experiments."""

from pathlib import Path
from typing import Union, Optional, Dict, Any, List
import pandas as pd
from rich.console import Console
from rich.prompt import Prompt
from collections import Counter

from .parameters import read_param
from ..processing.utils import clean_names

console = Console()


def scan_folder(folder: Union[str, Path],
                options: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Scan folder recursively to get list of experiment paths.

    Searches for Bruker experiment folders by finding acqus files,
    then filters by EXP and PULPROG parameters. Can optionally
    present an interactive menu for selection.

    Parameters
    ----------
    folder : str or Path
        Root folder(s) to scan (can be string or list of paths)
    options : dict, optional
        Scanning options with keys:

        - EXP : str
            Filter by experiment name (e.g., "PROF_PLASMA_NOESY")
            Set to "ignore" to skip EXP filtering
        - PULPROG : str
            Filter by pulse program (e.g., "noesygppr1d")

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - file: Path to experiment folder
        - EXP: Experiment name
        - PULPROG: Pulse program
        - USERA2: User parameter A2

    Notes
    -----
    Filters out special experiment numbers (99999, 98888).

    If no options provided, presents interactive menu to choose
    experiment type based on found EXP@PULPROG combinations.

    Examples
    --------
    >>> # Interactive mode (presents menu)
    >>> experiments = scan_folder("data/")

    >>> # Filter by pulse program
    >>> experiments = scan_folder(
    ...     "data/",
    ...     options={"PULPROG": "noesygppr1d", "EXP": "PROF_PLASMA_NOESY"}
    ... )

    >>> # Ignore EXP, filter only by PULPROG
    >>> experiments = scan_folder(
    ...     "data/",
    ...     options={"EXP": "ignore", "PULPROG": "noesygppr1d"}
    ... )
    """
    folder = Path(folder)
    options = options or {}

    EXP = options.get('EXP', '')
    PULPROG = options.get('PULPROG', '')

    # Find all acqus files recursively
    acqus_files = list(folder.rglob("acqus"))

    # Filter to only files named exactly "acqus" (not acqus.safe, etc.)
    acqus_files = [f for f in acqus_files if f.name == "acqus"]

    # Filter out odd experiment numbers
    acqus_files = [f for f in acqus_files
                   if not any(x in str(f) for x in ["99999/acqus", "98888/acqus"])]

    console.print(f"[blue]Found {len(acqus_files)} acqus files[/blue]")

    # Extract parameters from each acqus file
    exp_list = []
    for i, acqus_file in enumerate(acqus_files):
        console.print(f"Scanning: {i+1} / {len(acqus_files)}", end="\r")

        # Read EXP, PULPROG, and USERA2 parameters
        params = read_param(acqus_file, ["EXP", "PULPROG", "USERA2"])

        if params:
            exp_name = clean_names(params[0]) if params[0] else ""
            pulprog = clean_names(params[1]) if params[1] else ""
            usera2 = params[2] if len(params) > 2 else ""

            # Get experiment folder (parent of acqus)
            exp_folder = acqus_file.parent

            exp_list.append({
                'file': str(exp_folder),
                'EXP': exp_name,
                'PULPROG': pulprog,
                'USERA2': usera2
            })

    console.print()  # New line after progress

    if not exp_list:
        console.print("[yellow]No experiments found[/yellow]")
        return pd.DataFrame()

    exp_df = pd.DataFrame(exp_list)

    # Check if interactive mode should be used
    # Skip interactive if explicitly set to "all" or both filters provided
    skip_interactive = (
        EXP == "all" or
        (EXP and EXP != '' and PULPROG and PULPROG != '')
    )

    # Interactive selection if no filters provided
    if not skip_interactive and EXP == '' and PULPROG == '':
        exp_df = _interactive_selection(exp_df)

    # Filter by EXP (unless set to "ignore" or "all")
    elif not skip_interactive and EXP == "ignore" and PULPROG == '':
        # Filter only by PULPROG (interactive)
        exp_df = _interactive_selection_pulprog(exp_df)

    else:
        # Apply filters (or return all if EXP="all")
        if EXP and EXP not in ["ignore", "all"]:
            exp_df = exp_df[exp_df['EXP'].str.contains(EXP, na=False)]

        if PULPROG:
            exp_df = exp_df[exp_df['PULPROG'].str.contains(PULPROG, na=False)]

    # Print summary
    if len(exp_df) > 0:
        exp_pulprog_counts = Counter(
            exp_df['EXP'] + "@" + exp_df['PULPROG']
        )
        for combo, count in exp_pulprog_counts.items():
            console.print(f"[blue]scanFolder >> {combo}: {count}[/blue]")
    else:
        console.print("[yellow]No experiments matched filters[/yellow]")

    return exp_df.reset_index(drop=True)


def _interactive_selection(exp_df: pd.DataFrame) -> pd.DataFrame:
    """Present interactive menu for EXP@PULPROG selection."""
    # Count EXP@PULPROG combinations
    exp_df['combo'] = exp_df['EXP'] + "@" + exp_df['PULPROG']
    combo_counts = exp_df['combo'].value_counts()

    console.print("\n[bold]Choose experiment type to parse:[/bold]")
    choices = []
    for i, (combo, count) in enumerate(combo_counts.items(), 1):
        choice_text = f"{combo} ({count})"
        choices.append(choice_text)
        console.print(f"{i}. {choice_text}")

    # Get user choice
    choice_num = Prompt.ask(
        "Enter choice number",
        choices=[str(i) for i in range(1, len(choices) + 1)],
        default="1"
    )

    selected_combo = combo_counts.index[int(choice_num) - 1]
    selected_exp, selected_pulprog = selected_combo.split("@")

    # Filter DataFrame
    result = exp_df[
        (exp_df['EXP'] == selected_exp) &
        (exp_df['PULPROG'] == selected_pulprog)
    ].copy()

    result = result.drop('combo', axis=1)
    return result


def _interactive_selection_pulprog(exp_df: pd.DataFrame) -> pd.DataFrame:
    """Present interactive menu for PULPROG selection only."""
    pulprog_counts = exp_df['PULPROG'].value_counts()

    console.print("\n[bold]Choose pulse program to parse:[/bold]")
    choices = []
    for i, (pulprog, count) in enumerate(pulprog_counts.items(), 1):
        choice_text = f"{pulprog} ({count})"
        choices.append(choice_text)
        console.print(f"{i}. {choice_text}")

    # Get user choice
    choice_num = Prompt.ask(
        "Enter choice number",
        choices=[str(i) for i in range(1, len(choices) + 1)],
        default="1"
    )

    selected_pulprog = pulprog_counts.index[int(choice_num) - 1]

    # Filter DataFrame
    result = exp_df[exp_df['PULPROG'] == selected_pulprog].copy()
    return result
