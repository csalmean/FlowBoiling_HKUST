# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 11:00:24 2021

Timer module. Outputs trigger signal to DAU controller.

Timer contains logic bins for steady-state indicators (values set by devices).
When all indicators are positive, the timer changes frequency for a set number
of pulses.

Can also configure timer to send trigger when manual command sent.

@author: Chris
"""
import asyncio
import importlib
import re

from modules.module import *

class timer(core_module):
    def __init__(self, name,manager,**kwargs):
        super().__init__(name,manager,**kwargs)
        
        importstring='from __main__ import ' + kwargs['target']
        exec(importstring)
        self.target=eval(kwargs['target'])
        
        self.mode= kwargs['mode']
        
        if self.mode =='periodic':
            self.SS_target=eval(kwargs['SS_target'])
            
            self.intervals=kwargs['intervals']
    
        elif self.mode =='triggered':
            self.triggered=asyncio.Event()
    
    def determine_interval(self):
        print(f'Triggered: {self.SS_target.state}')
        # use SS_bin to determine intervals
        self.interval=self.intervals[self.SS_target.state]
        self.target.triggered.set()

    def manual_trigger(self):
        print('tim triggred')
        self.target.triggered.set()

    async def process(self):
        try:
            while not self._shutdown.is_set():
                if self.mode == 'periodic':
                    self.determine_interval()
                    self.status="Waiting 0"
                    
                    await asyncio.sleep(self.interval)
                    
                    self.status="Waiting 1"
                    
                elif self.mode == 'triggered':
                    self.status="Waiting 0"
                    
                    await self.triggered.wait()
                    self.target.triggered.set()
                    self.triggered.clear()
                    
                    self.status="Waiting 1"
                    
        except:
            self.status=re.sub('\d','2',self.status)