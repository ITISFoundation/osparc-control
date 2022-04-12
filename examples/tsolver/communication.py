from operator import truediv
import random
import time
from queue import PriorityQueue

class BaseControlError(Exception):
    """inherited by all exceptions in this module"""

class VariableNotAccessibleError(BaseControlError):
    """The variable can't be accessed for recording"""

#class EntryNotAvailable(BaseControlError):
#    """The entry is not available"""

class SideCar:
    def __init__(self, interface, io):
        self.t=0
        self.startsignal=False
        self.endsignal=False
        self.paused=True
        #self.getsignal=False;
        self.waitqueue=PriorityQueue()
        self.recordqueue=PriorityQueue()
        self.setqueue=PriorityQueue()
        self.records={}
        self.instructions= [] #{}
        self.canbeset=[]
        self.canbegotten=[]
        self.interface=interface
        self.io=io

    def can_be_set(self): # controllable parameters of the model
        return self.canbeset; 

    def setnow(self,key,value):
        if self.io == "RESPONDER":
            if(key in self.canbeset):
                self.setqueue.put((self.t, "", (key,value)))
                return 0
            else:
                raise VariableNotAccessibleError(f"Variable {key} cannot be set")
        elif self.io == "REQUESTER":
            self.instructions.append({'inst':'setnow','key':key,'val':value})
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1
    """
    # Doesn't seem to be used
    def set1(self,key,value,t):
        if self.io == "RESPONDER":
            if(key in self.canbeset):
                self.setqueue.insert(t,(key,value))
                return 0
            return -1;
        elif self.io == "REQUESTER":
            self.instructions.append({'inst':'set','t':t,'key':key,'val':value})
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1
    """

    def can_be_gotten(self): # observables of the model (similar to sensor)
        return self.canbegotten

    def record(self,key,timepoints,otherparams,index=None): # when and where to record observables
        ncalls = 0
        if self.io == "RESPONDER":
            if key in self.canbegotten:
                ncalls += 1
                self.recordqueue.put((timepoints,index,(key,otherparams))) #xxx problem with more than one timepoint
                self.records[index]=[]
            else:
                raise VariableNotAccessibleError(f"Variable {key} cannot be recorded ")

        elif self.io == "REQUESTER":
            index = random.getrandbits(64)
            self.instructions.append({'inst':'record','timepoints':timepoints,'key':key,'otherparams':otherparams,'index':index})
            return index
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1

    def get_record_entry(self, t):
        self.t = t
        if (not self.recordqueue.empty()) and self.recordqueue.queue[0][0] <= t: # Check if there's something to record at t
            entry = self.recordqueue.get()
            return entry

    def get_set_entry(self, t):
        self.t = t
        if (not self.setqueue.empty()) and self.setqueue.queue[0][0] <= t:
            entry = self.setqueue.get()
            return entry

    def wait_a_bit(self):
        time.sleep(0.05);
        
    def get(self,index):
        entry = self.records[index]
        if entry:
            return entry

    def wait_for_time(self,waittime,maxcount):
        counter=0;
        while self.t<waittime and counter<maxcount:
            self.sync()
            #self.sync() # Second call seems unnecessary
            self.wait_a_bit()
            counter+=1
        if self.t<waittime:
            print('timeout')

    def wait_if_necessary(self,t): #move what is possible into the sidecar
        while self.get_wait_status(t):
            print("triggered wait_if_necessary")
            self.wait_a_bit()
    
    def get_wait_status(self, t):
        self.sync()
        if (not self.waitqueue.empty()) and (self.waitqueue.queue[0][0] <= t):
            self.pause()
            #self.sync() # This call seems unnecessary
            return True
        else:
            self.release()
            return False

    def wait_for_me_at(self,t,index=None):
        if self.io == "RESPONDER":
            self.waitqueue.put((t,None,index))
        elif self.io == "REQUESTER":
            index = random.getrandbits(64)
            self.instructions.append({'inst':'waitformeat','t':t,'index':index})
            return index
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1
    """
    def continue_please(self,index=None):
        if self.io == "RESPONDER":
            mywait=self.waitqueue.get(index) # TODO: check that this works, python queue doesn't support get with index
            if mywait!=None:
                #self.waitqueue.delete(index) # TODO as above. Once the item has been got, it should be "deleted" already
                if self.waitqueue.queue[0]==None or self.waitqueue.queue[0][0]>self.t:
                    self.release();
        elif self.io == "REQUESTER":
            index = random.getrandbits(64)
            self.instructions.append({'inst':'continueplease','index':index})
            self.release()
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1
    """ 

    def continue_until(self,t,index=None): # schedule your wait point for later
        if self.io == "RESPONDER":
            self.wait_for_me_at(t,index);
            mywait=self.waitqueue.get() # TODO: check that this works, python queue doesn't support get with index
            if mywait!=None:
                if self.waitqueue.queue[0][0]>self.t:
                    self.release();

        elif self.io == "REQUESTER":
            index1 = random.getrandbits(64)
            self.instructions.append({'inst':'continueuntil','t':t,'index1':index1,'index2':index})
            self.release()
            return index1;
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1

    def start(self):
        if self.io == "RESPONDER":
            self.startsignal=True;
            self.release();
        elif self.io == "REQUESTER":
            self.instructions.append({'inst':'start'})
            self.release()
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1

    def wait_for_start_signal(self):
        while not self.startsignal:
        # while not self.sidecar.started():
            #time.sleep(0.05)
            self.sync()
        #self.sidecar.release()

    def pause(self):
        if (not self.paused) or (not self.startsignal):
            self.paused=True
            #self.sync() # Doesn't seem necessary
        
    def release(self):
        if self.paused:
            #self.sync() # Doesn't seem necessary
            self.paused=False 
            self.sync()

    def finished(self):
        return self.endsignal;

    def sync(self):
        if self.io == "RESPONDER":
            inputdata = None
            commands = self.interface.get_incoming_requests()
            for command in commands:
                if command.action == "command_instruct":
                    inputdata = command.params
                elif command.action == "command_retrieve":
                    outputdata={'t':self.t, 'endsignal':self.endsignal, 'paused':self.paused, 'records':self.records} # start?
                    self.interface.request_without_reply(
                        "command_data", params=outputdata
                    )
                    print("got retrieve")
                if inputdata != None:
                    self.instructions=inputdata['instructions']
                    if len(self.instructions) > 0:
                        self.executeInstructions()
                        print("Successfully executed " + str(inputdata))

        elif self.io == "REQUESTER": 
            if self.instructions:
                outputdata={'instructions':self.instructions}
                self.interface.request_without_reply(
                    "command_instruct", params=outputdata
                )
            self.interface.request_without_reply("command_retrieve")
            self.instructions=[]
            print("asked to get state...")

            inputdata = None        
            commands = self.interface.get_incoming_requests()
            for command in commands:
                if command.action == "command_data":
                    inputdata = command.params
                    self.t=inputdata['t']
                    self.endsignal=inputdata['endsignal']
                    self.paused=inputdata['paused']
                    self.records=inputdata['records']
                    print(self.t)
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1

           

    def finish(self):
            #self.waitqueue.deleteall(); # Queue should be already empty at the end
            self.endsignal=True; #make function for this and the next line

            self.pause() # what happens if the sidecar is in the middle of executing the wait_for_pause; how about release synchronization
            outputdata={'t':self.t, 'endsignal':self.endsignal, 'paused':self.paused, 'records':self.records} # start?
            self.interface.request_without_reply(
                "command_data", params=outputdata
            ) 

    def executeInstructions(self):
        l=len(self.instructions)
        for _ in range(l):
            entry = self.instructions.pop(0)
            inst = entry['inst']
            if inst=='setnow':
                self.setnow(entry['key'],entry['val'])
            elif inst=='record':
                self.record(entry['key'],entry['timepoints'],entry['otherparams'],entry['index'])
            elif inst=='waitformeat':
                self.wait_for_me_at(entry['t'],entry['index'])
            #elif inst=='continueplease':
            #   self.continue_please(entry['index'])
            elif inst=='continueuntil':
                self.continue_until(entry['t'],entry['index1'])
            elif inst=='start':
                self.start()