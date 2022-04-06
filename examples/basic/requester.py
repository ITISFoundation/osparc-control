from osparc_control import PairedTransmitter

paired_transmitter = PairedTransmitter(
    remote_host="localhost", exposed_commands=[], remote_port=2345, listen_port=2346
)

paired_transmitter.start_background_sync()

random_int = paired_transmitter.request_with_immediate_reply(
    "random_in_range", timeout=10.0, params={"a": 1, "b": 10}
)
print(random_int)
assert 1 <= random_int <= 10  # noqa: S101

paired_transmitter.stop_background_sync()
