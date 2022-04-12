
###################################

import numpy as np
import scipy
import threading
import time
import matplotlib.pyplot as plt 
import json
import random
import os


from communication import SideCar

class Tsolver:
    def __init__(self, dx, n, Tinit, dt, Tsource, k,heatcapacity, sourcescale, tend, sidecar):
        self.T = Tinit;
        self.t = 0;
        self.dx = dx;
        self.n = n;
        self.Tinit = Tinit;
        self.dt = dt;
        self.Tsource = Tsource;
        self.k = k;
        self.sourcescale = sourcescale;
        self.tend = tend;
        self.sidecar = sidecar;
        self.heatcapacity=10

    def main(self):
        self.wait_for_start_signal()
        self.record(self.t)
        self.apply_set(self.t)
 
        while self.t<self.tend:
            print(self.t)
            self.record(self.t)
            self.wait_if_necessary(self.t)
            self.apply_set(self.t)  
            n=self.n
            diffusion=self.k/(self.dx*self.dx) * (self.T[:n-2,1:n-1]+self.T[1:n-1,:n-2]+self.T[2:n,1:n-1]+self.T[1:n-1,2:n]-4*self.T[1:n-1,1:n-1]);
            self.T[1:n-1,1:n-1]=self.T[1:n-1,1:n-1]+self.dt*(self.sourcescale*self.Tsource+diffusion);
            self.t=self.t+self.dt;

        self.finish();
        return self.T;
    
    def wait_a_bit(self):
        time.sleep(0.05);
        
    def wait_if_necessary(self,t): #move what is possible into the sidecar
        while self.sidecar.get_wait_status(t):
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
        # self.sidecar.waitqueue.deleteall();
        # self.sidecar.endsignal=True; #make function for this and the next line
        # self.sidecar.pause() # what happens if the sidecar is in the middle of executing the wait_for_pause; how about release synchronization

    def record(self,t):
        while (not self.sidecar.recordqueue.empty()) and self.sidecar.recordqueue.first()[0] <= t:
            pop1=self.sidecar.recordqueue.pop()
            recindex=pop1[1]
            rec1=pop1[2]
            record=None
            if rec1[0]=='Tpoint':
                record = self.T[rec1[1][0],rec1[1][1]]
                record = record.tolist()
            elif rec1[0]=='Tvol':
                record = self.T[rec1[1][0]:rec1[1][2],rec1[1][1]:rec1[1][3]]
                record = record.tolist()
            else:
                print("Record key not understood: " + str(rec1[0]))
            self.sidecar.records[recindex].append((t,record))
        self.sidecar.t=t

    def apply_set(self,t):
        while (not self.sidecar.setqueue.empty()) and self.sidecar.setqueue.first()[0] <= t:
            set1=self.sidecar.setqueue.pop()[2]
            if set1[0]=='Tsource':
                dat=np.asarray(set1[1])
                if dat.shape==self.Tsource.shape:
                    self.Tsource=tmp
            elif set1[0]=='SARsource':
                dat=np.asarray(set1[1])
                if dat.shape==self.Tsource.shape:
                    self.Tsource=dat/self.heatcapacity
            elif set1[0]=='k':
                if set1[1]>0:
                    self.set_k(set1[1])
            elif set1[0]=='sourcescale':
                self.sourcescale=set1[1]
            elif set1[0]=='tend':
                self.tend=set1[1]


class TSolverSideCar(SideCar):
    def __init__(self, interface ):
        SideCar.__init__(self, interface, "RESPONDER")
        self.canbeset=self.can_be_set()
        self.canbegotten=self.can_be_gotten()
        
    def can_be_set(self): # controllable parameters of the model
        return ['Tsource', 'SARsource', 'k', 'sourcescale', 'tend']; 
    
    def can_be_gotten(self): # observables of the model (similar to sensor)
        return ['Tpoint', 'Tvol'];


class TsolverThread(threading.Thread): 
    def __init__(self, dx, n, Tinit, dt, Tsource, k, heatcapacity, sourcescale, tend, sidecar):
        threading.Thread.__init__(self)
        self.myTsolver=Tsolver(dx, n, Tinit, dt, Tsource, k, heatcapacity, sourcescale, tend, sidecar)
        self.name='Tsolver'
    def run(self):
        print("Starting ",self.name)
        T=self.myTsolver.main()
        print("Exiting ",self.name)

class TsolverSidecarThread(threading.Thread): 
    def __init__(self, interface ):
        threading.Thread.__init__(self)
        self.myTSolverSideCar=TSolverSideCar(interface)
        self.name='TsolverSidecar'
        self.stop=False
    def run(self):
        print("Starting ",self.name)
        while not self.stop:
            time.sleep(0.1)
        print("Exiting ",self.name)


