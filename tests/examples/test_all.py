import itertools
from pathlib import Path
from subprocess import PIPE  # noqa: S404
from subprocess import Popen  # noqa: S404
from subprocess import STDOUT  # noqa: S404
from time import sleep
from typing import List

import pytest


DELAY_PRCESS_START_S: float = 1.0
WAIT_BETWEEN_CHECKS_S: float = 0.3

# FIXTURES


@pytest.fixture
def example_1_simple_path(examples_path: Path) -> Path:
    path = (examples_path / "1_simple").resolve()
    assert path.exists()
    return path


@pytest.fixture
def example_2_base_time_add_path(examples_path: Path) -> Path:
    path = (examples_path / "2_base_time_add").resolve()
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
        processes = []
        for x in permutation:
            process = Popen(  # noqa: S607
                ["python", f"{x}"], shell=True, stdout=PIPE, stderr=STDOUT  # noqa: S602
            )
            sleep(DELAY_PRCESS_START_S)
            processes.append(process)

        # wait for processes to finish
        continue_running = True
        while continue_running:
            continue_running = all(
                process.returncode is not None for process in processes
            )
            sleep(WAIT_BETWEEN_CHECKS_S)

        # ensure all processes finished successfully
        for process in processes:
            stdout, _ = process.communicate()
            assert process.returncode == 0, stdout.decode()


# TESTS


def test_example_1_simple_runs(example_1_simple_path: Path) -> None:
    replier_path = example_1_simple_path / "replier.py"
    requester_path = example_1_simple_path / "requester.py"

    assert_run_in_parallel([replier_path, requester_path])


def test_example_2_base_time_add_runs(example_2_base_time_add_path: Path) -> None:
    controller_path = example_2_base_time_add_path / "controller.py"
    solver_path = example_2_base_time_add_path / "solver.py"

    assert_run_in_parallel([controller_path, solver_path])
