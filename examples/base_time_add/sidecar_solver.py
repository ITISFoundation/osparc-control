from osparc_control import CommandManifest
from osparc_control import CommandParameter
from osparc_control import CommnadType
from osparc_control import ControlInterface


command_add = CommandManifest(
    action="add_internal_time",
    description="adds internal time to a provided paramter",
    params=[
        CommandParameter(name="a", description="param to add to internal time"),
    ],
    command_type=CommnadType.WITH_DELAYED_REPLY,
)

command_get_time = CommandManifest(
    action="get_time",
    description="gets the time",
    params=[],
    command_type=CommnadType.WITH_IMMEDIATE_REPLY,
)

command_print_solver_status = CommandManifest(
    action="print_status",
    description="prints the status of the solver",
    params=[],
    command_type=CommnadType.WITHOUT_REPLY,
)

command_get_random_in_range = CommandManifest(
    action="random_in_range",
    description="gives_random_number_in_range",
    params=[
        CommandParameter(name="a", description="lower bound of the range"),
        CommandParameter(name="b", description="upper bound of the range")
    ],
    command_type=CommnadType.WITH_IMMEDIATE_REPLY,
)


control_interface = ControlInterface(
    remote_host="localhost",
    exposed_interface=[command_add, command_get_time, command_print_solver_status, command_get_random_in_range],
    remote_port=1235,
    listen_port=1234,
)
