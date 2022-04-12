
###################################

import numpy as np
import scipy
from scipy.sparse.linalg import spsolve
# from scipy.sparse import linalg
import threading
import time
import matplotlib.pyplot as plt 
import json
import random
import os


from communication import SideCar

class EMsolver:
    def __init__(self, n, EMinit, dt, EMsource, Tinit, tend, sigma0, sigmaT, sidecar):
        self.EM = EMinit;
        self.t = 0
        self.n = n
        self.dt = dt
        self.EMsource = EMsource.flatten()
        self.sigma0 = sigma0;
        self.sigmaT = sigmaT;
        self.sigma = self.sigma_calc(Tinit)
        self.tend = tend;
        self.sidecar = sidecar;
        self.V = np.zeros([n,n])
        self.SAR = np.zeros([n,n])

    def solveV(self):
        nrcoefs=self.n*self.n+4*self.n*(self.n-1)
        n2=self.n*self.n
        row=np.zeros(nrcoefs, dtype=int)
        col=np.zeros(nrcoefs, dtype=int)
        data=np.zeros(nrcoefs)
        
        counter=0
        mysigma=self.sigma[0,0]
        row[1]=0
        col[1]=1
        data[1]=mysigma*self.sigma[0,1]/(mysigma+self.sigma[0,1])
        row[2]=0
        col[2]=self.n
        data[2]=mysigma*self.sigma[1,0]/(mysigma+self.sigma[1,0])
        row[0]=0
        col[0]=0
        data[0]=-(4*mysigma+data[1]+data[2])
        counter+=3
        for j in range(1,self.n-1):
            mysigma=self.sigma[0,j]
            row[counter+1]=j
            col[counter+1]=j+1
            data[counter+1]=mysigma*self.sigma[0,j+1]/(mysigma+self.sigma[0,j+1])
            row[counter+2]=j
            col[counter+2]=j+self.n
            data[counter+2]=mysigma*self.sigma[1,j]/(mysigma+self.sigma[1,j])
            row[counter+3]=j
            col[counter+3]=j-1
            data[counter+3]=mysigma*self.sigma[0,j-1]/(mysigma+self.sigma[0,j-1])
            row[counter]=j
            col[counter]=j
            data[counter]=-(2*mysigma+data[counter+1]+data[counter+2]+data[counter+3])
            counter+=4
        j=self.n-1
        mysigma=self.sigma[0,j]
        row[counter+1]=j
        col[counter+1]=j+self.n
        data[counter+1]=mysigma*self.sigma[1,j]/(mysigma+self.sigma[1,j])
        row[counter+2]=j
        col[counter+2]=j-1
        data[counter+2]=mysigma*self.sigma[0,j-1]/(mysigma+self.sigma[0,j-1])
        row[counter]=j
        col[counter]=j
        data[counter]=-(4*mysigma+data[counter+1]+data[counter+2])
        counter+=3
        myindex=self.n
        for i in range(1,self.n-1):
            mysigma=self.sigma[i,0]
            row[counter+1]=myindex
            col[counter+1]=myindex+1
            data[counter+1]=mysigma*self.sigma[i,1]/(mysigma+self.sigma[i,1])
            row[counter+2]=myindex
            col[counter+2]=myindex+self.n
            data[counter+2]=mysigma*self.sigma[i+1,0]/(mysigma+self.sigma[i+1,0])
            row[counter+3]=myindex
            col[counter+3]=myindex-self.n
            data[counter+3]=mysigma*self.sigma[i-1,0]/(mysigma+self.sigma[i-1,0])
            row[counter]=myindex
            col[counter]=myindex
            data[counter]=-(2*mysigma+data[counter+1]+data[counter+2]+data[counter+3])
            counter+=4
            myindex+=1
            for j in range(1,self.n-1):
                mysigma=self.sigma[i,j]
                row[counter+1]=myindex
                col[counter+1]=myindex+1
                data[counter+1]=mysigma*self.sigma[i,j+1]/(mysigma+self.sigma[i,j+1])
                row[counter+2]=myindex
                col[counter+2]=myindex+self.n
                data[counter+2]=mysigma*self.sigma[i+1,j]/(mysigma+self.sigma[i+1,j])
                row[counter+3]=myindex
                col[counter+3]=myindex-self.n
                data[counter+3]=mysigma*self.sigma[i-1,j]/(mysigma+self.sigma[i-1,j])
                row[counter+4]=myindex
                col[counter+4]=myindex-1
                data[counter+4]=mysigma*self.sigma[i,j-1]/(mysigma+self.sigma[i,j-1])
                row[counter]=myindex
                col[counter]=myindex
                data[counter]=-(data[counter+1]+data[counter+2]+data[counter+3]+data[counter+4])
                counter+=5
                myindex+=1
            j=self.n-1
            mysigma=self.sigma[i,j]
            row[counter+1]=myindex
            col[counter+1]=myindex+self.n
            data[counter+1]=mysigma*self.sigma[i+1,j]/(mysigma+self.sigma[i+1,j])
            row[counter+2]=myindex
            col[counter+2]=myindex-self.n
            data[counter+2]=mysigma*self.sigma[i-1,j]/(mysigma+self.sigma[i-1,j])
            row[counter+3]=myindex
            col[counter+3]=myindex-1
            data[counter+3]=mysigma*self.sigma[i,j-1]/(mysigma+self.sigma[i,j-1])
            row[counter]=myindex
            col[counter]=myindex
            data[counter]=-(2*mysigma+data[counter+1]+data[counter+2]+data[counter+3])
            counter+=4
            myindex+=1
        i=self.n-1
        mysigma=self.sigma[i,0]
        row[counter+1]=myindex
        col[counter+1]=myindex+1
        data[counter+1]=mysigma*self.sigma[i,1]/(mysigma+self.sigma[i,1])
        row[counter+2]=myindex
        col[counter+2]=myindex-self.n
        data[counter+2]=mysigma*self.sigma[i-1,0]/(mysigma+self.sigma[i-1,0])
        row[counter]=myindex
        col[counter]=myindex
        data[counter]=-(4*mysigma+data[counter+1]+data[counter+2])
        counter+=3
        myindex+=1
        for j in range(1,self.n-1):
            mysigma=self.sigma[i,j]
            row[counter+1]=myindex
            col[counter+1]=myindex+1
            data[counter+1]=mysigma*self.sigma[i,j+1]/(mysigma+self.sigma[i,j+1])
            row[counter+2]=myindex
            col[counter+2]=myindex-self.n
            data[counter+2]=mysigma*self.sigma[i-1,j]/(mysigma+self.sigma[i-1,j])
            row[counter+3]=myindex
            col[counter+3]=myindex-1
            data[counter+3]=mysigma*self.sigma[i,j-1]/(mysigma+self.sigma[i,j-1])
            row[counter]=myindex
            col[counter]=myindex
            data[counter]=-(2*mysigma+data[counter+1]+data[counter+2]+data[counter+3])
            counter+=4
            myindex+=1
        j=self.n-1
        mysigma=self.sigma[i,j]
        row[counter+1]=myindex
        col[counter+1]=myindex-self.n
        data[counter+1]=mysigma*self.sigma[i-1,j]/(mysigma+self.sigma[i-1,j])
        row[counter+2]=myindex
        col[counter+2]=myindex-1
        data[counter+2]=mysigma*self.sigma[i,j-1]/(mysigma+self.sigma[i,j-1])
        row[counter]=myindex
        col[counter]=myindex
        data[counter]=-(4*mysigma+data[counter+1]+data[counter+2])
        
        coefmatrix=scipy.sparse.csr_matrix( (data,(row,col)), shape=(n2,n2) )
        self.V = scipy.sparse.linalg.spsolve(coefmatrix, -self.EMsource).reshape((self.n, self.n))        
        
    def computeSAR(self):
        self.SAR=self.sigma*self.V
        #xxx self.sigma*np.abs(self.E[rec1[1][0]:rec1[1][2],rec1[1][1]:rec1[1][3]])^2/(2*self.rho))
                                                      
    def sigma_calc(self,T):
        return self.sigma0+T*self.sigmaT
    
    def main(self):
        self.wait_for_start_signal()
        self.record(self.t)
        self.apply_set(self.t)
        
        while self.t<self.tend:
            self.record(self.t)
            self.wait_if_necessary(self.t)
            self.apply_set(self.t)  

            self.solveV()
            self.computeSAR()
            self.t=self.t+self.dt;
        
        self.is_finished()
        
        return 0

    def wait_a_bit(self):
        time.sleep(0.05);
 
    def wait_if_necessary(self,t): 
        while self.sidecar.get_wait_status(t):
            print("triggered wait_if_necessary")
            self.wait_a_bit()

    def wait_for_start_signal(self):
        while not self.sidecar.startsignal:
        # while not self.sidecar.started():
            self.wait_a_bit()
            self.sidecar.sync()
        self.sidecar.release()

    def is_finished(self):
        self.record(float("inf"))
        self.sidecar.finish()

    def record(self,t):
        recindex,recinfo=self.sidecar.is_there_something_to_record(t)
        while not (recindex is None):
            if recinfo[0]=='SARvol':
                record = self.SAR[recinfo[1][0]:recinfo[1][2],recinfo[1][1]:recinfo[1][3]];
                record = record.tolist()
                self.sidecar.record_for_me(recindex,t,record)
            recindex,recinfo=self.sidecar.is_there_something_to_record(t)

    def apply_set(self,t):
        setinfo=self.sidecar.is_there_something_to_set(t)
        while not (setinfo is None):
            if setinfo[0]=='sigma':
                sigma1=np.asarray(setinfo[1])
                if sigma1.shape==self.sigma.shape:
                    self.sigma=sigma1
            elif setinfo[0]=='T':
                T1=np.asarray(setinfo[1])
                if T1.shape==self.sigma.shape:
                    self.sigma=self.sigma_calc(T1)
            elif setinfo[0]=='tend':
                self.tend=setinfo[1]
            setinfo=self.sidecar.is_there_something_to_set(t)                


