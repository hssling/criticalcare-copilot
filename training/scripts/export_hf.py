"""Thin wrapper around ``hf/publish_model.py``; kept for discoverability
under ``training/scripts/``."""
from __future__ import annotations

import runpy
import sys

if __name__ == "__main__":
    sys.argv[0] = "hf/publish_model.py"
    runpy.run_path("hf/publish_model.py", run_name="__main__")
