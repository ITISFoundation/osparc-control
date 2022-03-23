from osparc_control import ControlInterface
import numpy as np
import time

class Controller:
    def __init__(self,tweakparam_key, initval, regulationparam_key, regulationparam_otherparams, setpoint, iteration_time, KP, KI, KD, control_interface):
        self.iteration_time = iteration_time
        self.tweakparam_key = tweakparam_key
        self.initval = initval
        self.regulationparam_key = regulationparam_key
        self.regulationparam_otherparams = regulationparam_otherparams
        self.setpoint = setpoint
        self.KP = KP
        self.KI = KI
        self.KD = KD
        self.control_interface = control_interface
        self.errors=[]
        self.sets=[]
        self.controlledvals=[]
    
    def run(self):
        error_prior = 0
        integral_prior = 0
        bias = 0 #TODO: should we move it to main args, with default val?
        
        self.t = self.iteration_time

        self.errors = []
        self.sets = []
        self.controlled_vals = []

        lasttime = 0
    
        self.control_interface.request_with_immediate_reply("start", params=[], timeout=10.0) # Give start signal
        
        #recindex = self.control_interface.request_with_immediate_reply("record", params={"record_what":"Tpoint"}, timeout=10.0)
        waittime = self.iteration_time
        #waitindex = control_interface.request_without_reply(waittime) # waitindex=self.controlled.wait_for_me_at(waittime)

        newset=self.initval
        self.control_interface.request_with_immediate_reply("execute_instruction", 
            params={"set_what": self.tweakparam_key,
            "set_val": newset,
            "instruction_type": "set_now"}, timeout=10.0)  
        
        while not self.is_finished():
            #self.wait_for_time(waittime,1000) #This also calls syncout and syncin -> Do we still need it?
            retval = self.control_interface.request_with_immediate_reply("record", params={"record_what":self.regulationparam_key}, timeout=5.0) #Record the value we want to control
            #retval = self.control_interface.request_with_delay_reply("record", params={"record_what":self.regulationparam_key, "wait_time": waittime})
            if not retval:
                error = error_prior
                timestep = self.t - lasttime
                lasttime = self.t
            else:
                time_solver, Tval = retval
                error = self.setpoint - Tval 
                timestep = time_solver - lasttime
                lasttime = time_solver
            
            #print(f"Time of controller is {lasttime}")
            self.errors.append(error)
            self.controlledvals.append(Tval) #TODO: this will crash if Tval doesn't exist
            integral = integral_prior + error*timestep
            derivative = (error - error_prior) / timestep
            output = self.KP*error + self.KI*integral + self.KD*derivative + bias
            newset = newset + output
            
            self.control_interface.request_with_immediate_reply("execute_instruction", 
                params={"set_what": self.tweakparam_key,
                "set_val": newset,
                "instruction_type": "set_now"}, timeout=0.0)

            self.sets.append(newset)

            error_prior = error
            integral_prior = integral
            waittime = waittime + self.iteration_time
       
            #recindex = control_interface.request_with_immediate_reply("record", params={"record_what":"Tpoint"}, timeout=10.0)
            #waitindex=self.controlled.continue_until(waittime,waitindex)
            print(f"Controlled values are {self.controlledvals}")
            print(f"Errors are {self.errors}")
        return {"controlled value": self.controlled_vals, "error": self.errors, "set value": self.sets}

    def is_finished(self): # Return true is Tsolver has reach tend. TODO: is this correct?
        return self.control_interface.request_with_immediate_reply("is_finished", timeout = 10.0)
    
    def wait_for_time(self,waittime,maxcount):
        while self.t < waittime:
            time.sleep(0.05) 
        if self.t < waittime:
            print("Controller timeout from wait_for_time")

def main() -> None:
    control_interface = ControlInterface(
    remote_host="localhost",
    exposed_interface=[],
    remote_port=1235,
    listen_port=1234,
)
    control_interface.start_background_sync()

    n=20; Tinit=np.zeros((n,n), float); Tsource=np.ones((n-2,n-2), float)
    controller = Controller('sourcescale', 1, 'Tpoint', [10,10], 4, 10, 0.01, 0.00, 0, control_interface)
    out = controller.run()
    print(out)
    control_interface.stop_background_sync()


if __name__ == "__main__":
    main()


# Example
# get_time and a variable
#print("Getting T variable and time")
#send_requests = True
#while send_requests:
#    retvals = control_interface.request_with_immediate_reply("record", params={"record_what":"Tpoint"}, timeout=10.0)
#    print("Returned values", retvals)

#control_interface.stop_background_sync()