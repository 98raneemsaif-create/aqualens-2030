"""Verify the approved PDF-only amendment in Airflow's active Python."""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

import pypdf
import pymupdf

assert sys.version_info[:2] == (3, 11)
assert pypdf.__version__ == "6.17.0"
assert importlib.metadata.version("PyMuPDF") == "1.28.2"
pins = {}
for line in Path("requirements/runtime.lock").read_text().splitlines():
    if line.strip() and not line.startswith("#"):
        name, version = line.split("==")
        actual = importlib.metadata.version(name)
        assert actual == version, (name, actual, version)
        pins[name] = actual
assert pins["apache-airflow"] == "3.3.1"
subprocess.run([sys.executable, "-m", "pip", "check"], check=True)
print(json.dumps(dict(python=sys.version, executable=sys.executable,
                      airflow=importlib.metadata.version("apache-airflow"),
                      pypdf=pypdf.__version__, pymupdf=pymupdf.VersionBind, verified_pin_count=len(pins),
                      pins=pins, gemini_key_present=bool(os.getenv("GEMINI_API_KEY"))), indent=2))
