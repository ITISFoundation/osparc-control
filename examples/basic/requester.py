from osparc_control import ControlInterface

control_interface = ControlInterface(
    remote_host="localhost", exposed_interface=[], remote_port=2345, listen_port=2346
)

control_interface.start_background_sync()

random_int = control_interface.request_with_immediate_reply(
    "random_in_range", timeout=10.0, params={"a": 1, "b": 10}
)
print(random_int)
assert 1 <= random_int <= 10  # noqa: S101

random_int = control_interface.request_with_immediate_reply(
    "random_in_range", timeout=10.0, params={"a": 1, "b": 10}
)
print(random_int)
assert 1 <= random_int <= 10  # noqa: S101

random_int = control_interface.request_with_immediate_reply(
    "random_in_range", timeout=10.0, params={"a": 1, "b": 10}
)
print(random_int)
assert 1 <= random_int <= 10  # noqa: S101

control_interface.stop_background_sync()
