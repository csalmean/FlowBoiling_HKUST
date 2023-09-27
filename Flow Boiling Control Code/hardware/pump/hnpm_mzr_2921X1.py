"""
Created on Mon May 17 19:03:33 2021

This module controls the HNP Mikrosysteme mzr-2921X1 microannular pump.

The pump uses a Faulhaber 24V servomotor, which can be controlled using
either the provided 'Motion manager 5' software, or by RS232/serial.

Pump is on COM15 in my experiments

@author: Chris Salmean
"""
import time
import serial
import asyncio

from hardware.hardware import *

class HNPM(controlled_device,serial_hardware):
    """ Hardware module for HNPM mzr-2921X1 pump.
    """
    def __init__(self, name,manager, **kwargs):
        controlled_device.__init__(self,name,manager, **kwargs)
        serial_hardware.__init__(self,name,manager, **kwargs)
        
        # immediately activate and set to 0
        if self.dummy==False:
            if self.ser.isOpen():
                pass
            else:
                self.ser.open()
            
            self.ser.write(str('ANSW0'+self.write_terminator).encode())
            self.ser.write(str('EN'+self.write_terminator).encode()) # enable pump
            self.ser.write(str('V0'+self.write_terminator).encode()) # set to 0 rpm
        
    def deactivate(self):
        print(f'{self.name} switching off')
        if self.dummy==False:
            try:
                if self.ser.isOpen():
                    self.ser.write(str('V0'+self.write_terminator).encode())
                    self.ser.write(str('DI'+self.write_terminator).encode())
                    self.ser.close()
                
                else:
                    self.ser.open()
                    self.ser.write(str('V0'+self.write_terminator).encode()) # set to 0 rpm
                    self.ser.write(str('DI'+self.write_terminator).encode()) # disable pump
                    self.ser.close()
                        
            except:
                self.ser.close()
                self.ser.open()
                self.ser.write(str('V0'+self.write_terminator).encode())
                self.ser.write(str('DI'+self.write_terminator).encode())
                self.ser.close()
                
    def restart(self):
        print(f'RESTARTING {self.name}')
        if self.ser.isOpen():
            self.ser.close()
        else:
            pass        
        self.ser.open()

    def set_actual(self, value):
        # Uses relationship, 1ml/min is 333.33 rpm. If a different pump is used, this should be calibrated.

        print(f'setting {self.name} to {value} ml/min')
        self.status=str('setting 0')
        if self.dummy== False:
            if self.ser.isOpen():
                self.rpm=int(value*333.33)
                
                message=('V'+str(self.rpm)+self.write_terminator)
                
                # Try to write to pump. If any mistake, throw an error.
                try:
                    print('Pump writing message')
                    self.ser.write((message).encode())
                    print(f'Pump flowrate changed to {value} ml/min')
                except:
                    print('PUMP FAILED TO UPDATE')
                    self.satus=str('setting 2')
                
            self.status=str('setting 1')
            
        else:
            # just pretend it's happened.
            pass
        
    # def set_rpm(self, rpm):
    #     if self.ser.isOpen():
    #         if rpm>self.max_rpm:
    #             rpm=self.max_rpm
    #             self.rpm=rpm
    #             print('Pump at maximum speed.')
    #         message=('V'+str(rpm)+self.write_terminator)
    #         self.ser.write((message).encode())
            
    # def get_rpm(self):
    #     if self.ser.isOpen():
    #         self.ser.write(str('GN'+self.write_terminator).encode())
    #         self.read_rpm=float((self.ser.readline().decode().replace(self.read_terminator,"")))
    #         return self.read_rpm

    # def get_flow(self):
    #     self.read_rpm=self.get_rpm()
    #     self.read_flow=self.read_rpm /333.33
    #     return self. read_flow

    # def set_flow(self, flow):
    #     if self.ser.isOpen():
    #         self.rpm=int(flow*333.33)
    #         print(self.rpm)
    #         self.set_rpm(self.rpm)
    #         print(f'Pump flowrate changed to {flow} ml/min')
    #         self.setpoint=flow

    # async def genericset(self,CV):
    #     await asyncio.sleep(0.01)
    #     if self.setpoint!=CV:
    #         self.set_flow(CV)
