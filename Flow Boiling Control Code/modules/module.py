# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 13:46:06 2021

The 'module' object. Contains code common to all modules.

@author: Chris
"""
import time
import asyncio
from collections import defaultdict

class core_module(object):
    def __init__(self, name, manager, **kwargs):
        self.name=name
        
        self.status=[self,"Startup 0"]
        self.manager=manager
        self.manager.module_dict[self.name]=[self,self.status]
    
        # self.is_dummy=kwargs['is_dummy']

        self.loop=asyncio.get_event_loop()
        self._shutdown=asyncio.Event(loop=self.loop)
        
        self.status="Startup 1"
    
    async def restart(self):
        self.status="restart 0"
        if not self._shutdown.is_set():
            await self.process()
           
    def stop(self):
        # shuts self down
        print(f'{self.name}: shutting down')
        self._shutdown.set()
    