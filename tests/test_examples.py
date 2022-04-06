import itertools
import sys
from pathlib import Path
from subprocess import PIPE  # noqa: S404
from subprocess import Popen  # noqa: S404
from subprocess import STDOUT  # noqa: S404
from time import sleep
from typing import List

import pytest

HERE = Path(sys.argv[0] if __name__ == "__main__" else __file__).resolve().parent


# FIXTURES


@pytest.fixture
def path_1_simple() -> Path:
    path = (HERE / ".." / "examples" / "1_simple").resolve()
    assert path.exists()
    return path


@pytest.fixture
def path_2_base_time_add() -> Path:
    path = (HERE / ".." / "examples" / "2_base_time_add").resolve()
    assert path.exists()
    return path


# UTILS


def assert_run_in_parallel(scrips_to_run: List[Path]) -> None:
    # check all exist before running
    for script_to_run in scrips_to_run:
        assert script_to_run.exists()

    for permutation in itertools.permutations(scrips_to_run):
        # run provided scripts
        print(f"Running permutation {permutation}")
        processes = [
            Popen(  # noqa: S607
                ["python", f"{x}"], shell=True, stdout=PIPE, stderr=STDOUT  # noqa: S602
            )
            for x in permutation
        ]

        # wait for processes to finish
        continue_running = True
        while continue_running:
            continue_running = all(
                [process.returncode is not None for process in processes]
            )
            sleep(0.3)

        # ensure all processes finished successfully
        for process in processes:
            stdout, _ = process.communicate()
            assert process.returncode == 0, stdout.decode()


# TESTS


def test_example_1_simple_runs(path_1_simple: Path) -> None:
    replier_path = path_1_simple / "replier.py"
    requester_path = path_1_simple / "requester.py"

    assert_run_in_parallel([replier_path, requester_path])


def test_example_2_base_time_add_runs(path_2_base_time_add: Path) -> None:
    controller_path = path_2_base_time_add / "controller.py"
    solver_path = path_2_base_time_add / "solver.py"

    assert_run_in_parallel([controller_path, solver_path])
