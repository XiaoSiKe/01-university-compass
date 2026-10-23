#!/usr/bin/env python3
"""Compatibility entry point; historical evidence remains immutable.

Runs the current version through the shared runner. --output must be new/empty;
without it the runner creates a unique run directory under the current version.
"""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[2] / "run_discovery.py"), run_name="__main__")
