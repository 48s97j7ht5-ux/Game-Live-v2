#!/usr/bin/env python3
"""CLI wrapper. Hair packing lives in factory/hair/pack.py."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "hair" / "pack.py"), run_name="__main__")
