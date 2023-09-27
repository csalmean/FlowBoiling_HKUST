# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 09:58:44 2021

Configuration file

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

class exp_config_dictionary(object):
    def __init__(self, save, folder_name, dummy):
        self.dummy=dummy
        
        self.SS_sweeps=1
        self.USS_sweeps=1
        
        # Frequency of DAQ readings during steady-state (SS) operation and unsteady-state (USS) operation.
        # Data is taken from steady-state period, so should aim for higher acquisition rate.

        self.SS_period=1
        self.USS_period=2
        
        # Since power generation scales with V^2/R and we wish to have approximately linear power steps, this
        # is only the first voltage step! The next step is (V^(1/2)), the step after is (V^(1/4)), and so on.
        
        self.step_size=30 #V
        
        # Minimum time which must elapse before SS is declared
        USS_min_time = 300 #seconds
        self.USS_min_count=int(USS_min_time/self.USS_period) # number of loops
        
        # Length of time over which SS values will be recorded
        SS_length=60 #seconds
        self.SS_count=SS_length/self.SS_period # number of loops
        
        # Can choose type of DAQ. Code works for both.
        self.DAQ_type='DAQ6510'
        # self.DAQ_type = 'Agilent34970A'

        # Number of lines of readings to show in terminal
        self.display_length=14
    
        # If 'save' is True, sets save path to be an adjacent 'data' folder in the current path.        
        self.save=save
        self.save_path=os.path.join(os.path.abspath(os.curdir).split('Control')[0],'Data2')
        
        self.folder_name=folder_name
        
        self.module_configuration()
        self.hardware_configuration()

    def module_configuration(self):
        """ Dictionary of modules in format name:{type,kwargs}
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
                        'mode':'periodic', # Timer will decide when it is time to take SS readings
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
        """ Sets up dictionary of hardware items, which will be set up be the __main__ script.
            Except from the connection details, best not to tamper with these settings.
        """
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
                      'channel':115, # Channel of the DAQ. Need to adjust depending how your setup is wired.
                      
                      # Configure alarms. Can do multiple alarms per sensor. 'L/H/HT' is type, 'P/V' is parameter to watch, '1.5' is limit, 'Alert/Stop' is action which will be taken if triggered
                      'alarms':[('H','P',0.2,'Alert')],
                      
                      'range':100, # Sensor range. Make sure this exceeds maximum expected value of sensor.
                      'nplc':0.5, # number of power-line cycles to average measurements. Longer gives more stable results
                      'settling_time':0, # time waited to allow relay to settle before beginning acquisition
                      
                      'SP':1,
                      'signal_range':[4,20], # Change this depending on transducer parameters. Signal can be between 4 and 20V in this case
                      'reading_range':[-1,1] # Change this depending on transducer. Reads pressures from -1-1 bar in this case
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
                      
                      'SS': False,
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
                      'alarms':[('H','P',50000,'Alert')],
                      
                      'range':10,
                      'nplc':0.5,
                      'settling_time':0,
                      
                      'SP':1,
                      'signal_range':[0,10],
                      'reading_range':[0,6]
                      }},
            
            'TC1':{'Type':'PT100',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':119,
                      'alarms':[('H','T',25,'Alert'), # Tells me if the inlet fluid temperature falls outside of the desired range
                                ('L','T',23,'Alert')],
                      
                      'range':100,
                      'nplc':1,
                      'settling_time':1e-3
                      }},
            
            'TC2':{'Type':'TC',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':137,
                      'alarms':[('H','T',120,'Stop') # Stops experiment if the outlet fluid temperature gets too high
                                ],
                      
                      'range':100,
                      'nplc':1,
                      'settling_time':1e-3,
                      
                      'SS': True,
                      'USS_length':self.USS_min_count
                      }},
            
            'S1':{'Type':'DC_shunt', # Set up a DC shunt so we can begin measuring heater properties
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':105,
                      'alarms':[('H','I',0.5,'Alert')],
                      
                      'range':100,
                      'nplc':0.5,
                      'settling_time':50e-3,
                      
                      'resistance':4.999, # Very accurate. Used high-precision shunt resistor
                      }},
            
            'H1':{'Type':'DC_heater',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':106,
                      'alarms':[('H','T',140,'Alert')],
                      
                      'range':100,
                      'nplc':0.5,
                      'settling_time':25e-3,
                                            
                      'shunt':'S1', # Direct the heater object to use shunt S1
                      
                      'T_sensing': True, # These parameters are taken from sensor calibration 
                      # Takes a while to manually input these parameters for each sensor, so instead use the additional settings on line 454
                      'a':0,
                      'b':2.225378609,
                      'c':-229.6251021,
                      'offset':0
                      }},
            
            'H2':{'Type':'DC_heater',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':107,
                      'alarms':[('H','T',140,'Alert')],
                      
                      'range':100,
                      'nplc':0.5,
                      'settling_time':25e-3,
                                            
                      'shunt':'S1',
                      
                      'T_sensing': True,
                      'a':0,
                      'b':2.154911814

,

                      'c':-230.1737087

,

                      'offset':0,
                                            }},
            
            'H3':{'Type':'DC_heater',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':108,
                      'alarms':[('H','T',140,'Alert'),
                                ('HT','T',150,'Stop')],
                      
                      'range':100,
                      'nplc':0.5,
                      'settling_time':25e-3,
                                            
                      'shunt':'S1',
                      
                      'T_sensing': True,
                      'a':0,
                      'b':2.158359773

,

                      'c':-230.8105597

,
                      'offset':0,
                      }},
            
            'H4':{'Type':'DC_heater',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':109,
                      'alarms':[('H','T',140,'Alert'),
                                ('HT','T',145,'Stop')],
                      
                      'range':100,
                      'nplc':0.5,
                      'settling_time':25e-3,
                                            
                      'shunt':'S1',
                      
                      'T_sensing': True,
                      'a':0,
                      'b':2.156553316

,

                      'c':-230.1880129

,
                      'offset':0,
                      }},
            
            'H5':{'Type':'DC_heater',
                  'kwargs':{
                      'DAQ_type':self.DAQ_type,
                      'DAQ':'DAQ',
                      'channel':110,
                      'alarms':[('H','T',140,'Alert'),
                                ('HT','T',145,'Stop')],
                      
                      'range':100,
                      'nplc':0.5,
                      'settling_time':25e-3,
                                            
                      'shunt':'S1',
                      
                      'T_sensing': True,
                      'a':0,
                      'b':2.286892629

,
                      'c':-229.9146102

,

                      'offset':0,
                      }},
            
            'QT':{'Type':'combined_Q', 
                  # This is a virtual sensor, which just combines the powers from each heater to estimate total power.
                  'kwargs':{
                      'DAQ':'DAQ',
                      'inputlist':[('H1','S1'),
                                   ('H2','S1'),
                                   ('H3','S1'),
                                   ('H4','S1'),
                                   ('H5','S1'),
                                   ],
                      'output':'Q'
                      }},
            
            'Activator':{'Type':'activator',
                         'kwargs':{'target':'DAQ'}},
            
            'cont':{'Type':'controller',
                    'kwargs':{'SS_target':'DAQ'}},
            
            'DCAC':{'Type':'inverter', # Inverter was used to reduce electromigration damage to heaters
                      'kwargs':{'controller':'cont',
                               
                                'address':"ASRL8::INSTR", # controlled using Arduino
                                'method':'visa',
                                'timeout':5000,

                                'PID':False,

                                'home':0,
                                'safe_position':0,
                                'limits':{'H':90,
                                          'L':0}}},
            
            'PSU':{'Type':'EAPS2384', # Used Elektro-Automatik PS200B series power supply, connected with outputs in series for higher voltages
                    'kwargs':{'controller':'cont',
                             
                              'address':"ASRL4::INSTR",
                             
                              'PID':False,
                              'SP':0,
                              'home':0,
                              'safe_position':0,
                              'limits':{'H':168, # Voltage is not allowed to exceed this value
                                        'L':0},
                             
                              'inverter':'DCAC',
                              
                              'stepping': True,
                              'step': self.step_size}},
            
            'PUMP':{'Type':'HNPM', # Used HNP Mikrosystems mzr series pump.
                    'kwargs':{'controller':'cont',
                              
                              'address':"ASRL6::INSTR",
                              'method':'serial',
                              'timeout':5000,
                              
                              'PID':False,
                          
                              'SP':0,
                              'home':0,
                              'safe_position':0,
                              'limits':{'H':6000, # Limit to 6000 rpm
                                        'L':0}}},
            
            'VALVE':{'Type':'stepper', # Pressure can be controlled using a stepper motor attached to the inlet valve
                      'kwargs':{'controller':'cont',
                               
                                'address':"ASRL5::INSTR", # Controlled using an Arduino on COM5
                                'method':'visa',
                                'timeout':5000,
       
                                'PID':True, # PID control used to match reading to setpoint
                                'kP':-2,
                                'kI':0,
                                'kD':0,
                               
                                'Int':0,
                                'Der':0,
                                'int_max':1,
                                'int_min':0,
                               
                                'target_sensor':'PPUMP', # This is the controlled variable
                                'target_attr':'P',
                                'SP':10, # setpoint is 10
                                'home':10,
                                'safe_position':45,
                                'limits':{'H':90,
                                          'L':0}}},
            
            }
        # Use this to quickly input calibration details (just copy and paste from auto-generated calibration report)
        
        additional_settings='H1_b:2.2179551203317764,H1_c:-228.38307798569494,H2_b:2.1384649503192414,H2_c:-228.03291362492186,H3_b:2.1480826453426607,H3_c:-229.13438065621423,H4_b:2.197264829193243,H4_c:-230.05823690117938,H5_b:2.3177744383391157,H5_c:-228.92579440642922,'
        
        # parse heater calibration settings and assign to each heater
        settinglist=additional_settings.split(',')
        try:
            for phrase in settinglist:
                if phrase!='':
                    target=phrase.split('_')[0]
                    setting=phrase.split('_')[-1].split(':')[0]
                    value=phrase.split('_')[1].split(':')[-1]
                    self.hardware[target]['kwargs'][setting]=float(value)
                    
                    print(f'{target}.{setting} updated by string to {value}:\n[Confirmation]: {target}:{setting}={self.hardware[target]["kwargs"][setting]}\n')
        except:
            print('Config failed to update additional settings.Please check them and try again' )
        
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