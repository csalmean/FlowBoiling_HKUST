# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 13:50:20 2021

This module controls the inverter.
This works by sending commands to an Arduino, which has been preconfigured to respond to certain serial commands.

must ensure that the Arduino in question has a DC-AC_Inverter.ino code flashed. Code can be found in the same folder as this script.

@author: Chris Salmean
"""

from hardware.hardware import *

import asyncio
import pyvisa as visa
from collections import defaultdict
import time

class inverter(controlled_device):
    """ Arduino Uno hardware interface code. 
    """
    def __init__(self, name,manager, **kwargs):
        super().__init__(name, manager, **kwargs)
        self.current_position=kwargs['home']
        self.dummy=kwargs['dummy']
        
        self.address=kwargs['address']
        self.active=False
        
        if self.dummy==False:
            self.status='Connecting 0'
            
            try:
                rm=visa.ResourceManager()
                self.ser=rm.open_resource(self.address)
                self.ser.read_termination='\n'
                
                print("Connected to inverter")
                self.status='Connecting 1'
   
            except: self.status='Connecting 2'
            
    def deactivate(self):
        print(f'{self.name} switching off')
        pass

    def restart(self):
        try:
            time.sleep(0.5)
            self.ser.open()
            print('Successfully restarted DCAC')
        except:
            print('DCAC still failed.')
            pass
        
        self.set_actual(self.current_position)
        

    def set_actual(self, value):
        """
        Writes just 'a' or 'b' to the Arduino. If the arduino receives 'a', it begins inverting the current. If it receives 'b', it stops.
        """
        self.status=('setting 0')
        
        if self.dummy==False:
            try:
                if value==1 and self.active==False:
                    command= ('a')
                    self.ser.write(command)
                    self.current_position=value
                    print(f'Inverter activated')
                    self.active=True
                    
                elif value==0 and self.active ==True:
                    command = ('b')
                    self.ser.write(command)
                    self.current_position=value
                    print(f'Inverter deactivated')
                    self.active=False
                else:
                    pass
            except:
                self.status=('setting 2')