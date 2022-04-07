import random
import time

from osparc_control import CommandManifest
from osparc_control import CommandParameter
from osparc_control import CommandType
from osparc_control import PairedTransmitter


# declare some commands to which a reply can be provided
random_in_range_manifest = CommandManifest(
    action="random_in_range",
    description="gets the time",
    params=[
        CommandParameter(name="a", description="lower bound for random numbers"),
        CommandParameter(name="b", description="upper bound for random numbers"),
    ],
    command_type=CommandType.WITH_IMMEDIATE_REPLY,
)

paired_transmitter = PairedTransmitter(
    remote_host="localhost",
    exposed_commands=[random_in_range_manifest],
    remote_port=2346,
    listen_port=2345,
)
paired_transmitter.start_background_sync()

wait_for_requests = True
while wait_for_requests:
    for command in paired_transmitter.get_incoming_requests():
        if command.action == random_in_range_manifest.action:
            random_int = random.randint(  # noqa: S311
                command.params["a"], command.params["b"]
            )
            paired_transmitter.reply_to_command(
                request_id=command.request_id, payload=random_int
            )
        wait_for_requests = False

# allow for message to be delivered
time.sleep(0.3)

paired_transmitter.stop_background_sync()
