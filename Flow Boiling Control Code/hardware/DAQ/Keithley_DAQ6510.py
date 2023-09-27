# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 12:23:09 2021

Code to allow control of Keithley DAQ6510

Mode of operation for this DAQ:
    - During initialisation, establish connection and create list of sensors which can be 
        populated by devices
    - After devices are all set up, activate DAQ (configure channels and trigger model)
    - Wait for trigger signal from timer. When received, run scan for specified number of sweeps.
    - Wait for DAQ to finish, then collect the data. Send to sensor objects and allow them to update themselves.
    
@author: Chris Salmean
"""
import asyncio
import pyvisa as visa
import random
from collections import defaultdict

from hardware.hardware import *
from hardware.DAQ.general_DAQ import *
import time
import re

class DAQ6510(DAU):
    def __init__(self,name,manager,**kwargs):
        super().__init__(name,manager,**kwargs)

        self.ser.read_termination='\n'
        self.ser.write_termination='\n'
        
        # we first create a buffer for USS/SS measurement
        try:
            self.ser.write('TRAC:DATA?')
        except:
            pass
        
        self.ser.write('*RST')
        
        idn=self.ser.query("*IDN?")
        print(f"Connected to: {idn}\n")
        
        self.status='setting buffer 0'
        cmd_list = [
                    ":TRAC:CLE",
                    ":TRAC:POIN 10000"]
        
        if self.dummy==False:
            for cmd in cmd_list:
                self.ser.write(cmd)
            
        else:
            print('Dummy DAU connected')
    
    def activate(self):
        self.status='activating 0'
        
        if self.dummy==False:
            for channel, commands in self.configuration_strings.items():
                for cmd in commands:
                    self.ser.write(cmd)
            
                self.scanlist+=str(channel)+str(', ')
            
            cmd_list=[
               "ROUT:SCAN:CRE ("+self.scanlist+")",
               "FORM:ASC:PREC 6",
               "AZER:ONCE",
           ]             
            
            for cmd in cmd_list:
               self.ser.write(cmd)
               
        else:
            self.status='activating 1'

    async def send_to_sensors(self):
        self.status='transmitting 0'        
        if self.dummy==False:
            # Update stored 'signal' variables for each connected sensor
            for channel,reading in self.data['zipped'].items():
                self.channel_dict[int(channel)].signal=[float(ele) for ele in reading]
                self.channel_dict[int(channel)].updated.set()
            
        else:
            #record time of first reading
            self.first_reading_time=time.time()-self.start_time
            
            for channel, sensor in self.channel_dict.items():
                sensor.signal=[]       
            await asyncio.sleep((0.3*self.n_sweeps[self.state]))
            
            #record time of last reading
            self.last_reading_time=time.time()-self.start_time
            # Use a dummy data generator
            for i in range(int(self.n_sweeps[self.state])):
                for channel, sensor in self.channel_dict.items():
                    sensor.signal.append(random.uniform(0,80))        
            
            for channel, sensor in self.channel_dict.items():
                sensor.updated.set()
                
            # print(f'DAU receiving {self.n_sweeps[self.state]} rows of data')
        self.status= 'transmitting 1'

    async def trigger(self):
        self.status="triggering 0"
        try:
            self.ser.query('FETC?') 
        except:
            pass
        
        cmd_list=[
            'TRAC:CLE', # empty buffer
            "ROUT:SCAN:COUN:SCAN "+str(self.n_sweeps[self.state]),
            ":INIT", # trigger DAQ to beign taking readings
            '*OPC?'] # tell DAQ to send a signal once it has finished
        
        self.first_reading_time=time.time()-self.start_time
        
        for cmd in cmd_list:
            self.ser.write(cmd)
            
        await asyncio.sleep(0.1)
        
        OPC=0
        while OPC!=1:
            await asyncio.sleep(0.1)
            try:
                OPC=int(self.ser.read()) # wait until the DAQ responds with 'finished' signal
            except:
                print('Waiting for DAQ')
        self.last_reading_time=time.time()-self.start_time
        
        buffer_length=self.ser.query('TRAC:ACT?')

        # Load readings and process by matching each value to a sensor channel.
        self.data={}
        self.data['raw']=(self.ser.query('TRAC:DATA? 1, '+str(buffer_length)+
                                  ', "defbuffer1", CHAN, READ')).split(',')
        self.data['channels']=[self.data['raw'][i] for i in range(len(self.data['raw'])) if i % 2 == 0]
        self.data['readings']=[self.data['raw'][i] for i in range(len(self.data['raw'])) if (i % 2)-1 == 0]
        self.data['zipped']=defaultdict(list)
        for number, channel in enumerate(self.data['channels']):
            self.data['zipped'][channel].append(self.data['readings'][number])
        self.status='triggering 1'
