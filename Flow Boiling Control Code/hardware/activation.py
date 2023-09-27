# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 12:38:18 2021

@author: Chris Salmean
"""
# activator class which can be set to activate any target module
class activator(object):
    def __init__ (self, name, manager, **kwargs):
        importstring='from __main__ import ' + kwargs['target']
        exec(importstring)
        
        self.target=eval(kwargs['target'])
        self.target.activate()
        
    async def process(self):
        pass