# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 08:18:30 2021

Keyboard monitor. Constantly monitors keyboard input and waits for the right arrow key to be pressed. Then compares keyboard input to commands and executes.

Have to use this technique as could not get a graphical interface to work in
conjunction with anaconda. Configuration files are set up in a way that will hopefully
allow graphical interface in future.

Keeps track of the user's keystrokes. After the experiment has started, this is
how the user keeps control over the system.

@author: Chris Salmean
"""
import asyncio
import sys
import re

from pynput import keyboard as kb
from modules.module import *


class keylogger(core_module):
    def __init__(self,name,manager,**kwargs):
        super().__init__(name,manager,**kwargs)
        
        # Begin keyboard listener
        self.listener=kb.Listener(on_press=self.on_press)
        self.listener.start()

        self.input=""
        self.old_input=""
        self.message=''
        self.messagelist=[]   
        print('Keyboard monitor is active. Type HELP followed by right-arrowkey for instructions')
   
    def on_press(self,key):
        # If a key is pressed, record this input
        self.track_input(key)
        # print('{0} pressed'.format(key))   
        try:
            self.input+=key.char
        except:
            pass     
   
    async def process(self):
        try:
            while not self._shutdown.is_set():
                self.status="running 0"

                # Check for new input every 0.2 seconds
                await asyncio.sleep(0.2)
                
                if self.input != self.old_input:
                    c1='\33[45m'
                    c2='\33[0m'
                    print(c1+f"\r {self.input}"+c2,end="")
                    sys.stdout.flush()
                    self.old_input=self.input
        
        except:
            self.status=re.sub('\d','2',self.status)
        
    def stop(self):
        # shuts self down
        print(f'\n{self.name}: shutting down')
        self._shutdown.set()
        self.listener.stop()
    
    def track_input(self,key):
        try:
            if key == kb.Key.right:
                # If the right arrow key is pressed, check input against lsit of commands
                c1= '\33[42m'
                c2='\33[0m'
                self.status='processing input 0'
                
                # If anything has been typed which matches a predefined command, tell the manager that the command has been requested
                if self.input == 'quit':
                    self.manager.shutdown()
                
                elif self.input == 'trig':
                    self.manager.manual_trigger()
                    
                elif self.input[0:3] == 'inp':
                    value=float(self.input.split('_')[-1])
                    self.manager.manual_input(value)
                
                elif self.input[0:3] == 'set':
                    parameter=(self.input.split('_')[1])
                    value = (self.input.split('_')[-1])
                    self.manager.set_param(parameter, value)
                
                elif self.input== 'skip':
                    self.manager.step(1)
                    
                elif self.input== 'fine':
                    self.manager.toggle_fine()
                
                elif self.input== 'back':
                    self.manager.step(-1)
                
                elif self.input == 'help':
                    print('Welcome to the control code for flow-boiling experiments.'+
                          ' To set controllable variables, use the format, "set_device.parameter_value".'+
                          ' Device names can be found in the configuration dictionary or on the output table.\n'+' Can also type "trig" to trigger DAQ even if not at steady state. \n'+
                          ' To skip ahead to the next power increment or go back, use '+
                          'the "skip" and "back" commands.\n To safely exit the program use "quit".\n'+
        
                          ' The right arrow key serves in place of the enter key.\n\n'+
                          ' Code written by Chris Salmean- open for anyone to use but '
                          'please provide credit, share any improvements you make and '
                          'do not use for profit.')
                else:
                    c1= '\x1b[1;30;43m'
                    c2='\x1b[0m'
                    print (c1+f'----{self.input} not a command.'+c2)
                
                self.input=""
                
            elif key == kb.Key.backspace:
                # If backspace is pressed, then remove a character from the stored string
                self.input=self.input[0:-1]
        except:
            self.status=re.sub('\d','2',self.status)
