"""Native build locks must preserve declared dependencies and Cairo pins."""
from pathlib import Path
import re

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
import pytest


ROOT = Path(__file__).resolve().parents[1]


def requirement_lines(path):
    return [line.strip() for line in path.read_text().replace('\\\n', ' ').splitlines()
            if line.strip() and not line.lstrip().startswith('#')]


@pytest.mark.parametrize('declared', requirement_lines(ROOT / 'requirements-build.in'))
def test_build_lock_preserves_each_declared_requirement(declared):
    requirement = Requirement(declared)
    matches = []
    for line in requirement_lines(ROOT / 'requirements-build.txt'):
        locked = Requirement(line.split(' --hash=', 1)[0].strip())
        if canonicalize_name(locked.name) == canonicalize_name(requirement.name):
            matches.append((locked, line))
    assert len(matches) == 1, f'Build lock must contain exactly one entry for {declared}'
    locked, line = matches[0]
    assert locked.specifier == requirement.specifier
    assert locked.marker == requirement.marker
    assert locked.extras == requirement.extras
    assert re.search(r'--hash=sha256:[a-f0-9]{64}(?:\s|$)', line)


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
