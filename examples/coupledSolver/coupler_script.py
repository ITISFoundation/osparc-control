
import time
import numpy as np
import time
import matplotlib.pyplot as plt 
from coupler import TsolverSidecarSateliteThread, EMsolverSidecarSateliteThread, EM_T_couplerThread


from osparc_control import CommandManifest
from osparc_control import CommandParameter
from osparc_control import CommandType
from osparc_control import PairedTransmitter



command_data = CommandManifest(
    action="command_data",
    description="State Data",
    params=[
        CommandParameter(name='t', description="time"),
        CommandParameter(name='endsignal', description="is finished"),
        CommandParameter(name='paused', description="is paused"), 
        CommandParameter(name='records', description="some records")
    ],
    command_type=CommandType.WITHOUT_REPLY,
)


Tcontrol_interface = PairedTransmitter(
    remote_host="localhost",
    exposed_commands=[command_data],
    remote_port=1236,
    listen_port=1235,
)

EMcontrol_interface = PairedTransmitter(
    remote_host="localhost",
    exposed_commands=[command_data],
    remote_port=1234,
    listen_port=1237,
)


n=20; 
Tinit=np.zeros((n,n), float)
threadEM1b=EMsolverSidecarSateliteThread(EMcontrol_interface)
threadT1b=TsolverSidecarSateliteThread(Tcontrol_interface)
thread3Coupling=EM_T_couplerThread(threadEM1b.myEMSolverTransmitterSatelite,threadT1b.myTSolverTransmitterSatelite,'T','SARvol',[1,1,n-1,n-1],'SARsource','Tvol',[0,0,n,n],1)


# Start new Threads
Tcontrol_interface.start_background_sync()
EMcontrol_interface.start_background_sync()

thread3Coupling.start()
threadEM1b.start()
threadT1b.start()

threads = []
threads.append(thread3Coupling)

# Wait for all threads to complete
for t in threads:
    t.join()

threadT1b.stop=True
threadEM1b.stop=True

print("Exiting Main Thread")

time.sleep(0.5)

Tcontrol_interface.stop_background_sync()
EMcontrol_interface.stop_background_sync()

plt.figure(figsize=(15,5))
plt.subplot(1, len(thread3Coupling.myCoupler.Tstored), 1)
print('Temperature evolution')
for i in range(len(thread3Coupling.myCoupler.Tstored)):
    plt.subplot(1, 5, i+1)
    plt.imshow(thread3Coupling.myCoupler.Tstored[i], vmin=0, vmax=1.3)
plt.savefig("tstored_plot.png")


plt.figure(figsize=(15,5))
plt.subplot(1, len(thread3Coupling.myCoupler.Tstored), 1)
print('EM evolution')
for i in range(len(thread3Coupling.myCoupler.EMstored)):
    plt.subplot(1, 5, i+1)
    plt.imshow(thread3Coupling.myCoupler.EMstored[i], vmin=0, vmax=1.5)
plt.savefig("EMstored_plot.png")