# About

This example consists of a `time_solver`. Which can add, the current time by a provided value.


# Usage

In one terminal run `sidecar_controller.py`.
In a second terminal run `time_solver.py`. It will load data from the `sidecar_solver.py` to use when communicating with the `sidecar_controller.py`


# In this example

Only the `solver` exposes an interface that can be queried. The `controller` does not have an exposed interface.
