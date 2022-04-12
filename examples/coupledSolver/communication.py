
import random
import time

import numpy as np

from queue import PriorityQueue
from operator import truediv

class KindofPriorityQueue():
    
    def __init__(self):
        self.myqueue = []
        
    def pop(self):
        if not self.myqueue:
            return None
        return self.myqueue.pop()
    
    def insert(self,t,elem):
        retval=random.getrandbits(64)
        self.myqueue.append((t, retval, elem))
        self.myqueue.sort(reverse=True) 
        return retval
    
    def insert_with_index(self,t,elem,index):
        self.myqueue.append((t, index, elem))
        self.myqueue.sort(reverse=True)
        
    def delete(self, index):
        counter=0
        while counter<len(self.myqueue) and self.myqueue[counter][1]!=index:
            counter+=1
        if counter<len(self.myqueue):
            del self.myqueue[counter]
            
    def deleteall(self):
        self.myqueue = []
            
    def first(self):
        if not self.myqueue:
            return None
        return self.myqueue[-1]
    
    def get(self, index):
        retval=None
        counter=0
        while counter<len(self.myqueue) and self.myqueue[counter][1]!=index:
            counter+=1
        if counter<len(self.myqueue):
            retval=self.myqueue[counter]
        return retval
    
    def empty(self):
        return not self.myqueue

class BaseControlError(Exception):
    """inherited by all exceptions in this module"""

class VariableNotAccessibleError(BaseControlError):
    """The variable can't be accessed for recording"""


