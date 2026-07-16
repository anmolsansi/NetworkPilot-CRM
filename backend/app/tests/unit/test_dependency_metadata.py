import tomllib
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[3]


def test_requirements_match_pyproject_runtime_dependencies():
    """Keep Render's requirements install aligned with package metadata."""
    pyproject = tomllib.loads((BACKEND_ROOT / "pyproject.toml").read_text())
    package_dependencies = set(pyproject["project"]["dependencies"])
    requirements_dependencies = {
        line.strip()
        for line in (BACKEND_ROOT / "requirements.txt").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert requirements_dependencies == package_dependencies, (
        "Runtime dependency declarations differ. "
        f"Only in requirements.txt: {sorted(requirements_dependencies - package_dependencies)}; "
        f"only in pyproject.toml: {sorted(package_dependencies - requirements_dependencies)}"
    )
