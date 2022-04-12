
import numpy as np
import threading
import time 
from communication import SideCar


class EM_T_coupler:
    def __init__(self,sidecarsateliteEM,sidecarsateliteT,EMsetparam_key,EMgetparam_key,EMgetparam_otherparams,Tsetparam_key,Tgetparam_key,Tgetparam_otherparams,coupling_interval):
        self.sidecarsateliteEM=sidecarsateliteEM
        self.sidecarsateliteT=sidecarsateliteT
        self.EMsetparam_key=EMsetparam_key
        self.Tsetparam_key=Tsetparam_key
        self.EMgetparam_key=EMgetparam_key
        self.EMgetparam_otherparams=EMgetparam_otherparams
        self.Tgetparam_key=Tgetparam_key
        self.Tgetparam_otherparams=Tgetparam_otherparams
        self.coupling_interval=coupling_interval
        self.Tstored=[]
        self.EMstored=[]
        
    def main(self):
        time=0
        recindexEM=self.sidecarsateliteEM.record(self.EMgetparam_key, self.coupling_interval, self.EMgetparam_otherparams)
        recindexT=self.sidecarsateliteT.record(self.Tgetparam_key, self.coupling_interval, self.Tgetparam_otherparams)

        waitindexEM=self.sidecarsateliteEM.wait_for_me_at(self.coupling_interval)
        waitindexT=self.sidecarsateliteT.wait_for_me_at(self.coupling_interval)
        self.sidecarsateliteEM.start()
        self.sidecarsateliteT.start()
        nexttime=self.coupling_interval
        while not (self.sidecarsateliteEM.finished() or self.sidecarsateliteT.finished()): #xxx correct?
            self.sidecarsateliteEM.wait_for_time(nexttime,1000)
            self.sidecarsateliteT.wait_for_time(nexttime,1000)
            # import pdb; pdb.set_trace()
            SAR=np.asarray(self.sidecarsateliteEM.get(recindexEM)[0][1])
            T=np.asarray(self.sidecarsateliteT.get(recindexT)[0][1])
            Tlist=T.tolist()
            SARlist=SAR.tolist()
            self.sidecarsateliteEM.setnow(self.EMsetparam_key, Tlist)
            self.sidecarsateliteT.setnow(self.Tsetparam_key, SARlist)
            self.Tstored.append(T)
            self.EMstored.append(SAR)
            nexttime=nexttime+self.coupling_interval
            recindexEM=self.sidecarsateliteEM.record(self.EMgetparam_key, nexttime, self.EMgetparam_otherparams)
            recindexT=self.sidecarsateliteT.record(self.Tgetparam_key, nexttime, self.Tgetparam_otherparams)    
            waitindexEM=self.sidecarsateliteEM.continue_until(nexttime,waitindexEM)    
            waitindexT=self.sidecarsateliteT.continue_until(nexttime,waitindexT)
        return 0



class EM_T_couplerThread(threading.Thread): 
    def __init__(self,sidecarsateliteEM,sidecarsateliteT,EMsetparam_key,EMgetparam_key,EMgetparam_otherparams,Tsetparam_key,Tgetparam_key,Tgetparam_otherparams,coupling_interval):
        threading.Thread.__init__(self)
        self.myCoupler=EM_T_coupler(sidecarsateliteEM,sidecarsateliteT,EMsetparam_key,EMgetparam_key,EMgetparam_otherparams,Tsetparam_key,Tgetparam_key,Tgetparam_otherparams,coupling_interval)
        self.name='EM_T_coupler'
    def run(self):
        print("Starting ",self.name)
        self.myCoupler.main()
        print("Exiting ",self.name)



class EMsolverSidecarSateliteThread(threading.Thread): 
    def __init__(self,interface):
        threading.Thread.__init__(self)
        self.myEMSolverSideCarSatelite=EMSolverSideCarSatelite(interface)
        self.name='EMsolverSidecarSatelite'
        self.stop=False
    def run(self):
        print("Starting ",self.name)
        while not self.stop:
            time.sleep(0.1)
        print("Exiting ",self.name)
        return 0


class EMSolverSideCarSatelite(SideCar):
    def __init__(self, interface):
        SideCar.__init__(self, interface, "REQUESTER")
        self.canbeset=self.can_be_set()
        self.canbegotten=self.can_be_gotten()
        
    def can_be_set(self): # controllable parameters of the model
        return ['sigma', 'T', 'tend'];
    
    def can_be_gotten(self): # observables of the model (similar to sensor)
        return ['SARvol'];



class TSolverSideCarSatelite(SideCar):
    def __init__(self, interface):
        SideCar.__init__(self, interface, "REQUESTER")
        self.canbeset=self.can_be_set()
        self.canbegotten=self.can_be_gotten()
        
    def can_be_set(self): # controllable parameters of the model
        return ['Tsource', 'SARsource', 'k', 'sourcescale', 'tend']; 
    
    def can_be_gotten(self): # observables of the model (similar to sensor)
        return ['Tpoint', 'Tvol'];


class TsolverSidecarSateliteThread(threading.Thread): 
    def __init__(self, interface):
        threading.Thread.__init__(self)
        self.myTSolverSideCarSatelite=TSolverSideCarSatelite(interface)
        self.name='TsolverSidecarSatelite'
        self.stop=False
    def run(self):
        print("Starting ",self.name)
        while not self.stop:
            time.sleep(0.1)
        print("Exiting ",self.name)
        return 0
