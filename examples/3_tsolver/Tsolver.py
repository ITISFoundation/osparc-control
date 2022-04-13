import time

import matplotlib.pyplot as plt
import numpy as np

from communication import Transmitter

from osparc_control import CommandManifest
from osparc_control import CommandParameter
from osparc_control import CommandType
from osparc_control import PairedTransmitter


class TSolver:
    def __init__(
        self, dx, n, Tinit, dt, Tsource, k, sourcescale, heatcapacity, tend, transmitter
    ):
        self.T = Tinit
        self.t = 0
        self.dx = dx
        self.n = n
        self.Tinit = Tinit
        self.dt = dt
        self.Tsource = Tsource
        self.k = k
        self.sourcescale = sourcescale
        self.heatcapacity = heatcapacity
        self.tend = tend
        self.transmitter = transmitter

    def run(self):
        transmitter.wait_for_start_signal()
        # self.record(self.t) # Duplicate: controller sends instruction for this
        # self.apply_set(self.t) # Duplicate: controller sends instruction for this

        while self.t < self.tend:
            print(f"Simulation time is {round(self.t,2)}")
            self.record(self.t)
            transmitter.wait_if_necessary(self.t)
            self.apply_set(self.t)
            n = self.n
            diffusion = (
                self.k
                / (self.dx * self.dx)
                * (
                    self.T[: n - 2, 1 : n - 1]
                    + self.T[1 : n - 1, : n - 2]
                    + self.T[2:n, 1 : n - 1]
                    + self.T[1 : n - 1, 2:n]
                    - 4 * self.T[1 : n - 1, 1 : n - 1]
                )
            )
            self.T[1 : n - 1, 1 : n - 1] = self.T[1 : n - 1, 1 : n - 1] + self.dt * (
                self.sourcescale * self.Tsource + diffusion
            )
            self.t = self.t + self.dt

        self.transmitter.finish()
        return self.T

    def wait_for_start_signal(self):
        while not self.transmitter.startsignal:
            time.sleep(0.05)
            self.transmitter.sync()
        self.transmitter.release()

    def record(self, t):
        entry = transmitter.get_record_entry(t)
        if entry[0]:
            recindex, (name, params) = entry
            if name == "Tpoint":
                self.transmitter.records[recindex].append(
                    (t, self.T[params[0], params[1]])
                )
            elif name == "Tvol":
                self.transmitter.records[recindex].append(
                    (t, self.T[params[0] : params[2], params[1] : params[3]])
                )

    def apply_set(self, t):
        entry = transmitter.get_set_entry(t)
        if entry:
            (setname, setval) = entry
            if setname == "Tsource":
                if setval.shape == Tsource.shape:
                    self.Tsource = setval
            elif setname == "SARsource":
                if setval.shape == Tsource.shape:
                    self.Tsource = setval / self.heatcapacity
            elif setname == "sourcescale":
                self.sourcescale = setval
            elif setname == "tend":
                self.tend = setval

    """ # Now uses transmitter finish()
    def finish(self):
        self.record(float("inf"))
        self.transmitter.finish()
        #self.transmitter.endsignal=True; #make function for this and the next line
        #self.transmitter.pause() # what happens if the transmitter is in the middle of executing the wait_for_pause; how about release synchronization
    """


def plot(out):
    fig, ax = plt.subplots()
    ax.set_aspect("equal")
    im = ax.imshow(out)
    fig.colorbar(im)
    fig.savefig("tsolver_plot.png")


if __name__ == "__main__":
    command_instruct = CommandManifest(
        action="command_instruct",
        description="Execute Instructions",
        params=[
            CommandParameter(
                name="instructions", description="Instructions for execution."
            )
        ],
        command_type=CommandType.WITHOUT_REPLY,
    )

    command_retrieve = CommandManifest(
        action="command_retrieve",
        description="gets state",
        params=[],
        command_type=CommandType.WITHOUT_REPLY,
    )

    control_interface = PairedTransmitter(
        remote_host="localhost",
        exposed_commands=[command_instruct, command_retrieve],
        remote_port=1234,
        listen_port=1235,
    )

    with control_interface:
        transmitter = Transmitter(control_interface, "RESPONDER")

        transmitter.canbegotten = ["Tpoint", "Tvol"]
        transmitter.canbeset = ["Tsource", "SARsource", "k", "sourcescale", "tend"]

        # Define initial conditions
        n = 20
        t_start = np.zeros((n, n), float)
        dt = 0.1
        thermo_source = np.ones((n - 2, n - 2), float)
        dx = 1
        k = 1
        heat_capacity = 10
        sourcescale = 1
        t_end = 500

        solver = TSolver(
            dx,
            n,
            t_start,
            dt,
            thermo_source,
            k,
            sourcescale,
            heat_capacity,
            t_end,
            transmitter,
        )

        out = solver.run()
        print(f"Temperature value at time {t_end} is {out[10,10]}")
        time.sleep(1)
        plot(out)
