# Agent Instructions

## Project Overview

`twobitreader` is a small pure-Python package for reading UCSC `.2bit` genome files.
The main implementation is in `twobitreader/__init__.py`, with CLI entry points in
`twobitreader/__main__.py` and download helpers in `twobitreader/download.py`.

## Development Notes

- Keep changes focused and compatible with the supported Python versions in
  `pyproject.toml`.
- Preserve the existing public API unless a change explicitly requires an API
  update.
- Be careful with binary `.2bit` parsing logic and coordinate behavior; prefer
  adding or updating tests for parser, slicing, masking, and byte-order changes.
- Avoid committing generated build artifacts such as `build/`, `dist/`,
  `*.egg-info/`, `__pycache__/`, and `*.pyc`.

## Useful Commands

- Full test suite: `python3 -m unittest discover -s tests`
- Smoke test: `python3 test_package.py`
- Development install: `pip install -e .`
- Build package: `python3 -m build`

The Makefile currently uses `python` for some targets. In environments where
`python` is not available, run the equivalent command with `python3`.
