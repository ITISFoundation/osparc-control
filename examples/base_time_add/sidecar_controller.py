from osparc_control import ControlInterface


control_interface = ControlInterface(
    remote_host="localhost", exposed_interface=[], remote_port=1234, listen_port=1235
)
control_interface.start_background_sync()

# add_internal_time

add_params = {"a": 10}
print("Will add ", add_params)
request_id = control_interface.request_with_delayed_reply(
    "add_internal_time", params=add_params
)

has_result = False
result = None
while not has_result:
    has_result, result = control_interface.check_for_reply(request_id=request_id)

print("result of addition", result)

# get_time

print("getting solver time")
solver_time = control_interface.request_with_immediate_reply("get_time", timeout=1.0)
random_int = control_interface.request_with_immediate_reply(
    "random_in_range", timeout=1.0, params={"a": 1, "b": 3}
)
print("solver time", solver_time)

print("sending command to print internal status")
control_interface.request_without_reply("print_status")


control_interface.stop_background_sync()
