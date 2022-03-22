from time import sleep

from osparc_control import CommandManifest, CommandParameter, CommnadType
from osparc_control.core import ControlInterface
from osparc_control.models import CommandRequest
import numpy as np


class TSolver:
    def __init__(self, dx, n, Tinit, dt, Tsource, k, sourcescale, tend, control_interface):
        self.dx = dx
        self.n = n
        self.Tinit = Tinit
        self.dt = dt
        self.Tsource = Tsource
        self.k = k
        self.sourcescale = sourcescale
        self.tend = tend
        self.control_interface = control_interface
        
        self.T = Tinit
        self.t = 0
           
        # internal time tick
        self.sleep_internal: float = 0.1
        #self.can_continue: bool = True # TODO: should we make this controllable?

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} time={self.time}, "
            f"sleep_interval={self.sleep_internal}>"
        )
    
    def run(self):

        """main loop of the solver"""
        while self.t < self.tend:
            for request in self.control_interface.get_incoming_requests():
                process_requests(self, request)

            diffusion=self.k/(self.dx*self.dx) * (self.T[:self.n-2,1:self.n-1]+self.T[1:self.n-1,:self.n-2]+self.T[2:self.n,1:self.n-1]+self.T[1:self.n-1,2:self.n]-4*self.T[1:self.n-1,1:self.n-1])
            self.T[1:self.n-1,1:self.n-1]=self.T[1:self.n-1,1:self.n-1]+self.dt*(self.sourcescale*self.Tsource+diffusion)
            self.t=self.t+self.dt

            # process internal stuff
            self.t += self.dt
            sleep(self.sleep_internal)

    def record(self, comm_record):
        #while (not control_interface) and (control_interface.get_incoming_requests[-1].time): TODo: do we have to check something here?
        if comm_record.params["record_what"] == "Tpoint":
            rec_x, rec_y = 10,10 # TODO: makes this an argument
            return [self.t, self.T[rec_x,rec_y]]

        #self.sidecar.t=t TODO: do we need this?
    
    def is_finished(self):
        if self.t >= self.tend: #TODO: or it received a stop signal
            return True
        else:
            return False

    def execute_instruction(self, instr_request):
        if instr_request.params["instruction_type"] == "set_now": # TODO implement others and maybe move out of Tsolver class
            if instr_request.params["set_what"] == "sourcescale":
                print(f"Setting sourcescale value to {instr_request.params['set_val']}")
                self.sourcescale = instr_request.params["set_val"]

def define_commands(): # TODO: could be moved to external "config file" and this becomes a reader

    command_record_now = CommandManifest(
    action="record",
    description="Records some variables at current time",
    params=[
        CommandParameter(name="record_what", description="Name of the variable to record"),
        #CommandParameter(name="Tvol", description="upper bound for random numbers"), TODO: implement
    ],
    command_type=CommnadType.WITH_IMMEDIATE_REPLY,
    )

    get_finished_status = CommandManifest(
    action = "is_finished",
    params = [],
    description = "Check if simulation is finished",
    command_type = CommnadType.WITH_IMMEDIATE_REPLY)

    command_exec_instruction = CommandManifest(
        action="execute_instruction",
        description="Applies a command to the solver",
        params =[
            CommandParameter(name="set_what", description="Name of the variable to set"),
            CommandParameter(name="set_val", description="Value to set"),
            CommandParameter(name="instruction_type", description="Type of instruction to execute")
            ],
        command_type = CommnadType.WITHOUT_REPLY
    )
    return [command_record_now, get_finished_status, command_exec_instruction]

def process_requests(T_solver: "TSolver", request: CommandRequest) -> None:
    # process incoming requests from remote
    print("Processing incoming requests...")
    if request.action == "record":
        ret_vals = T_solver.record(request)
        T_solver.control_interface.reply_to_command(
            request_id=request.request_id, payload=ret_vals,
        )
    if request.action == "is_finished":
        ret = T_solver.is_finished()
        T_solver.control_interface.reply_to_command(
            request_id=request.request_id, payload=ret,
        )
    if request.action == "execute_instruction":
        T_solver.execute_instruction(request)


def main() -> None:
    commands = define_commands()
    
    control_interface = ControlInterface(
    remote_host="localhost",
    exposed_interface=commands,
    remote_port=1234,
    listen_port=1235,
)
    control_interface.start_background_sync()

    n=20; Tinit=np.zeros((n,n), float); dt=0.1; Tsource=np.ones((n-2,n-2), float); dx=1; k=1; sourcescale=1; tend=80
    solver = TSolver(dx, n, Tinit, dt, Tsource, k, sourcescale, tend, control_interface=control_interface)
    solver.run()

    control_interface.stop_background_sync()


if __name__ == "__main__":
    main()
