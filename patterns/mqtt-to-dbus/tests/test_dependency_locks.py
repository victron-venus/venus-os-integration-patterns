"""The native preinstallation and runtime solve must select identical Cairo."""
from pathlib import Path
import re


def cairo_requirement(path):
    text = path.read_text().replace('\\\n', ' ')
    return next(line.strip() for line in text.splitlines()
                if line.startswith('pycairo=='))


def test_cairo_preinstallation_matches_runtime_version_and_hashes():
    root = Path(__file__).resolve().parents[1]
    runtime = cairo_requirement(root / 'requirements.txt')
    preinstall = cairo_requirement(root / 'requirements-cairo.txt')
    assert runtime.split()[0] == preinstall.split()[0]
    assert set(re.findall(r'--hash=sha256:([a-f0-9]{64})', runtime)) == set(
        re.findall(r'--hash=sha256:([a-f0-9]{64})', preinstall)
    )
    assert '--hash=sha256:' in runtime
