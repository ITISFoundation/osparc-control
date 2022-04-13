###################################
import json
import os
import random
import threading
import time

import matplotlib.pyplot as plt
import numpy as np
import scipy
from communication import Transmitter


class Tsolver:
    def __init__(
        self, dx, n, Tinit, dt, Tsource, k, heatcapacity, sourcescale, tend, transmitter
    ):
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
        self.transmitter = transmitter
        self.heatcapacity = 10

    def main(self):
        self.wait_for_start_signal()
        self.record(self.t)
        self.apply_set(self.t)

        while self.t < self.tend:
            print(self.t)
            self.record(self.t)
            self.wait_if_necessary(self.t)
            self.apply_set(self.t)
            n = self.n
            diffusion = (
                self.k
                / (self.dx * self.dx)
                * (
                    self.T[: n - 2, 1 : n - 1]
                    + self.T[1 : n - 1, : n - 2]
                    + self.T[2:n, 1 : n - 1]
                    + self.T[1 : n - 1, 2:n]
                    - 4 * self.T[1 : n - 1, 1 : n - 1]
                )
            )
            self.T[1 : n - 1, 1 : n - 1] = self.T[1 : n - 1, 1 : n - 1] + self.dt * (
                self.sourcescale * self.Tsource + diffusion
            )
            self.t = self.t + self.dt

        self.finish()
        return self.T

    def wait_a_bit(self):
        time.sleep(0.05)

    def wait_if_necessary(self, t):  # move what is possible into the transmitter
        while self.transmitter.get_wait_status(t):
            print("triggered wait_if_necessary")
            self.wait_a_bit()

    def wait_for_start_signal(self):
        while not self.transmitter.startsignal:
            self.wait_a_bit()
            self.transmitter.sync()
        self.transmitter.release()

    def finish(self):
        self.record(float("inf"))
        self.transmitter.finish()
        # self.transmitter.waitqueue.deleteall();
        # self.transmitter.endsignal=True; #make function for this and the next line
        # self.transmitter.pause() # what happens if the transmitter is in the middle of executing the wait_for_pause; how about release synchronization

    def record(self, t):
        entry = self.transmitter.get_record_entry(t)
        record = None

        if entry[0]:
            recindex, (name, params) = entry
            if name == "Tpoint":
                record = self.T[params[0], params[1]]
                record = record.tolist()
            elif name == "Tvol":
                # import pdb; pdb.set_trace()
                record = self.T[params[0] : params[2], params[1] : params[3]]
                record = record.tolist()
            else:
                print("Record key not understood: " + str(name))
            self.transmitter.records[recindex].append((t, record))
        self.transmitter.t = t

    def apply_set(self, t):
        entry = self.transmitter.get_set_entry(t)
        if entry:
            (setname, setval) = entry
            if setname == "Tsource":
                dat = np.asarray(setval)
                if dat.shape == self.Tsource.shape:
                    self.Tsource = dat
            elif setname == "SARsource":
                dat = np.asarray(setval)
                if dat.shape == self.Tsource.shape:
                    self.Tsource = dat / self.heatcapacity
            elif setname == "sourcescale":
                self.sourcescale = setval
            elif setname == "tend":
                self.tend = setval


class TSolverTransmitter(Transmitter):
    def __init__(self, interface):
        Transmitter.__init__(self, interface, "RESPONDER")
        self.canbeset = self.can_be_set()
        self.canbegotten = self.can_be_gotten()

    def can_be_set(self):  # controllable parameters of the model
        return ["Tsource", "SARsource", "k", "sourcescale", "tend"]

    def can_be_gotten(self):  # observables of the model (similar to sensor)
        return ["Tpoint", "Tvol"]


class TsolverThread(threading.Thread):
    def __init__(
        self, dx, n, Tinit, dt, Tsource, k, heatcapacity, sourcescale, tend, transmitter
    ):
        threading.Thread.__init__(self)
        self.myTsolver = Tsolver(
            dx, n, Tinit, dt, Tsource, k, heatcapacity, sourcescale, tend, transmitter
        )
        self.name = "Tsolver"

    def run(self):
        print("Starting ", self.name)
        T = self.myTsolver.main()
        print("Exiting ", self.name)


class TsolverSidecarThread(threading.Thread):
    def __init__(self, interface):
        threading.Thread.__init__(self)
        self.myTSolverTransmitter = TSolverTransmitter(interface)
        self.name = "TsolverSidecar"
        self.stop = False

    def run(self):
        print("Starting ", self.name)
        while not self.stop:
            time.sleep(0.1)
        print("Exiting ", self.name)
