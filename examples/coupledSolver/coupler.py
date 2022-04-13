
import numpy as np
import threading
import time 
from communication import Transmitter


class EM_T_coupler:
    def __init__(self,transmittersateliteEM,transmittersateliteT,EMsetparam_key,EMgetparam_key,EMgetparam_otherparams,Tsetparam_key,Tgetparam_key,Tgetparam_otherparams,coupling_interval):
        self.transmittersateliteEM=transmittersateliteEM
        self.transmittersateliteT=transmittersateliteT
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
        recindexEM=self.transmittersateliteEM.record(self.EMgetparam_key, self.coupling_interval, self.EMgetparam_otherparams)
        recindexT=self.transmittersateliteT.record(self.Tgetparam_key, self.coupling_interval, self.Tgetparam_otherparams)

        waitindexEM=self.transmittersateliteEM.wait_at_t(self.coupling_interval)
        waitindexT=self.transmittersateliteT.wait_at_t(self.coupling_interval)
        self.transmittersateliteEM.start()
        self.transmittersateliteT.start()
        nexttime=self.coupling_interval
        while not (self.transmittersateliteEM.finished() or self.transmittersateliteT.finished()): #xxx correct?
            self.transmittersateliteEM.wait_for_time(nexttime,1000)
            self.transmittersateliteT.wait_for_time(nexttime,1000)
            # import pdb; pdb.set_trace()
            SAR=np.asarray(self.transmittersateliteEM.get(recindexEM)[0][1])
            T=np.asarray(self.transmittersateliteT.get(recindexT)[0][1])
            Tlist=T.tolist()
            SARlist=SAR.tolist()
            self.transmittersateliteEM.setnow(self.EMsetparam_key, Tlist)
            self.transmittersateliteT.setnow(self.Tsetparam_key, SARlist)
            self.Tstored.append(T)
            self.EMstored.append(SAR)
            nexttime=nexttime+self.coupling_interval
            recindexEM=self.transmittersateliteEM.record(self.EMgetparam_key, nexttime, self.EMgetparam_otherparams)
            recindexT=self.transmittersateliteT.record(self.Tgetparam_key, nexttime, self.Tgetparam_otherparams)    
            waitindexEM=self.transmittersateliteEM.continue_until(nexttime,waitindexEM)    
            waitindexT=self.transmittersateliteT.continue_until(nexttime,waitindexT)
        return 0



class EM_T_couplerThread(threading.Thread): 
    def __init__(self,transmittersateliteEM,transmittersateliteT,EMsetparam_key,EMgetparam_key,EMgetparam_otherparams,Tsetparam_key,Tgetparam_key,Tgetparam_otherparams,coupling_interval):
        threading.Thread.__init__(self)
        self.myCoupler=EM_T_coupler(transmittersateliteEM,transmittersateliteT,EMsetparam_key,EMgetparam_key,EMgetparam_otherparams,Tsetparam_key,Tgetparam_key,Tgetparam_otherparams,coupling_interval)
        self.name='EM_T_coupler'
    def run(self):
        print("Starting ",self.name)
        self.myCoupler.main()
        print("Exiting ",self.name)



class EMsolverSidecarSateliteThread(threading.Thread): 
    def __init__(self,interface):
        threading.Thread.__init__(self)
        self.myEMSolverTransmitterSatelite=EMSolverTransmitterSatelite(interface)
        self.name='EMsolverSidecarSatelite'
        self.stop=False
    def run(self):
        print("Starting ",self.name)
        while not self.stop:
            time.sleep(0.1)
        print("Exiting ",self.name)
        return 0


class EMSolverTransmitterSatelite(Transmitter):
    def __init__(self, interface):
        Transmitter.__init__(self, interface, "REQUESTER")
        self.canbeset=self.can_be_set()
        self.canbegotten=self.can_be_gotten()
        
    def can_be_set(self): # controllable parameters of the model
        return ['sigma', 'T', 'tend'];
    
    def can_be_gotten(self): # observables of the model (similar to sensor)
        return ['SARvol'];



class TSolverTransmitterSatelite(Transmitter):
    def __init__(self, interface):
        Transmitter.__init__(self, interface, "REQUESTER")
        self.canbeset=self.can_be_set()
        self.canbegotten=self.can_be_gotten()
        
    def can_be_set(self): # controllable parameters of the model
        return ['Tsource', 'SARsource', 'k', 'sourcescale', 'tend']; 
    
    def can_be_gotten(self): # observables of the model (similar to sensor)
        return ['Tpoint', 'Tvol'];


class TsolverSidecarSateliteThread(threading.Thread): 
    def __init__(self, interface):
        threading.Thread.__init__(self)
        self.myTSolverTransmitterSatelite=TSolverTransmitterSatelite(interface)
        self.name='TsolverSidecarSatelite'
        self.stop=False
    def run(self):
        print("Starting ",self.name)
        while not self.stop:
            time.sleep(0.1)
        print("Exiting ",self.name)
        return 0
