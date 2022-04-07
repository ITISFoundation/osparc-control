import time
from osparc_control import CommandManifest, CommandParameter, CommnadType, ControlInterface

import numpy as np
import matplotlib.pyplot as plt

from Tsolver_sidecar import SideCar

class TSolver:
    def __init__(self, dx, n, Tinit, dt, Tsource, k, sourcescale, tend, sidecar):
        self.T = Tinit
        self.t = 0
        self.dx = dx
        self.n = n
        self.Tinit = Tinit
        self.dt = dt
        self.Tsource = Tsource
        self.k = k
        self.sourcescale = sourcescale
        self.tend = tend
        self.sidecar = sidecar

    def run(self):
        self.wait_for_start_signal()
        self.record(self.t)
        self.apply_set(self.t)
 
        while self.t<self.tend:
            print(self.t)
            self.record(self.t)
            self.wait_if_necessary(self.t)
            self.apply_set(self.t)  
            n=self.n
            diffusion=self.k/(self.dx*self.dx) * (self.T[:n-2,1:n-1]+self.T[1:n-1,:n-2]+self.T[2:n,1:n-1]+self.T[1:n-1,2:n]-4*self.T[1:n-1,1:n-1])
            self.T[1:n-1,1:n-1]=self.T[1:n-1,1:n-1]+self.dt*(self.sourcescale*self.Tsource+diffusion)
            self.t=self.t+self.dt

        self.finish()
        return self.T
    
    def wait_a_bit(self):
        time.sleep(0.05)
        
    def wait_if_necessary(self,t): #move what is possible into the sidecar
        while self.sidecar.get_wait_status(t):
            print(f"Solver: during wait_if_necessary, records are {self.sidecar.records}")
            print("triggered wait_if_necessary")
            self.wait_a_bit()


    def wait_for_start_signal(self):
        while not self.sidecar.startsignal:
        # while not self.sidecar.started():
            self.wait_a_bit()
            self.sidecar.sync()
        self.sidecar.release()

    def finish(self):
        self.record(float("inf"))
        self.sidecar.finish()
        #self.sidecar.endsignal=True; #make function for this and the next line
        #self.sidecar.pause() # what happens if the sidecar is in the middle of executing the wait_for_pause; how about release synchronization

    def record(self,t):
        while (not self.sidecar.recordqueue.empty()) and self.sidecar.recordqueue.first()[0] <= t:
            pop1=self.sidecar.recordqueue.pop()
            recindex=pop1[1]
            rec1=pop1[2]
            if rec1[0]=='Tpoint':
                self.sidecar.records[recindex].append((t,self.T[rec1[1][0],rec1[1][1]]))
                #print(f"Solver: after recording, records are {self.sidecar.records}")
            elif rec1[0]=='Tvol':
                self.sidecar.records[recindex].append((t,self.T[rec1[1][0]:rec1[1][2],rec1[1][1]:rec1[1][3]]))
        self.sidecar.t=t

    def apply_set(self,t):
        while (not self.sidecar.setqueue.empty()) and self.sidecar.setqueue.first()[0] <= t:
            set1=self.sidecar.setqueue.pop()[2]
            if set1[0]=='Tsource':
                if set1[1].shape==Tsource.shape:
                    self.Tsource=set1[1]
            elif set1[0]=='SARsource':
                if set1[1].shape==Tsource.shape:
                    self.Tsource=set1[1]/heatcapacity
            elif set1[0]=='k':
                if set1[1]>0:
                    self.set_k(set1[1])
            elif set1[0]=='sourcescale':
                self.sourcescale=set1[1]
            elif set1[0]=='tend':
                self.tend=set1[1]

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
    command_type=CommnadType.WITHOUT_REPLY)

    command_retrieve = CommandManifest(
    action="command_retrieve",
    description="gets state",
    params=[],
    command_type=CommnadType.WITHOUT_REPLY)   

    control_interface = ControlInterface(
    remote_host="localhost",
    exposed_interface=[command_instruct, command_retrieve],
    remote_port=1234,
    listen_port=1235)

    control_interface.start_background_sync()
    sidecar = SideCar(control_interface, "RESPONDER")
    sidecar.canbegotten = ['Tpoint', 'Tvol']
    sidecar.canbeset = ['Tsource', 'SARsource', 'k', 'sourcescale', 'tend']

    n=20; Tinit=np.zeros((n,n), float); dt=0.1; Tsource=np.ones((n-2,n-2), float); dx=1; k=1; sourcescale=1; tend=50
    solver = TSolver(dx, n, Tinit, dt, Tsource, k, sourcescale, tend, sidecar)

    out = solver.run()
    
    print(out[10,10])
    
    time.sleep(1)
    control_interface.stop_background_sync()
    plot(out)
