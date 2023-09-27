# -*- coding: utf-8 -*-
"""
Created on Wed Oct 13 14:10:57 2021

Contains class variables for generic data acquisition unit superclass. Agnostic of manufacturer etc.

@author: Chris Salmean
"""
import asyncio
import pyvisa as visa
import random
from hardware.hardware import *
import time
import re

class DAU(serial_hardware):
    def __init__(self,name,manager,**kwargs):
        super().__init__(name,manager,**kwargs)
        
        self.n_sweeps=kwargs['n_sweeps']
        
        self.configuration_strings={}
        self.scanlist='@'
        self.channel_dict = {}
        
        self.SS_bin={}
        self.state='USS'
        self.USS_count=kwargs['USS_count']
        self.SS_count=kwargs['SS_count']
        self.locked=True
        self._counter=0
        
        self.start_time=time.time()
        
    def determine_state(self):
      # check self to see if unsteady state (USS) or steady state (SS).
      # If SS has been activated, we need to lock this state for a number of counts.
      # If switching back to USs, also need to lock for a number of counts.
      
      if self.locked==False:
          USS_list=[i for i in self.SS_bin.values() if i == 'USS']
          if len(USS_list)>0:
              self.state='USS'
              
              print('*'*50)
              print('Step is taking longer than expected. Check experimental parameters are safe then manually proceed.')
              print('*'*50)
        
          else:
              self.state='SS'
              self.locked=True
              self._counter=0
           
      else:
          self._counter+=1
          if self.state=='SS':
              if self._counter>=self.SS_count:
                  self.state='USS'
                  self._counter=0
                  
          elif self.state=='USS':
              if self._counter>=self.USS_count:
                  self.locked=False
        
    async def process(self):
        # Wait for timer or keyboard to trigger DAQ, then check for steady or unsteady state. Then takes readings and tells sensor objects to update themselves.
        try:
            while not self._shutdown.is_set():
                
                self.status='waiting 0'
                await self.triggered.wait()
                print('DAQ triggered. Please wait')
                self.status='determining state 0'
                self.determine_state()
                if self.dummy==False:
                    self.status='triggering 0'
                    await self.trigger()
                    
                self.status='distributing 0'
                await self.send_to_sensors()
                self.triggered.clear()
                
        except:
            self.status=re.sub('\d','2',self.status)
            
    def stop(self):
        # shuts self down
        print(f'{self.name}: shutting down')
        self._shutdown.set()
        
        if self.dummy==False:
            self.ser.close()