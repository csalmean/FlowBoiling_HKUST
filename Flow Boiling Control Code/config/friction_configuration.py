# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 09:58:44 2021

Configuration file for measurement of friction in the device. No heaters are used in this case.

We populate this file with a dictionary, containing all of the modules and devices
which must be used.

We describe their mutable properties. With each experiment, properties must be
edited to represent the characteristics of the devices.

Configuration settings are defined as classes as they can then easily be selected and 
imported to the main script

Config file will be saved into the data directory so we can retrospectively
investigate the settings for each specific run.

@author: Chris
"""
import os

class friction_config_dictionary(object):
    def __init__(self, save, folder_name, dummy):
        self.dummy=dummy
        
        self.SS_sweeps=1
        self.USS_sweeps=1
        
        self.SS_period=1
        self.USS_period=2
        
        self.step_size=0 #V
        
        # Minimum time which must elapse before SS is declared
        USS_min_time = 120 #seconds
        self.USS_min_count=int(USS_min_time/self.USS_period) # number of loops
        
        SS_length=60 #seconds
        self.SS_count=SS_length/self.SS_period # number of loops
        
        self.DAQ_type='DAQ6510'
        # self.DAQ_type = 'Agilent34970A'
    
        self.display_length=14
            
        self.save=save
        self.save_path=os.path.join(os.path.abspath(os.curdir).split('Control')[0],'Data2')
        
        self.folder_name=folder_name
        
        self.module_configuration()
        self.hardware_configuration()


    def module_configuration(self):
        """ Dictionary of modules in format name:{type,kwargs}"""
        self.modules={
            'kbl': {'Type':'keylogger'},

            'log': {'Type':'datalogger',
                    'kwargs':{'saving':self.save,
                        'save_path':self.save_path,
                        'folder_name':self.folder_name,
                        
                        'conf_location':str(__file__),
                        
                        'SS_target':'DAQ',
                        'control_target':'cont',
                        'save_length':10,
                        
                        'display_length':self.display_length
                        }},

            'tim': {'Type':'timer',
                    'kwargs':{
                        'target': 'DAQ',
                        'mode':'periodic',
                        'SS_target':'DAQ',
                        'intervals': {'SS':self.SS_period,
                                      'USS':self.USS_period             
                            }}}
            }
        
        for module, settings in self.modules.items():
            if 'kwargs' not in settings.keys():
                self.modules[module]['kwargs']={'kwargs':None}
            
            self.modules[module]['kwargs']['dummy']=self.dummy
            
        return self.modules
            
    def hardware_configuration(self):
        
        self.hardware={
            'DAQ':{'Type': self.DAQ_type,
                   'kwargs':{
                       'method':'visa',
                       'address':'USB0::0x05E6::0x6510::04515817::0::INSTR',
                       'n_sweeps':{'SS':self.SS_sweeps,
                                   'USS':self.USS_sweeps},
                       
                       'SS_count':self.SS_count,
                       'USS_count':self.USS_min_count
                             }},
            
            'PRES':{'Type':'P_sensor',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':115,
                      'alarms':[('H','P',0.2,'Alert')],
                      
                      'range':100,
                      'nplc':0.5,
                      'settling_time':0,
                      
                      'SP':1,
                      'signal_range':[4,20],
                      'reading_range':[-1,1]
                      }},
            
            'PPUMP':{'Type':'P_sensor',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':116,
                      'alarms':[('H','P',1.1,'Alert'),
                                ('H','P',2.0,'Stop')],
                      
                      'range':100,
                      'nplc':0.5,
                      'settling_time':0,
                      
                      'SS': True,
                      'USS_length':15,
                      
                      'SP':1,
                      'signal_range':[3.944905,20],
                      'reading_range':[-1,10]
                      }},
            
            'P1':{'Type':'P_sensor',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':117,
                      'alarms':[('H','P',1.5,'Alert')],
                      
                      'range':100,
                      'nplc':0.5,
                      'settling_time':0,
                      
                      'SP':1,
                      'signal_range':[3.97087,20],
                      'reading_range':[0,6]
                      }},
            
            'dP':{'Type':'P_sensor',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':118,
                      'alarms':[('H','P',10000,'Alert')],
                      
                      'range':10,
                      'nplc':0.5,
                      'settling_time':0,
                      
                      'SP':1,
                      'signal_range':[0.0,10],
                      'reading_range':[0,6]
                      }},
            
            'TC1':{'Type':'PT100',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':119,
                      'alarms':[('H','T',25,'Alert')],
                      
                      'range':100,
                      'nplc':1,
                      'settling_time':1e-3
                      }},
            
            'TC2':{'Type':'TC',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':137,
                      'alarms':[('H','T',110,'Alert'),
                                ('H','T',140,'Stop')],
                      
                      'range':100,
                      'nplc':1,
                      'settling_time':1e-3,
                      
                      'SS': True,
                      'USS_length':self.USS_min_count
                      }},
            
            
            
            'Activator':{'Type':'activator',
                         'kwargs':{'target':'DAQ'}},
            
            'cont':{'Type':'controller',
                    'kwargs':{'SS_target':'DAQ'}},
            
            
            'PUMP':{'Type':'HNPM',
                    'kwargs':{'controller':'cont',
                              
                              'address':"ASRL6::INSTR",
                              'method':'serial',
                              'timeout':5000,
                              
                              'PID':False,
                          
                              'SP':0,
                              'home':0,
                              'safe_position':0,
                              'limits':{'H':6000,
                                        'L':0}}},
            
            'VALVE':{'Type':'stepper',
                      'kwargs':{'controller':'cont',
                               
                                'address':"ASRL5::INSTR",
                                'method':'visa',
                                'timeout':5000,
       
                                'PID':True,
                                'kP':-2,
                                'kI':0,
                                'kD':0,
                               
                                'Int':0,
                                'Der':0,
                                'int_max':1,
                                'int_min':0,
                               
                                'target_sensor':'PPUMP',
                                'target_attr':'P',
                                'SP':10,
                                'home':10,
                                'safe_position':90,
                                'limits':{'H':90,
                                          'L':0}}},
            
            }
        
        for device, settings in self.hardware.items():
            if 'kwargs' not in settings.keys():
                self.hardware[device]['kwargs']={'kwargs':None}
            
            if 'alarms' not in settings['kwargs'].keys():
                self.hardware[device]['kwargs']['alarms']=[("","","","")]
                
            if 'SS' not in settings['kwargs'].keys():
                self.hardware[device]['kwargs']['SS']=False
            
            if 'SP' not in settings['kwargs'].keys():
                self.hardware[device]['kwargs']['SP']=0
            
            self.hardware[device]['kwargs']['dummy']=self.dummy
        
        return self.hardware
        
# import os, shutil

# if not os.access(dirname, os.F_OK):
#     os.mkdir(dirname, 0o700)

# shutil.copy(fname, dirname)