class SideCar:
    def __init__(self, interface, io):
        self.t=0;
        self.startsignal=False;
        self.endsignal=False;
        self.paused=True;
        #self.getsignal=False;
        self.waitqueue=KindofPriorityQueue()
        self.recordqueue=KindofPriorityQueue()
        self.setqueue=KindofPriorityQueue()
        self.records={}
        self.instructions=[]
        self.instructioncounter=0
        self.canbeset=[]
        self.canbegotten=[]
        self.interface=interface
        self.io=io

    def can_be_set(self): # controllable parameters of the model
        return self.canbeset; 
    
    def is_there_something_to_set(self,t):
        self.t=t
        if (not self.setqueue.empty()) and self.setqueue.first()[0] <= t:
            return self.setqueue.pop()[2]
        else:
            return None

    def setnow(self,key,value):
        if self.io == "RESPONDER":
            if(key in self.canbeset):
                self.setqueue.insert(self.t,(key,value))
                return 0
            return -1
        elif self.io == "REQUESTER":
            # if isinstance(value, np.ndarray):
            #     value = value.tolist()
            self.instructions.append({'inst':'setnow','key':key,'val':value})
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1

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


    def can_be_gotten(self): # observables of the model (similar to sensor)
        return self.canbegotten

    def is_there_something_to_record(self,t):
        self.t=t
        if (not self.recordqueue.empty()) and self.recordqueue.first()[0] <= t:
            pop1=self.recordqueue.pop()
            return pop1[1],pop1[2]
        else:
            return None,None

    def record_for_me(self,recindex,t,item):
        self.records[recindex].append((t,item))
        self.t=t
        
    def record(self,key,timepoints,otherparams,index=None): # when and where to record observables
        if self.io == "RESPONDER":
            if key in self.canbegotten:
                self.recordqueue.insert_with_index(timepoints,(key,otherparams),index) #xxx problem with more than one timepoint
                self.records[index]=[]
            return 0
        elif self.io == "REQUESTER":
            index = random.getrandbits(64)
            self.instructions.append({'inst':'record','timepoints':timepoints,'key':key,'otherparams':otherparams,'index':index})
            return index
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1

    def wait_a_bit(self):
        time.sleep(0.05);
        
    def get(self,index):
        return self.records[index]

    def wait_for_time(self,waittime,maxcount):
        counter=0;
        while self.t<waittime and counter<maxcount:
            self.sync()
            self.sync()
            self.wait_a_bit()
            counter+=1
        if self.t<waittime:
            print('timeout')

    def get_wait_status(self, t):
        self.sync()
        # print(self.waitqueue.myqueue)
        if (not self.waitqueue.empty()) and (self.waitqueue.first()[0] <= t):
            self.pause()
            self.sync()
            return True
        else:
            self.release()
            return False

    def started(self):
        if not self.startsignal:
            self.sync()
            return True
        else:
            self.release()
            return False

    def get_time(self):
        return self.t;

    def wait_for_me_at(self,t,index=None):
        if self.io == "RESPONDER":
            self.waitqueue.insert_with_index(t,None,index)
        elif self.io == "REQUESTER":
            index = random.getrandbits(64)
            self.instructions.append({'inst':'waitformeat','t':t,'index':index})
            return index
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1

    def continue_please(self,index=None):
        if self.io == "RESPONDER":
            mywait=self.waitqueue.get(index)
            if mywait!=None:
                self.waitqueue.delete(index)
                if self.waitqueue.first()==None or self.waitqueue.first()[0]>self.t:
                    self.release();
        elif self.io == "REQUESTER":
            self.instructions.append({'inst':'continueplease','index':index})
            self.release()
        else:
            print("Unsupported communicator: " + str(self.io) + " - only 'REQUESTER' or 'RESPONDER' allowed")
            return-1
        

    def continue_until(self,t,index=None,index2=None): # schedule your wait point for later
        if self.io == "RESPONDER":
            self.wait_for_me_at(t,index);
            self.continue_please(index2);
            return
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

    def pause(self):
        if (not self.paused) or (not self.startsignal):
            self.paused=True
            self.sync()
        
    def release(self):
        if self.paused:
            self.sync()
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
                    print(str(inputdata))
                elif command.action == "command_retrieve":
                    records = self.records
                    if isinstance(records, np.ndarray):
                        records = records.tolist()
                    outputdata={'t':self.t, 'endsignal':self.endsignal, 'paused':self.paused, 'records':records} # start?
                    self.interface.request_without_reply(
                        "command_data", params=outputdata
                    )
                    print("got retrieve")
                if inputdata != None:
                    self.instructions=inputdata['instructions']
                    self.executeInstructions()
                    print("Successfully executed " + str(inputdata))
            
        elif self.io == "REQUESTER":
            print(self.instructions)
            if self.instructions:
                outputdata={'instructions':self.instructions}
                self.interface.request_without_reply(
                    "command_instruct", params=outputdata
                )
            self.interface.request_without_reply("command_retrieve")
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
            self.waitqueue.deleteall();
            self.endsignal=True; #make function for this and the next line
            records = self.records
            if isinstance(records, np.ndarray):
                records = records.tolist()
            self.pause() # what happens if the sidecar is in the middle of executing the wait_for_pause; how about release synchronization
            outputdata={'t':self.t, 'endsignal':self.endsignal, 'paused':self.paused, 'records':records} # start?
            self.interface.request_without_reply(
                "command_data", params=outputdata
            )     

    def executeInstructions(self):
        l=len(self.instructions)
        
        while self.instructioncounter<l:
            i=self.instructioncounter
            inst=self.instructions[i]['inst']
            self.instructioncounter=i+1
            if inst=='setnow':
                self.setnow(self.instructions[i]['key'],self.instructions[i]['val'])
            elif inst=='set':
                self.set1(self.instructions[i]['key'],self.instructions[i]['val'],self.instructions[i]['t'])
            elif inst=='record':
                self.record(self.instructions[i]['key'],self.instructions[i]['timepoints'],self.instructions[i]['otherparams'],self.instructions[i]['index'])
            elif inst=='waitformeat':
                self.wait_for_me_at(self.instructions[i]['t'],self.instructions[i]['index'])
            elif inst=='continueplease':
                self.continue_please(self.instructions[i]['index'])
            elif inst=='continueuntil':
                self.continue_until(self.instructions[i]['t'],self.instructions[i]['index1'],self.instructions[i]['index2'])
            elif inst=='start':
                self.start()
            else:
                print("Unknown or null instruction.")
