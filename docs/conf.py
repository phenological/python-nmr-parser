"""Sphinx configuration for nmr-parser documentation."""

import os
import sys

# Add source to path
sys.path.insert(0, os.path.abspath('../src'))

# Project information
project = 'nmr-parser'
copyright = '2023-2024, nmr.parser authors'
author = 'Julien Wist, Reika Masuda'
release = '0.4.0'

# Extensions
extensions = [
    'sphinx.ext.autodoc',        # Auto-generate docs from docstrings
    'sphinx.ext.napoleon',       # Support NumPy/Google docstrings
    'sphinx.ext.viewcode',       # Add links to source code
    # 'sphinx.ext.intersphinx',  # Link to other projects (disabled for faster builds)
    'sphinx.ext.autosummary',    # Generate summary tables
]

# Napoleon settings (for NumPy docstrings)
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

autosummary_generate = True

# HTML theme
html_theme = 'sphinx_rtd_theme'

# Intersphinx mapping (link to other docs) - disabled for faster builds
# intersphinx_mapping = {
#     'python': ('https://docs.python.org/3', None),
#     'numpy': ('https://numpy.org/doc/stable/', None),
#     'pandas': ('https://pandas.pydata.org/docs/', None),
#     'scipy': ('https://docs.scipy.org/doc/scipy/', None),
# }
