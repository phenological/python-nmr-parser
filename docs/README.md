# nmr-parser Documentation

This directory contains Sphinx documentation for the nmr-parser package.

## Building Documentation

### Prerequisites

Install Sphinx and theme:
```bash
uv add --dev sphinx sphinx-rtd-theme
```

### Build HTML docs

```bash
cd docs/
make html
```

Or using uv:
```bash
uv run sphinx-build -b html docs/ docs/_build/html
```

### View Documentation

Open in browser:
```bash
open _build/html/index.html  # macOS
xdg-open _build/html/index.html  # Linux
```

### Clean Build

```bash
make clean
```

## Documentation Format

The documentation uses:
- **Sphinx** - Documentation generator
- **NumPy docstring format** - Structured docstrings in code
- **reStructuredText (.rst)** - Documentation markup
- **Read the Docs theme** - Professional appearance

## Auto-generating API docs

Sphinx automatically extracts documentation from docstrings in the code using the `autodoc` extension.

### Example docstring (NumPy format):

```python
def read_param(file: Path, param: str) -> Optional[str]:
    """
    Read parameter from Bruker file.

    Parameters
    ----------
    file : Path
        Path to parameter file
    param : str
        Parameter name to extract

    Returns
    -------
    str or None
        Parameter value or None if not found

    Examples
    --------
    >>> read_param('acqus', 'PULPROG')
    'noesygppr1d'
    """
```

## Publishing Documentation

### Option 1: Read the Docs (Recommended)

1. Create account at https://readthedocs.org
2. Connect GitHub repository
3. Docs build automatically on each commit

### Option 2: GitHub Pages

```bash
# Build docs
make html

# Copy to docs branch
git checkout -b gh-pages
cp -r _build/html/* .
git add .
git commit -m "Update docs"
git push origin gh-pages
```

Enable GitHub Pages in repository settings → Pages → Source: gh-pages

## Sphinx Extensions Used

- **autodoc** - Auto-generate docs from docstrings
- **napoleon** - Support NumPy/Google docstrings
- **viewcode** - Link to source code
- **intersphinx** - Link to pandas, numpy, scipy docs
- **autosummary** - Generate API summary tables

## Customization

Edit `conf.py` to customize:
- Theme and colors
- Extensions
- Project metadata
- Napoleon settings (docstring format)
