# -*- coding: utf-8 -*-
"""
Created on Wed Oct  6 14:02:09 2021

Controller.
Every time the sensors update, the controller will take relevant values from them and
distribute to the controllable hardware (so long as not locked).

Contains dictionary collection of controllable hardware and relevant values.
Logger can interface with just this module to get information.

@author: Chris Salmean
"""
from modules.module import *
import time
import asyncio
import numpy as np
import re

class controller (core_module):
    def __init__(self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        self.manager.controller=self
        
        importstring='from __main__ import ' + kwargs['SS_target']
        exec(importstring)
        self.SS_target=eval(kwargs['SS_target'])

        # Get list of all sensors
        self.sensors=manager.sensor_dict
        self.devices={}
        self.processed=asyncio.Event()
        
        self.state='USS'
        self.step_count=0
    
    def change_attribute(self,device,attribute,value):
        # Can be used to directly alter the parameters of a controlled device
        if attribute != None:
            if device in self.devices.keys():
                value=np.array([float(value)])
                if self.devices[device].PID==True:
                    # Device stops using CV and starts using SP. i.e., PID control is cancelled.
                    self.devices[device].PID=False
                    
                # change setpoint to new value
                setattr(self.devices[device],attribute,value)
                if getattr(self.devices[device],'stepping',False) == True:
                    # If we jump to i.e. 50V, we need to change te current step count to reflect this. This is because the step size is not uniform (decreases in size as step count increases)
                    self.step_count=self.devices[device].calculate_step_count(value)
                print(f'Actor {device}.{attribute} changed to {value}, step changed to {self.step_count}')   
                
            elif device in self.sensors.keys():
                value=np.array([float(value)])
                
                setattr(self.sensors[device],attribute,value)
                print(f'Sensor {device}.{attribute} changed to {value}')    
            
    async def process(self):
        try:
            while not self._shutdown.is_set():
                self.status= 'waiting for sensors 0'
                for sensor in self.sensors.values():
                    await sensor.processed.wait()                
                    sensor.processed.clear()
                    
                for device in self.devices.values():
                    device.processed.clear()
                
                self.status= 'gathering 0'
                

                if self.state!= self.SS_target.state:
                    if self.SS_target.state=='USS':
                        self.step(1)
                        
                self.state=self.SS_target.state
                
                if self.state == 'SS':
                    self.processed.set()
                    self.processed.clear()
                else:
                    self.status= 'distributing 0'
                    self.update_sensors()
                    self.processed.set()    
                    self.processed.clear()
                
                for device in self.devices.values():
                    self.status='waiting for devices 0'
                    await device.processed.wait()            
        except:
            self.status=re.sub('\d','2',self.status)
    
    def step(self,value):
        # Alter the values of the stepping devices (step forwards or backwards)
        self.step_count+=value
        if self.step_count<0:
            print('Cannot go back further.')
            self.step_count=0
            
        # need to determine which devices to step.
        for name, device in self.devices.items():
            if getattr(device,'stepping',False) == True:
                if device.fine==True:
                    device.fine_counter+=value
                    if (device.fine_counter>=4)or(device.fine_counter<0):
                        device.fine_counter=0
                    else:
                        self.step_count-=value
                        
                print(f'Setting {name} to step {self.step_count}. Fine increment = {device.fine}, step {device.fine_counter}')
                
                device.step(self.step_count)
    
    def update_sensors(self):     
        # print('cont distributing PV values to devices')
        for device in self.devices.values():
            if device.PID==True:
                device.PV=getattr(device.target,device.target_attr)      
    
    