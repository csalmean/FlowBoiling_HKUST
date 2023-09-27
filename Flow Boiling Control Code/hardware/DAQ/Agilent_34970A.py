# -*- coding: utf-8 -*-
"""
Created on Sun May 23 14:50:48 2021

Code to allow control of Agilent 34970A data acquisition unit.

Mode of operation for this DAQ:
    - During initialisation, establish connection and create list which can be 
        populated by devices
    - After devices are all set up, activate DAQ (configure channels and trigger model)
    - Wait for trigger signal from timer. When received, scan for specified number of sweeps.
    - Wait for DAQ to finish, then collect the data. Send to devices.
    
    - Need to reconfigure for high-speed measurement when doing burst measurements
    
@author: Chris Salmean
"""
import asyncio
import pyvisa as visa
import time
from collections import defaultdict

from hardware.hardware import *
from hardware.DAQ.general_DAQ import *

class Agilent34970A (DAU):
    def __init__(self,name,manager,**kwargs):
        super().__init__(name,manager,**kwargs)
        
        self.status= 'checking 0'
        
        self.ser.read_termination='\n'
        self.ser.write_termination='\n'
        
        # we make a buffer for USS/SS measurements
        try:
            self.ser.query('FETC?')
        except:
            pass
        
        self.ser.write('*RST') # reset DAQ
        
        idn=self.ser.query("*IDN?")
        print(f"Connected to: {idn}\n")
        
        cmd_list = ['*RST',
                    "*OPC?"]
        
        if self.dummy==False:
            for cmd in cmd_list:
                self.ser.write(cmd)
            
            self.status='checking '+str(self.ser.read())          
        else:
            print('Dummy DAU connected')
    
    def activate(self):
        self.status='activating 0'
        
        if self.dummy==False:
            for channel, commands in self.configuration_strings.items():
                self.scanlist+=str(channel)+str(',')
            
            self.scanlist=self.scanlist[:-1]
                
            cmd_list=[
                'ROUT:MON:STAT ON', # switch on monitor display on DAQ box
                "ZERO:AUTO ONCE,("+self.scanlist+')', # auto-zero at beginning of each burst
                'ROUT:SCAN ('+self.scanlist+')' # tell DAQ which channels to look at
            ]
            
            for cmd in cmd_list:
                self.ser.write(cmd)
            
            for channel, commands in self.configuration_strings.items():      
                for cmd in commands:
                    time.sleep(0.05)
                    self.ser.write(cmd)
                
            self.status='activating '+str(self.ser.query('*OPC?')) 
        
        else:
            self.status='activating 1'          

    async def send_to_sensors(self):
        # Sends readings to the appropriate sensor and allows the sensor to update itself.
        self.status='transmitting 0'        
        if self.dummy==False:
            
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
        # Trigger DAQ to collect the desired information from the sensor channels.
        cmd_list=[
            'ROUT:SCAN ('+self.scanlist+')',
            'FORM:READ:CHAN ON',
            "TRIG:COUN "+str(self.n_sweeps[self.state]),
            'INIT', # trigger reading to begin
            '*OPC?'] # tell DAQ we want it to inform us when finished
        
        self.first_reading_time=time.time()-self.start_time
        for cmd in cmd_list:
            self.ser.write(cmd)
        await asyncio.sleep(0.1)
        OPC=0
        while OPC!=1:
            await asyncio.sleep(0.1) # wait for DAQ to send 'finished' message
            try:
                OPC=int(self.ser.read())
            except:
                print('Waiting for DAQ')
        
        self.last_reading_time=time.time()-self.start_time
        
        # Now take raw data from DAQ and assign to the correct sensor channel
        self.data={}
        self.data['raw']=(self.ser.query('FETC?')).replace("\r", "").split(',')
        self.data['channels']=[self.data['raw'][i] for i in range(len(self.data['raw'])) if (i % 2)-1 == 0]
        self.data['readings']=[self.data['raw'][i] for i in range(len(self.data['raw'])) if (i % 2) == 0]
        self.data['zipped']=defaultdict(list)

        for number, channel in enumerate(self.data['channels']):
            self.data['zipped'][channel].append(self.data['readings'][number])
        
        self.status='triggering 1'
