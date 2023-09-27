# -*- coding: utf-8 -*-
"""
Created on Wed Oct  6 13:37:20 2021

This module controls the stepper.
Stepper control is somewhat harder than the other components, as the signals
must first be sent by serial to the controlling Arduino, and from there to 
the servomotors.

Must ensure that the Arduinos have the Stepper_con.ino code flashed.
Code can be found in same folder as this script.

@author: Chris
"""
from hardware.hardware import *

import asyncio
import pyvisa as visa
from collections import defaultdict
import time

class stepper(controlled_device):
    """ Arduino Uno hardware interface code. 
    """
    def __init__(self, name,manager, **kwargs):
        super().__init__(name, manager, **kwargs)
        self.current_position=kwargs['home']
        self.dummy=kwargs['dummy']
        
        self.address=kwargs['address']
        
        if self.dummy==False:
            self.status='Connecting 0'
            
            try:
                rm=visa.ResourceManager()
                self.ser=rm.open_resource(self.address)
                self.ser.read_termination='\n'
                
                print("Connected to stepper")
                self.status='Connecting 1'
   
            except: self.status='Connecting 2'
            
    def deactivate(self):
        print(f'{self.name} switching off')
        if self.dummy==False:
            self.ser.close()

    def set_actual(self, value):
        """
        Writes the direction and distance (in degrees) needed to arduino
        Internally sends i.e. 'Ox' or 'Cx' over the serial connection, where
        x is angle.
        """
        self.status=('setting 0')
        # calculate number of steps needed to move from old location to new location
        delta=2*(value-self.current_position)
        delta=round(delta,0)
        delta/=2
        
        if self.dummy==False:
            if delta>0:
                command= (''.join(('O'+str(delta))))
                self.ser.write(command)
                self.current_position=value
                print(f'Moving {self.name}')
            elif delta<0:
                command = (''.join(('C'+str(-delta))))
                self.ser.write(command)
                self.current_position=value
                print(f'Moving {self.name}')
            else:
                pass