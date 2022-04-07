import sys
from pathlib import Path

import pytest


@pytest.fixture
def repo_folder() -> Path:
    here = Path(sys.argv[0] if __name__ == "__main__" else __file__).resolve().parent
    return (here / "..").resolve()


@pytest.fixture
def examples_path(repo_folder: Path) -> Path:
    path = repo_folder / "examples"
    assert path.exists()
    return path
