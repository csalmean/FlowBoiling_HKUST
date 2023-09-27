# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 12:55:22 2021

Reusable code for generic, controllable hardware object.

All controllable hardware (pump, PSUs, DAQs, Arduinos) have some things in common:
    - name, address
    - setpoint
    - method to manipulate
    - output to logger
    - limits of control

@author: Chris Salmean
"""
import asyncio

import pyvisa as visa
import serial
import numpy as np
import re

class serial_hardware(object):
    def __init__(self, name, manager, **kwargs):
        self.name=name
        self.address=kwargs['address']
        
        self.status='Initialising 0'
        self.manager=manager
        self.manager.hardware_dict[self.name]=[self,self.status]
        
        self.dummy=kwargs['dummy']
        
        self.triggered = asyncio.Event()
        
        self.loop=asyncio.get_event_loop()
        self._shutdown=asyncio.Event(loop=self.loop)
        
        if self.dummy==False:
            self.status='Connecting 0'
            
            try:
                # Perform connection step, depending if visa or serial connection is used.
                if kwargs['method']=='visa':
                    rm=visa.ResourceManager()
                    self.ser=rm.open_resource(self.address)
                    
                    self.status='Connecting 1'
                    
                elif kwargs['method']=='serial':
                    COMport='COM'+(''.join(filter(str.isdigit, self.address)))
                    self.ser=serial.Serial(
                        port=COMport,
                        baudrate=9600,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS)
                    
                    self.write_terminator='\r'
                    self.read_terminator='\r\n'
                    
                    self.status='Connecting 1'
                    
            except:
                self.status='Connecting 2'
    
class controlled_device(object):
    def __init__(self, name, manager, **kwargs):
        self.name=name
        self.manager=manager
        self.status='Initialising 0'
        
        self.manager.hardware_dict[self.name]=[self,self.status]
        self.manager.control_dict[self.name]=[self]
        
        importstring='from __main__ import ' + kwargs['controller']
        exec(importstring)
        self.controller=eval(kwargs['controller'])
        
        self.controller.devices[self.name]=self
        
        self.home=np.array([kwargs['home']])
        self.SP=np.array([kwargs['SP']])
        self.last_SP=np.array([0])
        
        self.PV=self.SP
        self.CV=self.SP
        
        self.manager.recorded_variables[self.name]={'SS':['SP'],
                                                'USS':['SP'],
                                                'disp_cont':['SP']}
        if 'safe_position' in kwargs.keys():
            self.manager.safety[name]=self
            self.safe_pos= kwargs['safe_position']
        
        self.PID=kwargs['PID']
        self.active=False
        
        if 'stepping' in kwargs.keys():
            self.stepping=True
            self.step_size=kwargs['step']
            
            self.fine=False
            self.fine_counter=0
        
        if self.PID==True:
            modelist=['SS','USS','disp_cont']
            for mode in modelist:        
                self.manager.recorded_variables[self.name][mode].insert(0,'PV')
                self.manager.recorded_variables[self.name][mode].append('CV')
            
            # set target object from within device
            importstring='from __main__ import '+kwargs['target_sensor']
            exec(importstring)
            self.target=eval(kwargs['target_sensor'])
            self.target_attr=kwargs['target_attr']
            
            self.kP=kwargs['kP']
            self.kI=kwargs['kI']
            self.kD=kwargs['kD']
            
            self.Int=kwargs['Int']
            self.Der=kwargs['Der']
            self.int_max=kwargs['int_max']
            self.int_min=kwargs['int_min']

        if 'limits' in kwargs:
            if 'H' in kwargs['limits'].keys():    
                self.max= kwargs['limits']['H']
            
            if 'L' in kwargs['limits'].keys():    
                self.min= kwargs['limits']['L']
                
        self.loop=asyncio.get_event_loop()
        self._shutdown=asyncio.Event(loop=self.loop)
        self.processed=asyncio.Event()
        self.new_values=asyncio.Event()
        
        self.status = 'Intialising 1'
        print(f'{self.name} activated')
        
    def calculate_response(self):
        # This is the PID controller. Use with care, as response can easily become unstable or can cause very sudden changes which can't be handled by the hardware.
        
        #re-evaluate self.PID, as it may have been changed by manual input.
        #due to nature of keylogger, manual input will be a number (0 or 1)
        # need to re-adjust to be boolean
        
        if self.PID==1: 
            self.PID=True
        elif self.PID==0:
            self.PID=False
        
        
        if self.PID==False:
            self.status = 'limits 0'
            if 'max' in dir(self):
                if self.SP[-1]>self.max:
                    print(f'{self.name} SP exceeds maximum')
                    self.SP[-1]=self.max
                    
            if 'min' in dir(self):
                if self.SP[-1]<self.min:
                    print(f'{self.name} SP deceeds minimum')
                    self.SP[-1]=self.min
            
            self.CV=self.SP
            # only send command if the SP has changed
            if self.SP!= self.last_SP: 
                self.status = 'Setting 0'
                self.set_actual(self.SP[-1])
                self.last_SP=self.SP
        
        else:
            self.status='PID 0'
            # PV is process variable, i.e. pressure at a valve
            # CV is the controlled variable, i.e. valve angle
            # SP is in terms of process variable (i.e., pressure)
            
            # If we change the PV or SP then angle changes as a response
            # If we want to actually directly change angle, must manipulate CV
            
            # use self.PV and self.SP to calculate new CV then execute
            # print(f'{self.name} SP: {self.SP}, PV:{self.PV}')
            # print(f'{self.name} calculating response')
            
            self.SP=self.target.SP
            error = self.SP[-1]-self.PV[-1]
            self.P = self.kP * error
            
            self.Int +=error
            if self.Int > self.int_max:
                  self.Int = self.int_max
                  
            elif  self.Int < self.int_min:
                  self.Int = self.int_min
            self.I = self.kI * self.Int
            
            self.D = -self.kD * (error-self.Der)
            self.Der = error
            
            self.CV= np.add(self.CV,np.array([self.P + self.I + self.D]))
            # print(f'P: {self.P}, I: {self.I}, D: {self.D}, CV: {self.CV}')
            
            self.status = 'Limits 0'
            if 'max' in dir(self):
                if self.CV[-1]>self.max:
                    print(f'{self.name} CV exceeds maximum. Set to {self.max}')
                    self.CV[-1]=self.max
                    
            if 'min' in dir(self):
                if self.CV[-1]<self.min:
                    print(f'{self.name} CV deceeds minimum. Set to {self.min}')
                    self.CV[-1]=self.min
            
            if self.active==True:
                self.status = 'setting 0'
                self.set_actual(self.CV[-1])
    
    def return_home(self):
        # Simply moves the controlled object back to its home position
        self.SP=self.home
        self.set_actual(self.SP[-1])
        
    async def process(self):
        try:
            while not self._shutdown.is_set():
                self.status= 'waiting 0'
                await self.controller.processed.wait()
                await asyncio.sleep(0.1)
                self.status='responding 0'
                self.calculate_response()
                self.processed.set()
                self.new_values.set()
                
        except:
            self.status=re.sub('\d','2',self.status)
    
    def step(self, step):
        # Move to the next step (i.e. for PSU, increase power) after SS has been recorded.
        self.SP=np.array([step * self.step_size])
    
    def stop(self):
        try:
            self.set_actual(self.safe_pos)
        except:
            pass
        
        self.deactivate()
        
        self._shutdown.set()
        
        
        