# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 12:22:48 2021

Use to set up physical sensors. All are connected through the data acquisition so code has been made compatible with both Agilent and Keithley units.

@author: Chris
"""
import asyncio
import numpy as np
import random
import re

class Sensor (object):
    """ All sensors have certain attributes in common; for example:
        name, channel number, signal, reading, high/low values. Set these in the 'sensor' object"""
    
    def __init__(self, name, manager, **kwargs):
        self.name=name
        
        self.manager=manager
        self.status='initialising 0'
        self.manager.hardware_dict[self.name]=[self,self.status]
        self.manager.sensor_dict[self.name]=self
                
        importstring='from __main__ import ' + kwargs['DAQ']
        exec(importstring)
        
        self.DAQ_type=kwargs['DAQ_type']
        self.DAQ=eval(kwargs['DAQ'])
        self.channel=kwargs['channel']
        self.channel_identifier='(@'+str(self.channel)+')'

        self.DAQ.channel_dict[self.channel]=self

        self.cmd_list=[]
        self.alarms=kwargs['alarms']
        
        if kwargs['SS']==True:
            #add sensor to SS bin of DAQ. Means DAQ will check this one for steady state
            self.DAQ.SS_bin[self.name]='USS'
            
            self.history=[]
            hist_length=kwargs['USS_length']*self.DAQ.n_sweeps['USS']
            
            for i in range(0,hist_length):
                n = random.randint(1,100)
                self.history.append(n)
        
        self.SP=np.array([kwargs['SP']])    
        
        # Start asynchronous loops
        self.loop=asyncio.get_event_loop()
        self._shutdown=asyncio.Event(loop=self.loop)
        
        self.signal=[]
        self.alarm_history=[]
        
        self.updated=asyncio.Event()
        self.processed=asyncio.Event()
        self.new_values=asyncio.Event()
            
    def check_alarms(self):
        for alarm in self.alarms:
            alarm_type=alarm[0]
            value=alarm[2]
            action=alarm[3]
            triggered=False

            # High alarm, triggered when reading is over alarm value
            if alarm_type=='H':
                alarm_variable=np.array(eval('self.'+alarm[1]))                
                cond=np.where(alarm_variable>value,True,False)
                if True in cond:
                    triggered=True
            
            # Low alarm, triggered when reading is under alarm value
            elif alarm_type=='L':
                alarm_variable=np.array(eval('self.'+alarm[1]))
                cond=np.where(alarm_variable<value,True,False)
                if True in cond:
                    triggered=True
            
            # High-trending alarm. Triggered if reading is over the alarm value for n consecutive measurements. 
            elif alarm_type=='HT':
                alarm_periods=alarm[4]
                alarm_variable=np.array(eval('self.'+alarm[1]))  
                self.alarm_history=np.append(self.alarm_history,(alarm_variable[-1]))
                if len(self.alarm_history)>=alarm_periods:
                    self.alarm_history=np.array(self.alarm_history[-3:])
                    cond=np.where(self.alarm_history>value,True,False)
                    if all(cond[-3:])==True:
                        triggered=True
            
            # Depending on selected action, set colour of warning text
            if triggered==True:
                if action == 'Alert':
                    c1= '\x1b[1;30;43m'
                    c2='\x1b[0m'
                    
                elif action == 'Stop':
                    c1= '\x1b[1;37;41m'
                    c2 = '\x1b[0m'   
                    
                # Tell manager there is an alarm and what action must be taken, then print to terminal.
                self.manager.alarm(self,alarm_type,action)
                print(c1+f'{self.name} Alarm triggered. {action}'+c2)
    
    def determine_SS(self):

        if 'history' in dir(self):
            self.status='SS calc 0'
            
            self.history.extend(eval('self.'+self.primary))
            self.history=self.history[len(eval('self.'+self.primary))::]
            
            # Look at relative change of this sensor over the specified period
            chan_max=(np.max(self.history))
            chan_min=(np.min(self.history))
            chan_mean=(np.mean(self.history))
            
            self.chan_range=(chan_max-chan_min)/chan_mean
            # print(f'SS device {self.name} range: {chan_range}')

            # If change is less than 2% of mean (i.e. +/- 1%), then this sensor will begin to report itself as 'SS'
            if self.chan_range<0.02:
                self.state='SS'
                self.DAQ.SS_bin[self.name]='SS'
            
            else:
                self.state='USS'
                self.DAQ.SS_bin[self.name]='USS'
        
    async def process(self):
        # This module carries out the following steps:
        try:
            while not self._shutdown.is_set():
                self.status= 'waiting 0'
                await self.updated.wait()
                
                self.status= 'processing 0'
                await self.process_data()
                
                for name in dir(self):
                    if 'virt_trig' in name:
                        triggerstring='self.'+name
                        eval(triggerstring).set()                    
                
                self.status='checking 0'
                self.check_alarms()
                
                self.status='SS_calc 0'
                self.determine_SS()
                
                self.status= 'transmitting 0'
                self.transmit()
                
                self.updated.clear()
    
        except:
            # Report that there is a problem
            self.status=re.sub('\d','2',self.status)
    
    async def process_data(self):
        # print(f'{self.name} converting signal into readings')
        setattr(self,self.primary,self.signal)
        
        self.processed.set()
        self.new_values.set()
        await asyncio.sleep(0.00001)
    
    async def restart(self):
        if not self._shutdown.is_set():
            await self.process()    
    
    def stop(self):
        print(f'{self.name}: shutting down')
        self._shutdown.set()
        
    def transmit(self):
        pass        

# Setup for funamental sensors. DAQs only measure voltage drop, but can be set to measure VDC, VAC, Thermocouple readings or resistances.
class VDC (Sensor):
    def __init__ (self, name, manager, **kwargs):
        #Inherit properties from the superclass (Generic sensor)
        super().__init__(name,manager,**kwargs)
        
        self.range=kwargs['range']
        self.nplc=kwargs['nplc']
        
        # populate command list. These are the settings which will be used to configure the DAQ, depending on its type
        # want two different groups of settings, for regular and burst use
        
        if self.DAQ_type == 'DAQ6510':
            self.cmd_list=[
                "FUNC 'VOLT:DC', "+self.channel_identifier, # set channel to record DC voltage
                "DISP:VOLT:DC:DIG 5, "+self.channel_identifier,
                "VOLT:DC:AZER OFF, "+self.channel_identifier # remove automatic zeroing for speed
                ]
            spacer=', '
            
        elif self.DAQ_type == 'Agilent34970A':
            self.cmd_list=[
                "CONF:VOLT:DC "+self.channel_identifier, # set channel to record DC voltage
                "ZERO:AUTO OFF, "+self.channel_identifier # remove automatic zeroing for speed
                ]
            spacer =','
            
        self.cmd_list.extend([              
                "VOLT:DC:NPLC "+str(self.nplc)+spacer+self.channel_identifier, # Tell DAQ how many power-line cycles to measure over. This improves accuracy
                "VOLT:DC:RANG "+str(self.range)+spacer+self.channel_identifier])    # tell DAQ what the expected measurement range is.

        # Now send command strings to DAQ    
        for command in self.cmd_list:
            self.DAQ.configuration_strings[self.channel]=self.cmd_list

        # V is the primary attribute of this sensor. i.e., if we ask the sensor to report its value, it'll say something like 'V=0'
        self.primary='V'

class VAC (Sensor):
    def __init__ (self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        
        
        self.range=kwargs['range']
        self.nplc=kwargs['nplc']
        self.settling_time=kwargs['settling_time']
        # populate command list.
        # want two different groups of settings, for regular and burst use
        
        if self.DAQ_type == 'DAQ6510':
            self.cmd_list=[
                "FUNC 'VOLT:AC', "+self.channel_identifier,
                "VOLT:AC:DET:BAND 300, "+self.channel_identifier,
                "DISP:VOLT:AC:DIG 5, "+self.channel_identifier,
                "VOLT:AC:DEL:AUTO OFF, "+self.channel_identifier            
                ]
            spacer =', '

            
        elif self.DAQ_type == 'Agilent34970A':
            self.cmd_list=[
                "CONF:VOLT:AC "+self.channel_identifier,
                "VOLT:AC:DET:BAND 200, "+self.channel_identifier,
                "ZERO:AUTO OFF "+self.channel_identifier
                ]
            spacer =','
            
        
        self.cmd_list.extend([
                "VOLT:AC:RANG "+str(self.range)+spacer+self.channel_identifier,
                "ROUT:CHAN:DEL "+str(self.settling_time)+spacer+self.channel_identifier])

        for command in self.cmd_list:
            self.DAQ.configuration_strings[self.channel]=self.cmd_list

        self.primary='V'

class TC (Sensor):
    # Measure temperature using thermocouple. In this case, we use a type-T thermocouple.
    def __init__ (self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        

        self.nplc=kwargs['nplc']
        self.settling_time=kwargs['settling_time']
        # populate command list.
        # want two different groups of settings, for regular and burst use
        
        if self.DAQ_type == 'DAQ6510':
            self.cmd_list=[
                "FUNC 'TEMP', "+self.channel_identifier,
                "TEMP:TRAN TC, "+self.channel_identifier,
                "TEMP:TC:TYPE T, "+self.channel_identifier, # Type T thermocouple. Might need to change for other experiments.
                "DISP:TEMP:DIG 5, "+self.channel_identifier,
                # "TEMP:AZER OFF, "+self.channel_identifier,
                "TEMP:DEL:AUTO OFF, "+self.channel_identifier,
                ]
            spacer=', '
            
        elif self.DAQ_type == 'Agilent34970A':
            self.cmd_list=[
                "CONF:TEMP TC,T ,"+self.channel_identifier,
                "ZERO:AUTO OFF,"+self.channel_identifier
                ]
            spacer=','
        
        self.cmd_list.extend([
            "TEMP:NPLC "+str(self.nplc)+spacer+self.channel_identifier,
            "ROUT:CHAN:DEL "+str(self.settling_time)+spacer+self.channel_identifier])
            
        for command in self.cmd_list:
            self.DAQ.configuration_strings[self.channel]=self.cmd_list

        self.primary='T'
        
        # Add to the manager's dictionary of variables which will be recorded and displayed 
        self.manager.recorded_variables[self.name]={'SS':['T'],
                                                    'USS':['T'],
                                                    'disp_sensing':['T']}
        
        for attrlist in self.manager.recorded_variables[self.name].values():
            for attribute in attrlist:
                setattr(self,attribute,0)
                              
class PT100 (Sensor):
    # Measure temperature using RTD temperature sensor.
    def __init__ (self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        

        self.nplc=kwargs['nplc']
        self.settling_time=kwargs['settling_time']
        # populate command list.
        # want two different groups of settings, for regular and burst use
        
        if self.DAQ_type == 'DAQ6510':
            self.cmd_list=[
                "FUNC 'TEMP', "+self.channel_identifier,
                "TEMP:TRAN FRTD, "+self.channel_identifier, # Four-wire RTD
                "TEMP:RTD:FOUR PT100, "+self.channel_identifier,
                "DISP:TEMP:DIG 5, "+self.channel_identifier,
                # "TEMP:AZER OFF, "+self.channel_identifier,
                "TEMP:DEL:AUTO OFF, "+self.channel_identifier,
                ]
            spacer=', '
            
        elif self.DAQ_type == 'Agilent34970A':
            self.cmd_list=[
                "CONF:TEMP FRTD,85, "+self.channel_identifier,
                "ZERO:AUTO OFF,"+self.channel_identifier
                ]
            spacer=','
        
        self.cmd_list.extend([
            "TEMP:NPLC "+str(self.nplc)+spacer+self.channel_identifier,
            "ROUT:CHAN:DEL "+str(self.settling_time)+spacer+self.channel_identifier])
            
        for command in self.cmd_list:
            self.DAQ.configuration_strings[self.channel]=self.cmd_list

        self.primary='T'
        
        self.manager.recorded_variables[self.name]={'SS':['T'],
                                                    'USS':['T'],
                                                    'disp_sensing':['T']}
        
        for attrlist in self.manager.recorded_variables[self.name].values():
            for attribute in attrlist:
                setattr(self,attribute,0)
                
class Res (Sensor):
    # Simply measure resistance across the wires.
    def __init__ (self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        
        self.n_wires=kwargs['n_wires']
        self.range=kwargs['range']
        self.nplc=kwargs['nplc']
        self.settling_time=kwargs['settling_time']
        # populate command list.
        # want two different groups of settings, for regular and burst use
        
        if self.n_wires == 4:
            name = 'FRES' # 4-wire resistance measuremnt can be used to negate the resistance of the wires themselves.
        else:
            name = 'RES' # Otherwise we jsut use the 2-wire method.
        
        if self.DAQ_type == 'DAQ6510':
            self.cmd_list=[
                ":FUNC '"+name+"', "+self.channel_identifier,
                ":DISP:"+name+":DIG 5, "+self.channel_identifier,
                ":"+name+":AZER OFF, "+self.channel_identifier,
                ":"+name+":OCOM ON, "+self.channel_identifier,
                ":"+name+":DEL:AUTO OFF, "+self.channel_identifier
                ]
            spacer=', '
            
        elif self.DAQ_type == 'Agilent34970A':
            self.cmd_list=[
                "CONF:"+name+" "+self.channel_identifier,
                "ZERO:AUTO OFF,"+self.channel_identifier
                ]
            spacer=','


        self.cmd_list.extend([
            name+":NPLC "+str(self.nplc)+spacer+self.channel_identifier,
            name+":RANG "+str(self.range)+spacer+self.channel_identifier,
            "ROUT:CHAN:DEL "+str(self.settling_time)+spacer+self.channel_identifier])

        
        for command in self.cmd_list:
            self.DAQ.configuration_strings[self.channel]=self.cmd_list
            
        self.primary='R'
           
# Setup for real sensors (i.e. pressure, RTDs, shunts)
class P_sensor(VDC):
    # Pressure sensors is measured by monitoring DC output from transducer (0-5V, proportional to pressure). For the transducers
    #  with current output (i..e 0-20mA), measure voltage drop across a resistor in series to determine current. (i.e. 220 Ohm resistor
    # in series will have voltage drop from 0-4.4 V). Can configure DAQ as a DC voltage sensor, and perform calculations on measured VDC.

    def __init__ (self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        
        # Configure linear relationship between voltage range and pressure range to allow estimation of pressure from voltage.
        self._signal_range = kwargs['signal_range']
        self._reading_range = kwargs['reading_range']
        self.calibration_m = (self._reading_range[1]-self._reading_range[0])/(
            self._signal_range[1]-self._signal_range[0])
        self.calibration_c = self._reading_range[0]-(self.calibration_m*self._signal_range[0])

        self.manager.recorded_variables[self.name]={'SS':['P'],
                                                    'USS':['P'],
                                                    'disp_sensing':['P']}
        
        for attrlist in self.manager.recorded_variables[self.name].values():
            for attribute in attrlist:
                setattr(self,attribute,0)

        # Although V is being measured, we want to display P for this sensor
        self.primary='P'

    async def process_data(self):
        # print(f'{self.name} converting signal into readings')
        self.V=np.abs(self.signal)

        # Convert measured voltage signal to internally-stored pressure.
        self.P =np.add(np.multiply(np.abs(self.V),self.calibration_m),self.calibration_c)
        # Convert pressure into Pa
        if self.name == 'dP':
            self.P*=100000
            
        self.processed.set()
        self.new_values.set()
        await asyncio.sleep(0.00001)
                
class RTD(Res):
    # These RTDs are not manufactured Pt100. These are resistance temperature sensors deposited onto the samples directly
    # as metal films. Their TCR is calibrated using an oven as described in my published works.

    def __init__ (self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
    
        # Take calibrated TCR parameters
        self.a = kwargs['a']
        self.b = kwargs['b']
        self.c = kwargs['c']
        self.offset=kwargs['offset']
        
        self.manager.recorded_variables[self.name]={'SS':['R','T'],
                                                    'USS':['R','T'],
                                                    'disp_sensing':['T']}
        
        for attrlist in self.manager.recorded_variables[self.name].values():
            for attribute in attrlist:
                setattr(self,attribute,0)        
        
    async def process_data(self):
        # print(f'{self.name} converting signal into readings')
        
        self.R=np.abs(self.signal)
        self._R_offset=np.add(self.R,self.offset)

        # Convert measured resistance to temperature
        self.T= np.add(np.multiply(np.square(self._R_offset),self.a),
                       np.add(np.multiply(self._R_offset, self.b),self.c))
        self.processed.set()
        self.new_values.set()
        await asyncio.sleep(0.00001)
    
# Could not get multiple inheritance to work with variables in init, so had to write
# out each heater and shunt separately. If anyone knows how to fix this please feel
# free to contribute.     
    
class DC_heater(VDC):
    """
    A heater can also be used as a temperature sensor, if its parameters have already been calibrated using an oven (as described in my published works)
    Using the voltage across the heater and across a shunt resistor in series, we can determine its resistance, temperature and power.
    The heater is therefore simply a DC voltage sensor, with extra calculation steps. 
    """
    def __init__ (self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        importstring='from __main__ import ' + kwargs['shunt']
        exec(importstring)
        
        # Point program towards the right shunt so that it can calculate the heater's resistance etc.
        self.shunt=eval(kwargs['shunt'])
        
        # Same as in the RTD object above, we need to know the pre-calibrated TCR of the heater to determine its temperature
        if kwargs['T_sensing']==True:
            self.a=kwargs['a']
            self.b=kwargs['b']
            self.c=kwargs['c']
            self.offset=kwargs['offset']
    
        # For each heater, we wish to record and display several parameters.
        self.manager.recorded_variables[self.name]={'SS':['V','R','Q','T'],
                                                    'USS':['V','R','Q','T'],
                                                    'disp_sensing':['Q','T']}
        
        for attrlist in self.manager.recorded_variables[self.name].values():
            for attribute in attrlist:
                setattr(self,attribute,0)    
    
    async def process_data(self):        
        # print(f'{self.name} converting signal into readings')
        await self.shunt.processed.wait()
        
        self.V=np.abs(self.signal)
        self.I=self.shunt.I
        
        self.R=np.divide(np.multiply(self.V,self.shunt.R),self.shunt.V)
        self.Q=np.divide(np.square(self.V),self.R)
        
        if 'a' in dir(self):
            self._R_offset=np.add(self.R,self.offset)
            self.T= np.add(np.multiply(np.square(self._R_offset),self.a),
                           np.add(np.multiply(self._R_offset, self.b),self.c))
        
        self.processed.set()
        self.new_values.set()

class AC_heater(VAC):
    """ 
    A heater can also be used as a temperature sensor, if its parameters have already been calibrated using an oven (as described in my published works)
    Using the voltage across the heater and across a shunt resistor in series, we can determine its resistance, temperature and power.
    The heater is therefore simply an AC voltage sensor, with extra calculation steps. 
    """
    def __init__ (self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        importstring='from __main__ import ' + kwargs['shunt']
        exec(importstring)
        
        self.shunt=eval(kwargs['shunt'])

        if kwargs['T_sensing']==True:
            self.a=kwargs['a']
            self.b=kwargs['b']
            self.c=kwargs['c']
            self.offset=kwargs['offset']
            
            self.manager.recorded_variables[self.name]={'SS':['V','R','Q','T'],
                                                        'USS':['V','R','Q','T'],
                                                        'disp_sensing':['Q','T']}
            
            for attrlist in self.manager.recorded_variables[self.name].values():
                for attribute in attrlist:
                    setattr(self,attribute,0)

    async def process_data(self):
        # print(f'{self.name} converting signal into readings')
        await self.shunt.processed.wait()
        self.V=np.abs(self.signal)
        self.I=self.shunt.I
        
        self.R=np.divide(np.multiply(self.V,self.shunt.R),self.shunt.V)
        self.Q=np.divide(np.square(self.V),self.R)
        
        if 'a' in dir(self):
            self._R_offset=np.add(self.R,self.offset)
            self.T= np.add(np.multiply(np.square(self._R_offset),self.a),
                           np.add(np.multiply(self._R_offset, self.b),self.c))
        
        self.processed.set()
        self.new_values.set()
        
class DC_shunt(VDC):
    """ Voltage drop across a shunt resistor in series can be used to determine the current in the heater. Can either direct
    shunt to alter parameters in each heater, or direct all heaters to check shunt.
    """
    def __init__ (self, name, manager, **kwargs):
       super().__init__(name,manager,**kwargs)
       self.R=kwargs['resistance']
       
       self.manager.recorded_variables[self.name]={'SS':['V','I'],
                                                   'USS':['V','I'],
                                                   'disp_sensing':['I']}
        
       for attrlist in self.manager.recorded_variables[self.name].values():
           for attribute in attrlist:
               setattr(self,attribute,0)
       
    async def process_data(self):
       # print(f'{self.name} converting signal into readings')
       self.V=np.abs(self.signal)
       self.I=np.divide(self.V,self.R)
       self.Q=np.multiply(self.V,self.I)
       
       self.processed.set()
       self.new_values.set()
       await asyncio.sleep(0.00001)
        
class AC_shunt(VAC):
    """ Voltage across a shunt resistor in series can be used to determine current in heater. Can either direct
    shunt to alter parameters in each heater, or direct all heaters to check shunt.
    """
    def __init__ (self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        self.R=kwargs['resistance']
        
        self.manager.recorded_variables[self.name]={'SS':['V','I'],
                                                    'USS':['V','I'],
                                                    'disp_sensing':['I']}
        
        for attrlist in self.manager.recorded_variables[self.name].values():
            for attribute in attrlist:
                setattr(self,attribute,0)
        
    async def process_data(self):
        # print(f'{self.name} converting signal into readings')
        self.V=np.abs(self.signal)
        self.I=np.divide(self.V,self.R)
        self.Q=np.multiply(self.V,self.I)
        
        self.processed.set()
        self.new_values.set()
        await asyncio.sleep(0.00001)
