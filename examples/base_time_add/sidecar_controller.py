from osparc_control import PairedTransmitter

paired_transmitter = PairedTransmitter(
    remote_host="localhost", exposed_commands=[], remote_port=1234, listen_port=1235
)
paired_transmitter.start_background_sync()

# add_internal_time

add_params = {"a": 10}
print("Will add ", add_params)
request_id = paired_transmitter.request_with_delayed_reply(
    "add_internal_time", params=add_params
)

has_result = False
result = None
while not has_result:
    has_result, result = paired_transmitter.check_for_reply(request_id=request_id)

print("result of addition", result)

# get_time

print("getting solver time")
solver_time = paired_transmitter.request_with_immediate_reply("get_time", timeout=1.0)
random_int = paired_transmitter.request_with_immediate_reply(
    "random_in_range", timeout=1.0, params={"a": 1, "b": 3}
)
print("solver time", solver_time)

print("sending command to print internal status")
paired_transmitter.request_without_reply("print_status")


paired_transmitter.stop_background_sync()
