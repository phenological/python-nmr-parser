nmr-parser Documentation
========================

Python package for parsing NMR IVDr data from Bruker instruments.

This is a Python migration of the R package ``nmr.parser`` (v0.3.4), preserving
all functionality while adopting Python best practices.

Quick Start
-----------

.. code-block:: python

   from nmr_parser import read_experiment

   # Read complete experiment
   exp = read_experiment("data/HB-COVID0001/10")

   # Access data
   print(exp['acqus'])    # Acquisition parameters
   print(exp['spec'])     # Spectrum data
   print(exp['quant'])    # Quantification results

Installation
------------

.. code-block:: bash

   pip install nmr-parser

API Reference
-------------

Core Functions
~~~~~~~~~~~~~~

.. autosummary::
   :toctree: _autosummary
   :recursive:

   nmr_parser.read_experiment
   nmr_parser.read_spectrum
   nmr_parser.read_param
   nmr_parser.read_params
   nmr_parser.scan_folder

XML Parsers
~~~~~~~~~~~

.. autosummary::
   :toctree: _autosummary
   :recursive:

   nmr_parser.read_quant
   nmr_parser.read_lipo
   nmr_parser.read_qc
   nmr_parser.read_pacs
   nmr_parser.read_eretic
   nmr_parser.read_title

Processing Utilities
~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: _autosummary
   :recursive:

   nmr_parser.clean_names
   nmr_parser.extend_lipo
   nmr_parser.extend_lipo_value

Reference Tables
~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: _autosummary
   :recursive:

   nmr_parser.get_lipo_table
   nmr_parser.get_qc_table
   nmr_parser.get_pacs_table
   nmr_parser.get_sm_table

Module Documentation
~~~~~~~~~~~~~~~~~~~~

Core Module
^^^^^^^^^^^

.. automodule:: nmr_parser.core.experiment
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. automodule:: nmr_parser.core.spectrum
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. automodule:: nmr_parser.core.parameters
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. automodule:: nmr_parser.core.folders
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

XML Parsers Module
^^^^^^^^^^^^^^^^^^

.. automodule:: nmr_parser.xml_parsers.quantification
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. automodule:: nmr_parser.xml_parsers.lipoproteins
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. automodule:: nmr_parser.xml_parsers.quality_control
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. automodule:: nmr_parser.xml_parsers.pacs
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. automodule:: nmr_parser.xml_parsers.eretic
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. automodule:: nmr_parser.xml_parsers.title
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Processing Module
^^^^^^^^^^^^^^^^^

.. automodule:: nmr_parser.processing.lipoprotein_calc
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. automodule:: nmr_parser.processing.utils
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Reference Module
^^^^^^^^^^^^^^^^

.. automodule:: nmr_parser.reference.tables
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
