
from osparc_control import CommandManifest, CommandParameter, CommandType, PairedTransmitter

import time
import numpy as np 
import matplotlib.pyplot as plt

from Tsolver_sidecar import SideCar

class Controller:
    def __init__(self,tweakparam_key, initval, regulationparam_key, regulationparam_otherparams, setpoint, iteration_time, KP, KI, KD, controlled):
        self.iteration_time = iteration_time
        self.tweakparam_key = tweakparam_key
        self.initval = initval
        self.regulationparam_key = regulationparam_key
        self.regulationparam_otherparams = regulationparam_otherparams
        self.setpoint = setpoint
        self.KP = KP
        self.KI = KI
        self.KD = KD
        self.controlled = controlled
        self.errors=[]
        self.sets=[]
        self.controlledvals=[]
        
    def run(self):
        error_prior = 0
        integral_prior = 0
        bias = 0 
        
        self.t = self.iteration_time
        
        recindex=self.controlled.record(self.regulationparam_key, self.iteration_time, self.regulationparam_otherparams)
        waittime=self.iteration_time
        waitindex=self.controlled.wait_for_me_at(waittime)
        newset=self.initval
        self.controlled.setnow(self.tweakparam_key, newset)
        self.controlled.start()
        self.errors=[]
        self.sets=[]
        self.controlledvals=[]
        lasttime=0
        
        while not self.controlled.endsignal:
            #self.controlled.wait_for_time(waittime,1000)
            self.controlled.sync() # Maybe we can get rid of wait_for_time
            get1=self.controlled.get(recindex)
            print(f"Controller: time is {waittime}")
            print(recindex)
            print(self.controlled.records)
            print(get1)
            if not get1:
                error1 = error_prior
                timestep=self.t-lasttime
                lasttime=self.t
                print('problem?')
            else:
                error1 = self.setpoint - get1[0][1]
                timestep=get1[0][0]-lasttime
                lasttime=get1[0][0]
            self.errors.append(error1)
            self.controlledvals.append(get1[0][1])
            integral = integral_prior + error1 * timestep
            derivative = (error1 - error_prior) / timestep
            output=self.KP*error1 + self.KI*integral + self.KD*derivative + bias
            newset=newset+output 

            self.controlled.setnow(self.tweakparam_key, newset)
            self.sets.append(newset)
            error_prior = error1
            integral_prior = integral
            waittime=waittime+self.iteration_time
            recindex=self.controlled.record(self.regulationparam_key,waittime,self.regulationparam_otherparams)
            waitindex=self.controlled.continue_until(waittime,waitindex)
            print(self.controlled.finished())
        return {"set value":self.sets, "errors": self.errors, "controlled value": self.controlledvals}

def plot(out_dict):
    fig, ax = plt.subplots(3)
    for i, (key, val) in enumerate(out_dict.items()):
        ax[i].plot(val, marker="o")
        ax[i].set_title(key)
    fig.savefig("controller_plot.png")

if __name__ == "__main__":
    command_data = CommandManifest(
    action="command_data",
    description="receive some stuff",
    params=[
        CommandParameter(name='t', description="time"),
        CommandParameter(name='endsignal', description="end?"),
        CommandParameter(name='paused', description="is paused"), 
        CommandParameter(name='records', description="some records")
    ],
    command_type=CommandType.WITHOUT_REPLY,
   )

    control_interface = PairedTransmitter(
    remote_host="localhost",
    exposed_commands=[command_data],
    remote_port=1235,
    listen_port=1234,
   )
    control_interface.start_background_sync()
    sidecar = SideCar(control_interface, "REQUESTER")

    controller = Controller('sourcescale', 1, 'Tpoint', [10,10], 4, 10, 0.01, 0.00, 0, sidecar)
    out = controller.run()
    control_interface.stop_background_sync()

    plot(out)



