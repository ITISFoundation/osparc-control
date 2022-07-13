import random
import time

from osparc_control import CommandManifest
from osparc_control import CommandParameter
from osparc_control import CommandType
from osparc_control import PairedTransmitter


# declare some commands to which a reply can be provided
RANDOM_IN_RANGE_MANIFEST = CommandManifest(
    action="random_in_range",
    description="gets the time",
    params=[
        CommandParameter(name="a", description="lower bound for random numbers"),
        CommandParameter(name="b", description="upper bound for random numbers"),
    ],
    command_type=CommandType.WITH_IMMEDIATE_REPLY,
)


def _process_commands(paired_transmitter: PairedTransmitter) -> None:
    for command in paired_transmitter.get_incoming_requests():
        # for each command react to it
        if command.action == RANDOM_IN_RANGE_MANIFEST.action:
            random_int = random.randint(  # noqa: S311
                command.params["a"], command.params["b"]
            )
            print(f"Replying to {command.action} with {random_int}")
            paired_transmitter.reply_to_command(
                request_id=command.request_id, payload=random_int
            )


def main() -> None:
    # initialization of paired_transmitter
    paired_transmitter = PairedTransmitter(
        remote_host="localhost",
        exposed_commands=[RANDOM_IN_RANGE_MANIFEST],
        remote_port=2346,
        listen_port=2345,
    )
    paired_transmitter.start_background_sync()

    # this loop will never exit and continue to reply to requests
    while True:
        # custom application logic goes here

        # whenever the application has some free time it can check for incoming requests
        # below method will fetch all commands and reply to the ones defined
        _process_commands(paired_transmitter)

        # sleep a bit between attempts of polling for new commands to process
        # NOTE: this can be removed if the application logic is not very fast
        # reduce sleep interval if faster response time is required
        time.sleep(0.1)

    # if the application can exit the above loop then the close
    # background sync process by uncommenting below line
    # paired_transmitter.stop_background_sync()


if __name__ == "__main__":
    main()
