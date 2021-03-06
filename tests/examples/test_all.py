import itertools
from pathlib import Path
from subprocess import PIPE  # noqa: S404
from subprocess import Popen  # noqa: S404
from subprocess import STDOUT  # noqa: S404
from time import sleep
from typing import List

import pip
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


@pytest.fixture
def example_3_tsolver(examples_path: Path) -> Path:
    path = (examples_path / "3_tsolver").resolve()
    assert path.exists()
    return path


@pytest.fixture
def example_4_coupled_solver(examples_path: Path) -> Path:
    path = (examples_path / "4_coupled_solver").resolve()
    assert path.exists()
    return path


# UTILS


def install_dependencies(search_path: Path) -> None:
    requirements_txt = search_path / "requirements.txt"
    if not (requirements_txt.exists() and requirements_txt.is_file()):
        print(f"No requirements found in {search_path.name}")  # pragma: no cover
        return  # pragma: no cover

    print(f"Installing dependencies for {search_path.name}:")
    for dependency in requirements_txt.read_text().split("\n"):
        print(f"- '{dependency}'")
        pip.main(["install", dependency])


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


def test_example_example_3_tsolver(example_3_tsolver: Path) -> None:
    install_dependencies(example_3_tsolver)

    t_solver_path = example_3_tsolver / "Tsolver.py"
    controller_path = example_3_tsolver / "Controller.py"

    assert_run_in_parallel([controller_path, t_solver_path])


def test_4_coupled_solver(example_4_coupled_solver: Path) -> None:
    install_dependencies(example_4_coupled_solver)

    coupler_script_path = example_4_coupled_solver / "coupler_script.py"
    tsolver_script_path = example_4_coupled_solver / "tsolver_script.py"
    em_solver_script_path = example_4_coupled_solver / "EMSolver_script.py"

    assert_run_in_parallel(
        [coupler_script_path, tsolver_script_path, em_solver_script_path]
    )
