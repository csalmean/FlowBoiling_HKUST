# FlowBoiling_HKUST
Software suite developed in 2021-2022 for autonomous data acquisition and control in closed-loop flow boiling experiments.  Developed by Dr. Christopher Salmean at the Hong Kong University of Science and Techology.

Closed-loop flow boiling setup consisting of the following controllable hardware, assembled as a flow loop as shown in the figure below. For more information about experimental setup, please see my [published works on flow boiling](https://scholar.google.com/citations?user=EifbxgwAAAAJ&hl=en).

Pump: HNP Mikrosystems mzr-2921<br>
Stepper motor controlled by Arduino Uno (generic motor)<br>
DC power supply: Elektro-Automatik PS2000B, can also swap for HP 33120A signal generator and high-frequency amplifier.<br>
DC-AC full-bridge MOSFET inverter controlled by Arduino Uno (made in-house)<br>
Data Acquision Unit: Keithley Instruments DAQ6510, can also swap for Agilent 34970A.<br>

Device: fabricated in HKUST's Nanosystem Fabrication Facility. Silicon chips with 5x aluminium heaters in series, wire-bonded to custom PCB in series with shunt resistor.

![Flow loop](https://github.com/csalmean/FlowBoiling_HKUST/assets/133036780/3978b613-2ac0-4fd6-9a81-5d0935e27132)

Here's a photograph of the experimental setup:
![Setup_blurred](https://github.com/csalmean/FlowBoiling_HKUST/assets/133036780/e02c4f9a-dc87-4e67-9ae9-8b94b2a382de)

Since the code needed to respond to user inputs, monitor alarms, send control commands and receive data, it was decided to operate using asynchronous programming.

A summary of the various modules and their operation is shown below:
![Code diagram 1](https://github.com/csalmean/FlowBoiling_HKUST/assets/133036780/22ca0d7f-2b15-46cc-89f6-db9e01f06a78)

Since everything was written for my own experimental setup, it may take some work to get it working on your own hardware. However, I hope the annotation and explanatory diagrams above can help you to modify it as needed. I suggest you start with __main__ and the configuration files, and adjust the hardware as necessary.
