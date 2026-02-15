"""Utility functions for data processing."""

import re
from typing import Union, List


def clean_names(names: Union[str, List[str]]) -> Union[str, List[str]]:
    """
    Clean names for importation into databases.

    This function standardizes names by removing special characters,
    normalizing whitespace, and converting to lowercase. It's designed
    to create database-friendly identifiers while preserving meaningful
    information.

    Parameters
    ----------
    names : str or list of str
        A name or array of names to clean

    Returns
    -------
    str or list of str
        Cleaned name(s) in the same format as input

    Examples
    --------
    >>> clean_names("ddd.aaa")
    'ddd-aaa'
    >>> clean_names(["ddd uuu", "ddd+aaa", "ddd*yyy"])
    ['ddd-uuu', 'dddpaaa', 'dddtyyy']
    >>> clean_names("ddd#dd")
    'ddd#dd'
    """
    # Handle single string input
    is_single = isinstance(names, str)
    if is_single:
        names = [names]

    cleaned = []
    for name in names:
        # Remove backslashes
        name = name.replace("\\", " ")

        # Remove trailing spaces
        name = re.sub(r'\s+$', '', name)

        # Remove leading spaces
        name = re.sub(r'^\s+', '', name)

        # Remove double spaces
        name = re.sub(r'\s+', ' ', name)

        # Convert to lowercase
        name = name.lower()

        # Handle special characters
        # Trailing asterisk becomes -s
        name = re.sub(r'\*$', '-s', name)
        # Other asterisks become t
        name = re.sub(r'\*', 't', name)
        # Plus signs become p
        name = re.sub(r'\+', 'p', name)

        # Remove all except alphanumeric and # (for replicates)
        # Keep # but replace other non-alphanumeric chars (including spaces) with dash
        name = re.sub(r'[^\w#]', '-', name)

        # Collapse multiple dashes
        name = re.sub(r'-+', '-', name)

        # Remove leading dash
        name = re.sub(r'^-', '', name)

        # Remove trailing dashes
        name = re.sub(r'-*$', '', name)

        cleaned.append(name)

    # Make names unique by appending #1, #2, etc. for duplicates
    # (similar to R's make.unique function)
    seen = {}
    result = []
    for name in cleaned:
        if name in seen:
            seen[name] += 1
            result.append(f"{name}#{seen[name]}")
        else:
            seen[name] = 0
            result.append(name)

    # Return in same format as input
    if is_single:
        return result[0]
    return result
