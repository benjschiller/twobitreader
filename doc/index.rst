.. twobitreader documentation master file, created by
   sphinx-quickstart on Wed Feb 29 14:17:11 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

twobitreader: a fast python package for reading .2bit files
===========================================================

Licensed under Perl Artistic License 2.0

No warranty is provided, express or implied


==========================
Module-level documentation
==========================

.. toctree::
   :maxdepth: 2

   twobitreader
   download

====================
Run module as script
====================
twobitreader
------------
twobitreader can be imported as a module within python or run as a script from the command line, for example

``$ python -m twobitreader example.2bit < example.bed``

When run in this mode, twobitreader accepts only one argument, the filename of the .2bit genome, and reads coordinates from stdin in `BED format <http://genome.ucsc.edu/FAQ/FAQformat#format1>`_

Output is given in FASTA format to stdout (warnings and errors are issued on stderr)

twobitreader.download
---------------------
twobitreader.download can also be run as a script to fetch a genome by name, for example

``$ python -m twobitreader.download hg19``

which will save hg19.2bit to your current directory

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

