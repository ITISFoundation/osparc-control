# o<sup>2</sup>S<sup>2</sup>PARC Control Example (Thermal Solver + PID Controller)
This example illustrates how to use [osparc-control](https://itisfoundation.github.io/osparc-control) and a [Generic Coupling API](#generic-coupling-api) to control a model (e.g. a physiological or physical model) in real-time. We assume that you have Python 3.6+ and that you are installing dependencies via [pip](https://pip.pypa.io/en/stable/). <br /><br /> 

## Installation
osparc-control can be installed via pip
```bash
pip install osparc-control
```

## How to run this example
In a terminal run:
```bash
python examples/examples/tsolver/Tsolver.py
```
And in another:
```bash
python examples/examples/tsolver/Controller.py
```
The order in which you run the two scripts doesn't matter.
Once both scripts are launched, you will see some debugging output (e.g. simulation time advancing).<br /><br /> 

## Expected output

Once the simulation has finished, two figures will be saved in your working directory: one is a 2D heatmap of temperature values at the end of the simulation (this is the output of ```Tsolver.py```) and the other shows the time evolution of values and errors (output of `Controller.py`)<br /><br /> 

## How this example works

A thermal solver (```Tsolver.py```) is controlled by a simple and generic PID controller (```Controller.py```) to reach the setpoint temperature value of 4 (*setpoint* argument in ```Controller.py```). 
At each coupling interval, defined by the Controller argument *iteration_time*, the temperature value (*T*) is recorded , the *error* between the current value and the setpoint is computed, and a new *sourcescale* value is set. 
At the end of the simulation the temperature value reaches the desired *setpoint*. 

This is just a toy example for illustrative purposes, we are looking forward to receive implementations of much more refined controllers and models!

Recording/setting rely on instructions transmitted between the Solver and the Controller, all the helper functions for the communication are encapsulated in ```communication.py```. These helper functions are designed to be generic and should work out-of-the-box, this means that you can just copy this script and use it to implement your use-case. <br /><br /> 

## How to adapt this example to other use-cases
In order to work with our [Generic Coupling API](#generic-coupling-api), controllers and models need to support certain functions (they are part of `communication.py`). These functions are not set in stone and can be adaptated according to the users needs.

### Model
`can_be_set`:  list of parameters of the model that can be modified by the controller

`can_be_gotten`: returns the list of states that can be recorded and reported.

Example code in `Tsolver.py` that uses those functions:
```python
sidecar.canbegotten = ['Tpoint', 'Tvol']
sidecar.canbeset = ['Tsource', 'SARsource', 'k', 'sourcescale', 'tend']
```
`record`: retrieve the values of certain variables (the ones that *can_be_gotten*) at a given time point

`apply_set`: set the value of some parameters of the model (the ones that *can_be_set*)

`wait_if_necessary`: do not iterate beyond this time point unless "continue" signal is received

### Controller

In this example, the Controller uses these set of functions (defined in `communication.py`) to control the recording/retrieval of variables, and the timing of execution. For example:

`record`: record the value of a variable at a at a given time point (a variable that *can_be_gotten*)

`wait_for_me_at`: pause the execution at a certain time point

`set_now`: set the value of a parameter of the model (a parameter that *can_be_set*)

`get`: retrieve the value of the recorded variable

`continue_until`: continue the iterations until the desired time point

Both the Model and Controller can make use of additional functions, such as `start` and `finish`, to send start and end signals.<br /><br /> 

## Generic Coupling API
The Coupling API has been designed to allow closed-loop simulations in [o<sup>2</sup>S<sup>2</sup>PARC](https://docs.osparc.io/#/) for different kinds of control applications. This API is generic and allows the combination of different physiological models and controllers contributed by the community and onboarded on o<sup>2</sup>S<sup>2</sup>PARC through [dedicated Nodes](https://docs.osparc.io/#/docs/submission). 

You are welcome to contact us for more information and suggestions, at support@osparc.io. Please mention "Control API" in the subject.
