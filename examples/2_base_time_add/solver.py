from time import sleep

from osparc_control import CommandManifest
from osparc_control import CommandParameter
from osparc_control import CommandRequest
from osparc_control import CommandType
from osparc_control import PairedTransmitter

# Define exposed commands by this service.
# Each command can be of 3 separate types.

# The requester is expected to poll for the results of this command.
# The results will be delivered as soon as possible and stored
# on the requester's side until he is ready to use it.
# NOTE: when handling this command a respone should always be provided.
COMMAND_ADD = CommandManifest(
    action="add_internal_time",
    description="adds internal time to a provided paramter",
    params=[
        CommandParameter(name="a", description="param to add to internal time"),
    ],
    command_type=CommandType.WITH_DELAYED_REPLY,
)

# The requester will be blocked until the result to this comand is delivered.
# NOTE: when handling this command a respone should always be provided.
# NOTE: the requester waits with a timeout which has to be proportional to
# how much time it takes for this command to be processed
COMMAND_GET_TIME = CommandManifest(
    action="get_time",
    description="gets the time",
    params=[],
    command_type=CommandType.WITH_IMMEDIATE_REPLY,
)

# The requester expects no reply to this command.
# NOTE: when handling this command a reply must NOT be provided.
COMMAND_CLOSE_SOLVER = CommandManifest(
    action="close_solver",
    description="prints the status of the solver",
    params=[],
    command_type=CommandType.WITHOUT_REPLY,
)


def handle_inputs(time_solver: "TimeSolver", request: CommandRequest) -> None:
    """
    Handle incoming requests agains declared commands
    """
    if request.action == COMMAND_ADD.action:
        sum_result = time_solver._add(**request.params)
        time_solver.paired_transmitter.reply_to_command(
            request_id=request.request_id, payload=sum_result
        )
        return

    if request.action == COMMAND_GET_TIME.action:
        time_solver.paired_transmitter.reply_to_command(
            request_id=request.request_id, payload=time_solver.time
        )
        return

    if request.action == COMMAND_CLOSE_SOLVER.action:
        print(f"Quitting solver: {time_solver}")
        # signal solver loop to stop
        time_solver.can_continue = False
        return


class TimeSolver:
    def __init__(
        self, initial_time: float, paired_transmitter: PairedTransmitter
    ) -> None:
        self.time = initial_time
        self.paired_transmitter = paired_transmitter

        # internal time tick
        self.sleep_internal: float = 0.1
        self.can_continue: bool = True

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} time={self.time}, "
            f"sleep_interval={self.sleep_internal}>"
        )

    def _add(self, a: float) -> float:
        return self.time + a

    def run(self) -> None:
        """main loop of the solver"""
        while self.can_continue:
            # process incoming requests from remote
            for request in self.paired_transmitter.get_incoming_requests():
                handle_inputs(time_solver=self, request=request)

            # solver internal processing
            self.time += 1
            sleep(self.sleep_internal)


def main() -> None:
    paired_transmitter = PairedTransmitter(
        remote_host="localhost",
        exposed_commands=[COMMAND_ADD, COMMAND_GET_TIME, COMMAND_CLOSE_SOLVER],
        remote_port=1235,
        listen_port=1234,
    )

    with paired_transmitter:
        time_solver = TimeSolver(initial_time=0, paired_transmitter=paired_transmitter)
        time_solver.run()

    print("finished")


if __name__ == "__main__":
    main()