class EMSolverSideCar(SideCar):
    def __init__(self, interface ):
        SideCar.__init__(self, interface, "RESPONDER")
        self.canbeset=self.can_be_set()
        self.canbegotten=self.can_be_gotten()
        
    def can_be_set(self): # controllable parameters of the model
        return ['sigma', 'T', 'tend'];
    
    def can_be_gotten(self): # observables of the model (similar to sensor)
        return ['SARvol'];




class EMsolverThread(threading.Thread): 
    def __init__(self, n, EMinit, dt, EMsource, Tinit, tend, sigma0, sigmaT, sidecar):
        threading.Thread.__init__(self)
        self.myEMsolver=EMsolver(n, EMinit, dt, EMsource, Tinit, tend, sigma0, sigmaT, sidecar)
        self.name='EMsolver'
    def run(self):
        print("Starting ",self.name)
        SAR=self.myEMsolver.main()
        print("Exiting ",self.name)



class EMsolverSidecarThread(threading.Thread): 
    def __init__(self, interface):
        threading.Thread.__init__(self)
        self.myEMSolverSideCar=EMSolverSideCar(interface)
        self.name='EMsolverSidecar'
        self.stop=False
    def run(self):
        print("Starting ",self.name)
        while not self.stop:
            time.sleep(0.1)
        print("Exiting ",self.name)

