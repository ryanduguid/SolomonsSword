import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import louisgoldberg


ROOT = Path(__file__).resolve().parents[1]


def test_rollback_distribution_points_to_the_maintained_project() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    lockfile = (ROOT / "uv.lock").read_text(encoding="utf-8")
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    package_init = (ROOT / "louisgoldberg" / "__init__.py").read_text(encoding="utf-8")
    cli = (ROOT / "louisgoldberg" / "cli.py").read_text(encoding="utf-8")
    release_notes = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

    assert 'name = "solomons-sword"' in pyproject
    assert 'solomons-sword = "louisgoldberg.cli:main"' in pyproject
    assert 'name = "solomons-sword"' in lockfile
    assert 'name = "louisgoldberg"' not in lockfile
    assert '_dist_version("solomons-sword")' in package_init
    assert 'prog="solomons-sword"' in cli
    assert version("solomons-sword") == louisgoldberg.__version__
    assert not (ROOT / ".github" / "workflows" / "release.yml").exists()
    assert (
        'Homepage = "https://github.com/ryanduguid/australian-accounting/'
        'tree/main/packages/solomons-sword"' in pyproject
    )
    assert (
        'Repository = "https://github.com/ryanduguid/australian-accounting/'
        'tree/main/packages/solomons-sword"' in pyproject
    )
    assert 'Issues = "https://github.com/ryanduguid/australian-accounting/issues"' in pyproject
    assert "**Package lifecycle:** published from Australian Accounting." in readme
    assert "python -m pip install solomons-sword" in readme
    assert "git clone https://github.com/ryanduguid/SolomonsSword.git" not in readme
    assert "`solomons-sword` distribution and command" in readme
    assert "`louisgoldberg` import package" in readme
    assert "solomons-sword s100a-check" in readme
    assert "louisgoldberg s100a-check" not in readme
    assert "releases?q=solomons-sword" in release_notes
    assert "Releases through v0.1.2" in release_notes
    assert (
        "https://github.com/ryanduguid/australian-accounting/security/advisories/new"
        in security
    )
    assert "Do not open a public issue" in security

    help_result = subprocess.run(
        [sys.executable, "-m", "louisgoldberg.cli", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert help_result.returncode == 0
    assert help_result.stdout.startswith("usage: solomons-sword")
