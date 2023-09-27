# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 12:37:12 2021

Code for virtual sensors. Use data from physical sensors and perform calculations to yield more information.
For example, can configure temeprature sensor to take current and voltage from
a heater and shunt, therefore calculating resistance and temperature of the heater.

The virtual sensors must wait until the physical sensors have finished updating.
For this purpose, we employ asyncronous events.

@author: Chris Salmean
"""
import asyncio
import random
import numpy as np
import re

class Virtual_Sensor(object):
    def __init__(self, name, manager, **kwargs):
        self.name=name
        
        self.manager=manager
        self.status='initialising 0'
        self.manager.hardware_dict[self.name]=[self,self.status]
        self.manager.sensor_dict[self.name]=self
        
        self.SP=np.array([kwargs['SP']])    
        self.signal=0
                
        if kwargs['SS']==True:
            # If the DAQ is going to monitor this sensor for steady state, must add sensor to SS bin of DAQ.
            self.DAQ.SS_bin[self.name]='USS'
            
            self.history=[]
            hist_length=kwargs['SS_time']*self.DAQ.n_sweeps['USS']
            
            for i in range(0,hist_length):
                n = random.randint(1,100)
                self.history.append(n)
        
        self.alarms = kwargs['alarms']
        
        self.loop=asyncio.get_event_loop()
        self._shutdown=asyncio.Event(loop=self.loop)
        self.processed=asyncio.Event()
        self.new_values=asyncio.Event()
        
        self.inputlist=[]
        
    def check_alarms(self):
        # Alarms function the same way as they do for physical sensors.
        for alarm in self.alarms:
            alarm_type=alarm[0]
            value=alarm[2]
            action=alarm[3]
            triggered=False   
            
            if alarm_type=='H':
                alarm_variable=eval('self.'+alarm[1])
                cond=np.where(alarm_variable>value,True,False)
                if True in cond:
                    triggered=True
                
            elif alarm_type=='L':
                alarm_variable=eval('self.'+alarm[1])
                cond=np.where(alarm_variable>value,True,False)
                if True in cond:
                    triggered=True
       
            if triggered==True:
                if action == 'Alert':
                    c1= '\x1b[1;30;43m'
                    c2='\x1b[0m'
                    
                elif action == 'Stop':
                    c1= '\x1b[1;37;41m'
                    c2 = '\x1b[0m'   
                    
                self.manager.alarm(self,alarm_type,action)
                print(c1+f'{self.name} Alarm triggered. {action}'+c2)
    
    def determine_SS(self):
        if 'history' in dir(self):            
            self.history.extend(eval('self.'+self.primary))
            self.history=self.history[len(self.primary)::]
            print(self.history)
            
            chan_max=(np.max(self.history))
            chan_min=(np.min(self.history))
            chan_mean=(np.mean(self.history))
            
            chan_range=(chan_max-chan_min)/chan_mean
            print(f'{self.name} range: {chan_range}')
            if chan_range<1.6:
                self.state='SS'
                self.DAQ.SS_bin[self.name]='SS'
            
            else:
                self.state='USS'
                self.DAQ.SS_bin[self.name]='USS'
                
            # so when all variables in the bin say 'SS', DAQ, timer and logger change state.
            print(chan_range)
    
    async def process(self):
        try:
            while not self._shutdown.is_set():
                # The virtual sensor needs to wait for its inputs to change.
                # Inputting objects aren't 'aware' that they are being monitored by the virtual sensor
                # When they finish processing their signals to readings, they set themselves as
                # done. Virtual sensor waits for all to be done, then performs calculations.
                self.status = 'waiting 0'
                for input_trigger in self.inputlist:
                    await input_trigger.wait()
                self.status= 'processing 0'
                self.process_data()
                self.status='checking 0'
                self.check_alarms()
                self.status='SS_calc 0'
                self.determine_SS()
                self.status= 'transmitting 0'
                self.transmit()
                   
                for input_trigger in self.inputlist:
                    input_trigger.clear()
            
        except:
            self.status=re.sub('\d','2',self.status)
            
    def stop(self):
        print(f'{self.name}: shutting down')
        self._shutdown.set()
        
    def transmit(self):
        # print(f'{self.name} new readings available')
        pass

class combined_Q(Virtual_Sensor):
    "Code to calculate power evolved in the microheater"
    def __init__ (self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        # Point sensor towards the relevant heater(s) and shunt(s)
        self.heaterlist=[]
        
        for pair in kwargs['inputlist']:
            for item in pair:
                importstring='from __main__ import ' + item
                exec(importstring)
                
                trigger_name='virt_trig'+self.name
                if trigger_name not in dir(eval(item)):
                    setattr(eval(item),trigger_name,asyncio.Event())
                    trigger_name=eval(item).name + '.' + trigger_name
                    self.inputlist.append(eval(trigger_name))
                
            self.heaterlist.append((eval(pair[0]),eval(pair[1])))
        
        self.manager.recorded_variables[self.name]={'SS':kwargs['output'],
                                                    'USS':kwargs['output'],
                                                    'disp_sensing':kwargs['output']}
        
        for attrlist in self.manager.recorded_variables[self.name].values():
            for attribute in attrlist:
                setattr(self,attribute,0)  
        
        self.status='initialising 1'

    def process_data(self):
        """to function in both series and parallel, want to calculate power for each
        heater and then sum, rather than adding voltages then calculating.
        """
        self.Q=[0]*len(self.heaterlist[0][0].V)
        
        for count, pair in enumerate(self.heaterlist):
            heater_v=pair[0].V
            shunt_v=pair[1].V
            shunt_r=pair[1].R
            power=np.divide(np.multiply(heater_v,shunt_v),shunt_r)
            
            self.Q=np.add(self.Q,power)
            
        # NEED TO SCALE BY NUMBER OF FUNCTIONING HEATERS IF PARALLEL
        self.processed.set()
        self.new_values.set()
        
class man_input(Virtual_Sensor):
    "virtual sensor which just takes an input value and passes as its reading"
    def __init__ (self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        self.primary=kwargs['primary']
        
        self.status='initialising 1'
        
    def alter(self, value):
        self.status= 'waiting 0'
        setattr(self,self.primary,[value])
        
        self.processed.set()
        self.status= 'waiting 1'
