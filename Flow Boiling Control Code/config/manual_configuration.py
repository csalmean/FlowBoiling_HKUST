# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 09:58:44 2021

***Configuration file for runs with manual stepping only.***

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

class man_config_dictionary(object):
    def __init__(self, save, folder_name, dummy):
        self.dummy=dummy
        
        self.SS_sweeps=2
        self.USS_sweeps=1
        
        # Frequency of DAQ readings during steady-state (SS) operation and unsteady-state (USS) operation.
        # Data is taken from steady-state period, so should aim for higher acquisition rate.

        self.SS_period=1
        self.USS_period=2
        
        # Since power generation scales with V^2/R and we wish to have approximately linear power steps, this
        # is only the first voltage step! The next step is (V^(1/2)), the step after is (V^(1/4)), and so on.

        self.step_size=5 #V
        
        # Minimum time which must elapse before SS is declared.

        USS_min_time = 10 #seconds
        self.USS_min_count=int(USS_min_time/self.USS_period) # number of loops
        
        # Length of time over which SS values will be recorded
        SS_length=5 #seconds
        self.SS_count=SS_length/self.SS_period # number of loops
        
        self.DAQ_type='DAQ6510'
    
        self.display_length=15
    
        # If 'save' is True, sets save path to be an adjacent 'data' folder in the current path.
        self.save=save
        self.save_path=os.path.join(os.path.abspath(os.curdir).split('Control')[0],'Data')
        
        self.folder_name=folder_name
        
        self.module_configuration()
        self.hardware_configuration()

    def module_configuration(self):
        """ Sets up dictionary of modules in format name:{type,kwargs}.
            This dictionary tells the __main__ script what to set up during initialisation.      
        """
        self.modules={
            'kbl': {'Type':'keylogger'},

            'log': {'Type':'datalogger',
                    'kwargs':{'saving':self.save,
                        'save_path':self.save_path,
                        'folder_name':self.folder_name,
                        
                        'conf_location':str(__file__),
                        
                        'SS_target':'DAQ',
                        'control_target':'cont',

                        # How many entries are collected before committing to the target save file. Can increase saving frequency, but loading the file is a blocking action
                        # which will prevent us from being able to save the modifications if it takes too long to load.
                        'save_length':10, 
                        
                        'display_length':self.display_length
                        }},

            'tim': {'Type':'timer',
                    'kwargs':{
                        'target': 'DAQ',
                        'mode':'triggered', # Timer doesn't decide when to take SS readings, rather it waits for us to tell it.
                        'SS_target':'DAQ'
                        }}       
                            
            }
        
        for module, settings in self.modules.items():
            if 'kwargs' not in settings.keys():
                self.modules[module]['kwargs']={'kwargs':None}
            
            self.modules[module]['kwargs']['dummy']=self.dummy
            
        return self.modules
            
    def hardware_configuration(self):
        """ Sets up dictionary of hardware items, which will be set up be the __main__ script.
            Except from the connection details, best not to tamper with these settings.
        """

        self.hardware={
            'DAQ':{'Type': self.DAQ_type,
                   'kwargs':{
                       'method':'visa',
                       'address':'USB0::0x05E6::0x6510::04515817::0::INSTR', # Can find connection address using Windows Device Manager or Keysight IO Libraries Suite  
                       'n_sweeps':{'SS':self.SS_sweeps,
                                   'USS':self.USS_sweeps},
                       
                       'SS_count':self.SS_count,
                       'USS_count':self.USS_min_count
                             }},
                
            'P1':{'Type':'P_sensor',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':117, # Channel 117 of the DAQ. Need to adjust depending how your setup is wired.
                      # Configure alarms. Can do multiple alarms per sensor. 'L/H/HT' is type, 'P/V' is parameter to watch, '1.5' is limit, 'Alert/Stop' is action which will be taken if triggered
                      'alarms':[('H','P',1.5,'Alert')],
                      
                      'range':100, # Sensor range. Make sure this exceeds maximum expected value of sensor.
                      'nplc':0.5, # number of power-line cycles to average measurements. Longer gives more stable results
                      'settling_time':0, # time waited to allow relay to settle before beginning acquisition
                      
                      'SP':1, 
                      'signal_range':[4,20], # Change this depending on transducer parameters. Signal can be between 4 and 20V in this case
                      'reading_range':[0,6] # Change this depending on transducer. Reads pressures from 0-6 bar in this case
                      }},
            
            'cont':{'Type':'controller', # Set up virtual controller
                    'kwargs':{'SS_target':'DAQ'}},
            
            'PSU':{'Type':'EAPS2384', # Set up power supply
                    'kwargs':{'controller':'cont',
                             
                              'address':"ASRL4::INSTR", # Connected through COM4. Will need to change in other projects
                             
                              'PID':False, # Do we want P&ID control? I'd recommend against it unless tuning is already done.
                              'SP':0,
                              'home':0.5, # If we home the PSU, this is the setpoint
                              'limits':{'H':45, # Do not allow voltage to exceed this.
                                        'L':0},
                             
                              'stepping': True, # Does the PSU step after SS readings have been taken?
                              'step': self.step_size}},
            
            'VALVE':{'Type':'stepper', # If a stepper motor is being used to control the valve, can use these parameters. Final experiments just used manual valve control as easier to tune.
                     'kwargs':{'controller':'cont',
                               
                               'address':"ASRL5::INSTR",
                               'method':'visa',
                               'timeout':5000,
    
                               'PID':False, # Do we want to use PID control? Parameters below.
                               'kP':1,
                               'kI':0.1,
                               'kD':0.05,
                               
                               'Int':0,
                               'Der':0,
                               'int_max':1,
                               'int_min':0,
                               
                               'target_sensor':'P1', # Valve will be manipulated to try and match this sensor's readings to setpoint
                               'target_attr':'P',
                               'SP':0,
                               'home':0,
                               'limits':{'H':90, # Valve will not open more than 90 degrees or close more than 0 degrees.
                                         'L':0}}},
                     
            'PUMP':{'Type':'HNPM', # Using HNPM microannular gear pump. 
                    'kwargs':{'controller':'cont',
                                                            
                              'address':"ASRL2::INSTR", # connection details
                              'method':'serial',
                              'timeout':5000,
                              
                              'PID':False,
                          
                              'SP':0,
                              'home':0,
                              'limits':{'H':6000, # will not exceed 6000rpm
                                        'L':0}}},
            }
        
        # For all hardware devices, set parameters which have not been specified
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
