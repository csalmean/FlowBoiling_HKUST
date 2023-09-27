# -*- coding: utf-8 -*-
"""
Created on Mon May 17 19:03:33 2021

This module controls the Elektro-Automatik EA PS 2384 3B dual-source power supply. 
In my experiments, I wired the dual sources in series to allow higher voltages to be reached. Configured in code as only one voltage source.

The interface was beyond my own skill level, so I bypassed this using the 
(very fortunately) premade package by the absolute hero named Henrik Stroetgen.

If running this code on another computer, first download the package using 
pip install ea_psu_controller.

@author: Chris Salmean
"""
from hardware.hardware import *

import time
from ea_psu_controller.psu_ea import *

import numpy as np
import asyncio
import math

class EAPS2384(controlled_device):
    """ Hardware module for power supply Elektro-Automatik EA PS 2384 3B
    """
    def __init__(self, name,manager, **kwargs):
        super().__init__(name,manager, **kwargs)
        
        self.address=kwargs['address']
        COMport='COM'+(''.join(filter(str.isdigit, self.address)))
        
        self.dummy=kwargs['dummy']
        
        if self.dummy==False:
            self.ser=PsuEA(comport=COMport)
              
        self.setpoint=[0]
    
        # Immediately activate and set voltage to zero
        if self.dummy==False:

            self.ser.remote_on(output_num=0)
            time.sleep(0.1)
            self.ser.set_voltage(0, output_num=0)
            time.sleep(0.1)
            self.ser.output_on(output_num=0)
            time.sleep(0.1)
            self.ser.psu.close()

            self.status=str('Zeroing 1')
        
        # Establish connection to inverter if it exists
        if 'inverter' in kwargs.keys():
            self.inverted=True
            importstring='from __main__ import ' + kwargs['inverter']
            exec(importstring)
            self.inverter=eval(kwargs['inverter'])
            self.inverter.set_actual(0)
            
    def calculate_step_count(self,value):
        # Depending on the setpoint voltage, calculate what step of the experiment we should be on.
        step_count=math.floor((value/self.step_size)**2)
        return step_count
            
    def deactivate(self):
        print(f'{self.name} switching off')
        
        if self.dummy==False:
            try:
                self.ser.psu.open()
                time.sleep(0.2)
                self.ser.close(remote=True,output=True,output_num=0)
            except:
                time.sleep(0.2)
                self.ser.close(remote=True,output=True,output_num=0)

        if self.inverted==True:
            try:
                self.inverter.set_actual(0)
                self.inverter.ser.close()
                
            except:
                self.inverter.ser.open()
                self.inverter.ser.close()
    
    def crash(self):
        # This is just to test the software's error-handling ability. Since PSU can cause a lot of damage if used incorrectly, this is an important thing to test.
        self.status='Crashing 0'
        try:
            print(1/0)
        except:
            self.status='Crashing 2'
    
    async def restart(self):
        self.status='Restarting 0'
        COMport='COM'+(''.join(filter(str.isdigit, self.address)))
        try:
            self.ser.psu.close()
            try:
                self.ser=PsuEA(comport=COMport)
            except:
                pass
            
            task=asyncio.create_task(self.process())
            self.manager.tasks.append(task)
            self.ser.output_on(output_num=0)
            await asyncio.sleep(0.1)
            self.ser.close(remote=True,output=True,output_num=0)
            await asyncio.sleep(0.1)
            print('.')
            self.ser=PsuEA(comport=COMport)
            await asyncio.sleep(0.1)
            print('..')

            self.ser.remote_on(output_num=0)
            time.sleep(0.1)
            self.ser.set_voltage(0, output_num=0)
            time.sleep(0.1)
            self.ser.output_on(output_num=0)
            time.sleep(0.1)
            self.ser.psu.close()
            
            self.processed.set()
            self.processed.clear()
        except:
            pass

    def set_actual(self, value):
        self.status='setting 0'
        print(f'Changing {self.name} to {value}')
        if self.dummy== False:
            if self.inverted==True:
                if value >=80: # Inverter should be used at high powers. In my own work, it seemed like electromigration started at voltage >80V
                    self.inverter.set_actual(1)
                elif value <= 80:
                    self.inverter.set_actual(0)

            # need to divide by 2 because using both of the PSU channels in series
            value/=2

            self.ser.psu.open()
            self.ser.set_voltage(value, output_num=0)
            self.ser.psu.close()

        else:
            # just pretend it's happened.
            pass
    
    def step(self, step):
        # Increase the voltage to the next step. If the fine control function is toggled, steps will be much smaller.
        self.SP=np.array([(np.sqrt(((step*4)+self.fine_counter)/4) * self.step_size)])