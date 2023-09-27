# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 17:42:00 2021

This module controls the HP-33120A signal generator.

Use to generate an AC signal at high frequency (massively reduces electromigration).
Use high-frequency amplifier to generate sufficient power. 

@author: Chris Salmean
"""
from hardware.hardware import *

import pyvisa as visa
import time
import numpy as np
import asyncio
import math

class HP33120A(controlled_device,serial_hardware):
    def __init__(self, name,manager, **kwargs):
        
        controlled_device.__init__(self,name,manager, **kwargs)
        
        serial_hardware.__init__(self,name,manager, **kwargs)

        self.channel_dict={}
        
        # Signal is amplified, so we need to multiply when recording device input power
        self.multiplier=kwargs['amplifier_multiplier']
        
        self.frequency=1.0E+5
        
        self.ser.read_termination='\n'

        # self.ser.write('*RST')
        idn=self.ser.query("*IDN?")
        print(f"Connected to: {idn}\n")
        

        # Immediately set voltage to zero
        cmd_list = [
            'VOLT:UNIT VRMS',
            'APPL:SIN 1.0E+5, MIN, 0']
        
        if self.dummy==False:
            for cmd in cmd_list:
                self.ser.write(cmd)
    
    def calculate_step_count(self,value):
        # Find the step we are on, if a specific voltage has been set
        step_count=math.floor((value/self.step_size)**2)
        return step_count
    
    def deactivate(self):
        print(f'{self.name} switching off')
        cmd_list = ['APPL:SIN 1.0E+5, 0.02, 0']
        
        if self.dummy==False:
            for cmd in cmd_list:
                self.ser.write(cmd)
        
            self.ser.close()

    def set_actual(self, value):
        self.status = 'setting 0'
        print(f'Changing {self.name} to {value}')
        if self.dummy== False:
            # serial commands
            
            value/=self.multiplier
            voltagestring='{:e}'.format(value).upper()

            cmd_list = ['APPL:SIN 1.0E+5, '+voltagestring+', 0']
            for cmd in cmd_list:
                self.ser.write(cmd)
                
        else:
            # just pretend it's happened.
            pass
         
    def step(self, step):
        # Adjust setpoint depending what step we are on. This is needed as power increases with square of voltage. For approx. linear power increase, need voltage to increase with
        # square root of step number
        self.SP=np.array([np.sqrt(step) * self.step_size])