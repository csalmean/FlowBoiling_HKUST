# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 13:04:17 2021

Main control code for Flow boiling experiments
Most functions are carried out in adjoining scripts. This script just ties everything together.

@author: Chris
"""

"""
Imports
"""
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from __init__ import *
import time

"""
Setup
- Ask user to determine specific details of this run so logger and control software can act accordingly""" 
while True:
    save=input('Save results?\n[y/n]\n')
    if save.upper()=='Y':
        save=True
        chip_name=input('Chip name?\n')
        break
    
    elif save.upper()=='N':
        save=False
        chip_name='plc'
        break
    
    else:
        print('Please choose from the options above.')
        continue

while True:
    dummy=input('Dummy run?\n[y/n]\n')
    if dummy.upper()=='Y':
        dummy=True
        break
    
    elif dummy.upper()=='N':
        dummy=False
        break
    else:
        print('Please choose from the options above.')
        continue

while True:
    mode=input('Mode?\n[M: Manual control only\nC: Calibration\nE: Experimental run\nF: Friction]\n')
    if mode.upper() == 'E':
        while True:
            flowrate=input('Intended flowrate? [ml/min]\n')
            direction=input('Flow direction? [fw/bw/n]\n')
            
            if direction.upper() == 'N':
                folder_name=''.join([chip_name,"_fw_",flowrate,"ml_min"])
                break
            elif direction.upper() == 'FW' or direction.upper() == 'BW':
                folder_name=''.join([chip_name,"_",direction,"_",flowrate,"ml_min"])
                break
            else:
                print('Please choose from the options above.')
                continue
        
        configurator=exp_config_dictionary(save,folder_name,dummy)
        break

    elif mode.upper() == 'C':
        folder_name=''.join([chip_name,"_cal"])
        configurator=cal_config_dictionary(save,folder_name,dummy)
        print(f'Calibration started at {time.asctime()}')
        break
    
    elif mode.upper() == 'M':
        folder_name=''.join([chip_name,"_man"])
        configurator=man_config_dictionary(save,folder_name,dummy)
        break
    
    elif mode.upper() == 'F':
        folder_name=''.join([chip_name,"_f"])
        configurator=friction_config_dictionary(save,folder_name,dummy)
        break

    else:
        print('Configuration failed. Please choose from the above options.')
        continue

"""
Instantiation
- Use configuration file to find global objects which must be created, set them
all up with links to each other, then activate them.    
"""
# Create manager for experiment
man=module_manager()

# hardware must be set up before modules. Otherwise they have nothing for
# modules to refer to.
hardwares=[]
for name, settings in configurator.hardware.items():
    modtype=eval(settings['Type'])
    globals()[name]=modtype(name,man,**settings['kwargs'])
    hardwares.append(globals()[name])

modules=[]
for name, settings in configurator.modules.items():
    modtype=eval(settings['Type'])
    globals()[name]=modtype(name,man,**settings['kwargs'])
    modules.append(globals()[name])

"""
Processing
- Activate asyncronous tasks, assign all to manager so they can be stopped after their usefulness is up.
"""

tasks=[]
tasks.append(asyncio.create_task(man.process()))

for hardware in hardwares:
    tasks.append(asyncio.create_task(hardware.process()))
    
for module in modules:
    tasks.append(asyncio.create_task(module.process()))

man.tasks=tasks