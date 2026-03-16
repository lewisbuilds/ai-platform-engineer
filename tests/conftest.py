"""Pytest bootstrap configuration for src layout."""

from pathlib import Path
import sys


SRC_PATH = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))
