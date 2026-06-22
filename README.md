# twobitreader

[![CI](https://github.com/benjschiller/twobitreader/actions/workflows/ci.yml/badge.svg)](https://github.com/benjschiller/twobitreader/actions/workflows/ci.yml)
[![Lint](https://github.com/benjschiller/twobitreader/actions/workflows/lint.yml/badge.svg)](https://github.com/benjschiller/twobitreader/actions/workflows/lint.yml)
[![Docs](https://github.com/benjschiller/twobitreader/actions/workflows/docs.yml/badge.svg)](https://github.com/benjschiller/twobitreader/actions/workflows/docs.yml)

`twobitreader` is a small, fast Python package for reading UCSC `.2bit` genome
files. It supports random access by sequence name and genomic interval, making
it useful for pulling slices from large genome files without loading whole
chromosomes into memory.

The package reads `.2bit` files only; it does not write them.

## Performance in v4

Version 4 keeps decoding pure Python while reducing startup cost and speeding up
common slice paths. The main changes are lazy construction of the large
two-byte lookup table, faster N-block lookup with `bisect`, and decoded sequence
buffers backed by plain Python character lists instead of deprecated
`array('u')` buffers.

Benchmarks below compare v4.0.0 with v3.1.8 on Python 3.14.5, using
synthetic 5 Mb `.2bit` files. The v3.1.9 tag has the same reader
implementation as v3.1.8, plus release/CI packaging changes.

![v4 import performance](doc/performance-v4-import.svg)

![v4 slice speedups](doc/performance-v4-slices.svg)

| Benchmark | v3.1.8 | v4.0.0 | Change |
| --- | ---: | ---: | ---: |
| Cold import time | 179.6 ms | 35.6 ms | 5.0x faster |
| Peak import memory | 14.18 MB | 2.22 MB | 6.4x less |
| Plain 1 Mb slice | 135.6 ms | 17.3 ms | 7.8x faster |
| 10 bp slice with 50k N-blocks | 0.749 ms | 0.0026 ms | 290x faster |

## Installation

Install the latest released package from PyPI:

```bash
pip install twobitreader
```

For local development, clone the repository and install it in editable mode:

```bash
git clone https://github.com/benjschiller/twobitreader.git
cd twobitreader
pip install -e ".[dev,docs]"
pre-commit install
```

## Python Usage

Open a `.2bit` file with `TwoBitFile`. It behaves like a dictionary whose keys
are sequence names and whose values are sliceable sequence objects.

```python
from twobitreader import TwoBitFile

with TwoBitFile("hg19.2bit") as genome:
    print(genome.keys())
    print(genome.sequence_sizes()["chr1"])

    sequence = genome["chr1"][100_000:100_050]
    print(sequence)
```

Coordinates follow Python and UCSC BED conventions: they are 0-based and
end-open. For example, `genome["chr1"][10:20]` returns 10 bases.

Converting an entire chromosome to a string works, but can use a lot of memory:

```python
with TwoBitFile("hg19.2bit") as genome:
    chr_m = str(genome["chrM"])
```

## Command-Line Usage

`twobitreader` can also read BED-style intervals from standard input and write
FASTA records to standard output:

```bash
python -m twobitreader genome.2bit < regions.bed > regions.fa
```

Input lines should have at least three whitespace-separated fields:

```text
chrom    start    end
chr1     100000   100050
chr2     250      300
```

Invalid regions are skipped with warnings written to standard error. Intervals
that extend past the end of a sequence are truncated.

## Downloading Genomes

The `twobitreader.download` module can fetch `.2bit` genomes from UCSC:

```bash
python -m twobitreader.download hg19
```

Please follow UCSC's usage guidelines and avoid excessive automated downloads.

## Development

Run the full test suite with:

```bash
python3 -m unittest discover -s tests
```

Run the lightweight package smoke test with:

```bash
python3 test_package.py
```

Build the package with:

```bash
python3 -m build
```

Build the Sphinx documentation with:

```bash
sphinx-build -W --keep-going -b html doc doc/_build/html
```

Run formatting and repository checks with:

```bash
pre-commit run --all-files
```

The Makefile uses `python` in a few targets. If your environment only provides
`python3`, run the equivalent command directly with `python3`.

## License

`twobitreader` is licensed under the Perl Artistic License 2.0. See
[LICENSE.txt](LICENSE.txt) and [COPYRIGHT](COPYRIGHT) for details.

No warranty is provided, express or implied.
