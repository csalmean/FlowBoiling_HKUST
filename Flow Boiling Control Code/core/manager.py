# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 13:54:35 2021

Manager module, which collects status updates from all modules and restarts them if for some reason they break.
Also waits for commands to be passed from the keyboard logger and distributes them to the right devices

Status codes:
    0: has begun
    1: has ended
    2: error

@author: Chris Salmean
"""
import asyncio
import time
import numpy as np

class module_manager(object):
    def __init__(self):
        self.name='man'
        self.module_dict={}
        self.hardware_dict={}
        self.sensor_dict={}
        self.control_dict={}
        self.safety={}
        
        self.startup_time=time.time()
        
        self.loop=asyncio.get_event_loop()
        self._shutdown=asyncio.Event(loop=self.loop)
        
        self.recorded_variables={}
        
    def alarm(self,target,alarm_type,action):
        # If alarm is triggered, it is sent to the manager. Manager decides what needs to be done.
        for module in self.module_dict.values():
            # Select datalogger
            if 'datalogger' in module[0].__class__.__name__:
                message=[np.round((time.time()-self.startup_time),2),action,target.name,alarm_type]
                module[0].log_error(message)
        
                if action=='Stop':
                    print('SAVING THE LAST 3 LINES OF DATA')
                    try:
                        module[0].save_to_file('SS')
                    except:
                        pass
        
        if action =='Alert':
            pass
        elif action == 'Stop':
            # perform shutdown step
            # self.safety_procedure()
            self.shutdown()
        
    async def check_status(self):
        # Collects status of each module
        checkdict={**self.module_dict,**self.hardware_dict}
        for name, item in checkdict.items():
            status=item[0].status
            checkdict[name][1]=status
            # print('\n.')
            if status[-1] == '2':
                # If a module reports any problems, restart it and report error to logger
                c1= '\x1b[1;37;41m'
                c2 = '\x1b[0m'
                
                print(c1+ f'Error detected in {name}. \nStatus: {status}' + c2)
                await self.perform_restart(item[0])
                print('Restart initiated')
                # And transmit error code to logger
                for module in self.module_dict.values():
                    if 'datalogger' in module[0].__class__.__name__:
                        message=[np.round((time.time()-self.startup_time),2),'error',name,status]
                        module[0].log_error(message)

    def manual_trigger(self):
        # If timer is periodic, can skip minimum waiting time before SS is detected and tell DAQ that SS has been detected.
        for module_name, module in self.module_dict.items():
            if 'tim' in module_name:
                if module[0].mode!='periodic':
                    module[0].triggered.set()
                
        for module_name, module in self.hardware_dict.items():
            if 'DAQ' in module_name:
                module[0].locked = False
                for device, value in module[0].SS_bin.items():
                    module[0].SS_bin[device]='SS'
                
    def manual_input(self,value):
        target=None
        for objectname in self.hardware_dict:
            if 'INP' in objectname.upper():
                importstring='from __main__ import ' + objectname
                exec(importstring)
                
                target=eval(objectname)
                
        if target!=None:
            target.alter(value)

    async def perform_restart(self, module):
        print(f'Restarting {module}')
        self.loop.create_task(module.restart())
        
    async def process(self):
        # Check status of all modules every 0.5 seconds.
        while not self._shutdown.is_set():
            await self.check_status()
            await asyncio.sleep(0.5)
    
    def safety_procedure(self):
         # Moves controlled devices back to safe setpoint.
         for name, device in self.safety.items():
             print(f'{name} going to safe position')
             device.set_actual(device.safe_pos)
         
    def set_param(self,parameter, value):
        if 'controller' not in dir(self):
            print('No controller instantiated.')
            
        else:
            # can be in format 'set_P1_1' or 'set_P1.SP_1'. Attribute is optional.
            device=parameter.split('.')[0].upper()
            if device in self.hardware_dict.keys():
                if len(parameter.split('.'))>1:
                    attribute=parameter.split('.')[-1].upper()
                    
                elif device in self.control_dict.keys():
                    attribute='SP'
                            
                elif device in self.sensor_dict.keys():
                    attribute='SP' 
                else:
                    attribute=None
                    
                self.controller.change_attribute(device, attribute, value)
                # trigger controller to run through again.
                for sensor in self.sensor_dict.values():
                    sensor.new_values.set()
                
            else:
                print(f'No device named {device} in records. Check device names are in ALL CAPS')     
            
    def shutdown(self):
        # Performs shutdown procedure. This requires commanding each device to stop in turn, then cancelling the asynchronous tasks
        for name, module in self.module_dict.items():
            module[0].stop()
            status=module[0].status
            self.module_dict[name][1]=status
        
        for name, hardware in self.hardware_dict.items():
            hardware[0].stop()
            status=hardware[0].status
            self.hardware_dict[name][1]=status
        
        for task in self.tasks:
            task.cancel()
        self.stop()
          
    def step(self, value):
        for info in self.hardware_dict.keys():
            if 'DAQ' in info[0]:
                self.hardware_dict[info][0]._counter=0
        
        self.controller.step(value)
        
    def stop(self):
        # shuts self down
        print(f'{self.name}: shutting down')
        self._shutdown.set()
            
    def toggle_fine(self):
        # changes step size for psu to 1/2 of previous step size
        for info in self.hardware_dict.keys():
            if 'PSU' in info:
                self.hardware_dict[info][0].fine= not self.hardware_dict[info][0].fine
                print(f'PSU fine increments set to {self.hardware_dict[info][0].fine}')
                
                if self.hardware_dict[info][0].fine==False:
                    self.hardware_dict[info][0].fine_counter=0