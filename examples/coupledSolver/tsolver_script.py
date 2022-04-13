
import numpy as np
import time
import matplotlib.pyplot as plt 
from TSolver import TsolverThread, TsolverSidecarThread

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
    remote_port=1235,
    listen_port=1236,
)


##############################

n=20; 
Tinit=np.zeros((n,n), float); 
Tsource=np.ones((n-2,n-2), float); 


threadT1a=TsolverSidecarThread(model_interface)
threadT2=TsolverThread(1, n, Tinit, 0.1, Tsource, 1, 10, 1, 5, threadT1a.myTSolverTransmitter)


# Start new Threads
model_interface.start_background_sync()

threadT1a.start()
threadT2.start()


threads = []
threads.append(threadT2)

# Wait for all threads to complete
for t in threads:
    t.join()
threadT1a.stop=True


time.sleep(0.5)
model_interface.stop_background_sync()


fig, ax = plt.subplots(1)
ax.set_aspect('equal')
T=threadT2.myTsolver.T
plt.imshow(T)
plt.colorbar()
plt.savefig("tsolver_plot.png")