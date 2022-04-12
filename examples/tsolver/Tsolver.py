import time
from osparc_control import CommandManifest, CommandParameter, CommandType, PairedTransmitter

import numpy as np
import matplotlib.pyplot as plt

from communication import SideCar

class TSolver:
    def __init__(self, dx, n, Tinit, dt, Tsource, k, sourcescale, heatcapacity, tend, sidecar):
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
        self.sidecar = sidecar

    def run(self):
        sidecar.wait_for_start_signal()
        #self.record(self.t) # Duplicate: controller sends instruction for this
        #self.apply_set(self.t) # Duplicate: controller sends instruction for this
 
        while self.t<self.tend:
            print(f"Simulation time is {round(self.t,2)}")
            self.record(self.t)
            sidecar.wait_if_necessary(self.t)
            self.apply_set(self.t)  
            n=self.n
            diffusion=self.k/(self.dx*self.dx) * (self.T[:n-2,1:n-1]+self.T[1:n-1,:n-2]+self.T[2:n,1:n-1]+self.T[1:n-1,2:n]-4*self.T[1:n-1,1:n-1])
            self.T[1:n-1,1:n-1]=self.T[1:n-1,1:n-1]+self.dt*(self.sourcescale*self.Tsource+diffusion)
            self.t=self.t+self.dt

        self.sidecar.finish()
        return self.T

    """ # Now uses sidecar finish()
    def finish(self):
        self.record(float("inf"))
        self.sidecar.finish()
        #self.sidecar.endsignal=True; #make function for this and the next line
        #self.sidecar.pause() # what happens if the sidecar is in the middle of executing the wait_for_pause; how about release synchronization
    """

    def record(self,t):
        entry = sidecar.get_record_entry(t) # Check if a record request is present
        if entry:
            _, recindex, (name, params) = entry
            if name=='Tpoint':
                self.sidecar.records[recindex].append((t,self.T[params[0],params[1]]))
            elif name=='Tvol':
                self.sidecar.records[recindex].append((t,self.T[params[0]:params[2],params[1]:params[3]]))

    def apply_set(self,t):
        entry = sidecar.get_set_entry(t) # Check if a request to set a value is present
        if entry:
            _, _, (setname, setval) = entry
            if setname =='Tsource':
                if setval.shape==Tsource.shape:
                    self.Tsource=setval
            elif setname=='SARsource':
                if setval.shape==Tsource.shape:
                    self.Tsource=setval/self.heatcapacity
            elif setname=='sourcescale':
                self.sourcescale=setval
            elif setname=='tend':
                self.tend=setval

def plot(out):
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    im = ax.imshow(out)
    fig.colorbar(im)
    fig.savefig("tsolver_plot.png")

if __name__ == "__main__":
    command_instruct = CommandManifest(
    action="command_instruct",
    description="Execute Instructions",
    params=[
        CommandParameter(name="instructions", description="Instructions for execution.")
    ],
    command_type=CommandType.WITHOUT_REPLY)

    command_retrieve = CommandManifest(
    action="command_retrieve",
    description="gets state",
    params=[],
    command_type=CommandType.WITHOUT_REPLY)   

    control_interface = PairedTransmitter(
    remote_host="localhost",
    exposed_commands=[command_instruct, command_retrieve],
    remote_port=1234,
    listen_port=1235)

    with control_interface:
        sidecar = SideCar(control_interface, "RESPONDER")
    
        sidecar.canbegotten = ['Tpoint', 'Tvol']
        sidecar.canbeset = ['Tsource', 'SARsource', 'k', 'sourcescale', 'tend']

        n=20; Tinit=np.zeros((n,n), float); dt=0.1; Tsource=np.ones((n-2,n-2), float); dx=1; k=1; sourcescale=1; heatcapacity=10; tend=500
        solver = TSolver(dx, n, Tinit, dt, Tsource, k, sourcescale, heatcapacity, tend, sidecar)

        out = solver.run()
        print(f"Temperature value at time {tend} is {out[10,10]}")
        plot(out)
