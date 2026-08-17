"""
Smoke test: every .lu file in examples/ should run to completion
(exit code 0) with no dependencies beyond the standard library. This
is what CI runs on every push to catch a library change that breaks
one of the shipped examples.
"""
import glob
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUMEN_PY = os.path.join(REPO_ROOT, "lumen.py")
EXAMPLES = sorted(glob.glob(os.path.join(REPO_ROOT, "examples", "*.lu")))


@pytest.mark.parametrize("path", EXAMPLES, ids=[os.path.basename(p) for p in EXAMPLES])
def test_example_runs_cleanly(path):
    result = subprocess.run(
        [sys.executable, LUMEN_PY, path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, (
        f"{os.path.basename(path)} exited {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
