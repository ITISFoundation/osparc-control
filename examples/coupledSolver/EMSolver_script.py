
import numpy as np
import time
import matplotlib.pyplot as plt 
from EMSolver import EMsolverThread, EMsolverSidecarThread


from osparc_control import CommandManifest
from osparc_control import CommandParameter
from osparc_control import CommandType
from osparc_control import PairedTransmitter



command_instruct = CommandManifest(
    action="command_instruct",
    description="Execution Instructions",
    params=[
        CommandParameter(name="instructions", description="Instructions for execution.")
    ],
    command_type=CommandType.WITHOUT_REPLY,
)

command_retrieve = CommandManifest(
    action="command_retrieve",
    description="gets state",
    params=[],
    command_type=CommandType.WITHOUT_REPLY,
)

model_interface = PairedTransmitter(
    remote_host="localhost",
    exposed_commands=[command_instruct, command_retrieve],
    remote_port=1237,
    listen_port=1234,
)


n=20; 
Tinit=np.zeros((n,n), float); 
EMsource=np.zeros((n,n), float)
EMsource[int(n/3),int(n/4)]=1
EMinit=np.zeros((n,n), float)


threadEM1a=EMsolverSidecarThread(model_interface)
threadEM2=EMsolverThread(n, EMinit, 1, EMsource, Tinit, 5, 1, 5, threadEM1a.myEMSolverSideCar)

# Start new Threads
model_interface.start_background_sync()


threadEM1a.start()
threadEM2.start()

threads = []

threads.append(threadEM2)

# Wait for all threads to complete
for t in threads:
    t.join()

threadEM1a.stop=True


time.sleep(0.5)
model_interface.stop_background_sync()

fig = plt.figure()
ax = fig.add_subplot(1,1,1)
ax.set_aspect('equal')
plt.imshow(threadEM2.myEMsolver.SAR)
plt.colorbar()
plt.savefig("emsolver_plot.png")