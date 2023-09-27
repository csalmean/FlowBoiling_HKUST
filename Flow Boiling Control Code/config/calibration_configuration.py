# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 09:58:44 2021

Configuration file for heater calibration runs. In these experiments the device is placed in an
oven and its temperature and resistance are measured.

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

class cal_config_dictionary(object):
    def __init__(self, save, folder_name, dummy):
        self.dummy=dummy
        
        self.SS_sweeps=10
        self.USS_sweeps=10
        
        self.SS_period=1
        self.USS_period=2
                
        self.step_size=5 #V
        
        # Minimum time which must elapse before SS is declared
        USS_min_time = 10 #seconds
        self.USS_min_count=int(USS_min_time/self.USS_period) # number of loops
        
        SS_length=5 #seconds
        self.SS_count=SS_length/self.SS_period # number of loops
        
        self.DAQ_type='Agilent34970A' # The calibrations use the Agilent DAQ
    
        self.display_length=15
            
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
                        'save_length':5,
                        
                        'display_length':self.display_length
                        }},

            'tim': {'Type':'timer',
                    'kwargs':{
                        'target': 'DAQ',
                        'mode':'triggered',
                        'SS_target':'DAQ'}
                            }
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
                       'address':'ASRL5::INSTR',
                       'n_sweeps':{'SS':self.SS_sweeps,
                                   'USS':self.USS_sweeps},
                       
                       'SS_count':self.SS_count,
                       'USS_count':self.USS_min_count
                             }},
            
            # 'TC1':{'Type':'TC',
            #       'kwargs':{
            #           'DAQ_type':self.DAQ_type,
            #           'DAQ':'DAQ',
            #           'channel':101,
            #           'alarms':[('H','T',110,'Alert')],
                      
            #           'range':100,
            #           'nplc':1,
            #           'settling_time':1e-3
            #           }},
            
            'TC1':{'Type':'PT100',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':102,
                      'alarms':[('H','T',110,'Alert')],
                      
                      'range':100,
                      'nplc':1,
                      'settling_time':1e-3
                      }},
            

            # The heaters are instatiated but their recorded resistance is not manipulated. Output for each heater is simply its resistance.
            'H1':{'Type':'RTD',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':104,
                      
                      'n_wires':4,
                      'range':1000,
                      'nplc':1,
                      'settling_time':5e-3,
                      
                      'a':0,
                      'b':1,
                      'c':0,
                      'offset':0
                      }},
            
            'H2':{'Type':'RTD',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':105,
                      
                      'n_wires':4,
                      'range':1000,
                      'nplc':1,
                      'settling_time':5e-3,
                      
                      'a':0,
                      'b':1,
                      'c':0,
                      'offset':0
                      }},
            
            'H3':{'Type':'RTD',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':106,
                      
                      'n_wires':4,
                      'range':1000,
                      'nplc':1,
                      'settling_time':5e-3,
                      
                      'a':0,
                      'b':1,
                      'c':0,
                      'offset':0
                      }},
            
            'H4':{'Type':'RTD',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':107,
                      
                      'n_wires':4,
                      'range':1000,
                      'nplc':1,
                      'settling_time':5e-3,
                      
                      'a':0,
                      'b':1,
                      'c':0,
                      'offset':0
                      }},
            
            'H5':{'Type':'RTD',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':103,
                      
                      'n_wires':4,
                      'range':1000,
                      'nplc':1,
                      'settling_time':5e-3,
                      
                      'a':0,
                      'b':1,
                      'c':0,
                      'offset':0
                      }},
            
            'Activator':{'Type':'activator',
                         'kwargs':{'target':'DAQ'}},
            
            'cont':{'Type':'controller',
                    'kwargs':{'SS_target':'DAQ'}},
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