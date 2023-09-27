# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 10:42:41 2021

File logger. This module takes the experimental measurements and any errors, and saves to file.

- creates folder structure depending upon user inputs
- saves the following into the folder:
    - Steady state measurements
    - Unsteady state measurements
    - Configuration file

- outputs table containing recent data history, for realtime monitoring in console

@author: Chris Salmean
"""
from modules.module import *
import pandas as pd
import numpy as np
import time
from tabulate import tabulate
import os
import shutil
import re

class datalogger(core_module):
    def __init__(self, name, manager, **kwargs):
        super().__init__(name,manager,**kwargs)
        
        importstring='from __main__ import ' + kwargs['SS_target']
        exec(importstring)
        self.SS_target=eval(kwargs['SS_target'])
        
        importstring='from __main__ import ' + kwargs['control_target']
        exec(importstring)
        self.control_target=eval(kwargs['control_target'])
        
        self.observed_objects={}
        
        # These are the dataframes which will be held in the datalogger.
        self.df_titles=['SS','USS','disp_sensing','disp_cont']
        
        self.stored_variables={}
        for df in self.df_titles:
            self.stored_variables[df]={}

        df_columns={'internal_memory':[]}
        for df in self.df_titles:
            df_columns[df]=[]
        
        for device,details in manager.recorded_variables.items():
            importstring='from __main__ import '+device
            exec(importstring)
            
            self.observed_objects[device]=(eval(device))
            
            for mode in self.df_titles:
                if mode in details.keys():
                    self.stored_variables[mode][device]=details[mode]
                    df_columns['internal_memory'].extend([str(
                        device+'.'+attr) for attr in details[mode]])
                    df_columns[mode].extend([str(
                        device+'.'+attr) for attr in details[mode]])
                       
        self.saving=kwargs['saving']
        self.save_path=kwargs['save_path']
        self.folder_name=kwargs['folder_name']
        self.filenumber=1
        self.startup=True
        
        self.conf_location=kwargs['conf_location']
        self.create_directories()
            
        df_columns['internal_memory'] = list(dict.fromkeys(df_columns['internal_memory']))
        
        self.dfs={}
        for name, df in df_columns.items():
            df_columns[name].insert(0,'t')
            self.dfs[name]=pd.DataFrame(columns=df)
        # self.internal_memory=pd.DataFrame(columns=df_columns['internal_memory'])
        self.save_threshold=kwargs['save_length']
        
        self.display_length=kwargs['display_length']
        
        self.state=self.SS_target.state
        self.state_counter=0
        self.start_time=time.time()
        self.last_measurement_time=0
    
    def copy_rename(self,src,dest):
        # This function ensures files aren't overwritten. If the file already exists, it renames the current file to have a unique ID

        # walk through files in target directory, get name of each. 
        filenames = next(os.walk(dest), (None, None, []))[2] 
        
        # Get name of file to be copied and modify to be numbered
        filename, ext = os.path.splitext(os.path.basename(src))
        name_to_copy=filename+'_'+str(1)+ext
        
        # compare names, increment name of file to be copied until it doesn't match
        i=1
        while name_to_copy in filenames:
            name_to_copy=(name_to_copy.replace(str(i),str(i+1)))
            i+=1
        
        shutil.copy(src, os.path.join(dest,name_to_copy))
    
    def create_directories(self):
        # If we try to save the files somewhere new, the directory has to be made first.
        if self.saving==True:
            self.dir_path=os.path.join(self.save_path,self.folder_name)
            
            # Create target directory if doesn't exist
            if not os.path.exists(self.dir_path):
                os.makedirs(self.dir_path)
                print(f"Directory {self.dir_path} created")
            else:    
                pass
            
            # create directories to contain error and config logs
            dirs=['config_logs','error_logs']
            for directory in dirs:
                dir_loc=os.path.join(self.dir_path,directory)
            
                if not os.path.exists(dir_loc):
                    os.makedirs(dir_loc)
                    print(f"Directory {directory} created")
            else:    
                pass
            
            # copy configuration file to conf directory
            conf_dir=os.path.join(self.dir_path,'config_logs')
            self.copy_rename(self.conf_location,conf_dir)
    
    def check_length(self):
        # Since loading and writing the csv are blocking, these actions should not be done too frequently. There's a possibility for large files
        # that the data fails to load because the previous step is still saving. Instead, store consecutive values to internal memory, and
        # save to csv in batches.

        if self.state==self.SS_target.state:
            if len(self.dfs['internal_memory'])>=self.save_threshold:
                # reached end of internal buffer so save to csv and start over
                self.status= 'Saving 0'
                print(f'{self.state} saved')
                self.save_to_file(self.state)
                self.status= 'Wiping memory 0'
                self.dfs['internal_memory']=pd.DataFrame(columns=self.dfs[
                    'internal_memory'].columns)
    
    def determine_state(self):
        # Check out the steady-state status of the target (DAQ). If there's any change, start saving to the appropriate file
        if self.state!=self.SS_target.state:
            # state has changed
            self.state_counter=0
            print('state changed, logger saving')
            self.save_to_file(self.state)
            
            self.state=self.SS_target.state
            self.dfs['internal_memory']=pd.DataFrame(columns=self.dfs[
                'internal_memory'].columns)
        else:
            self.state_counter+=1
   
    def extract_dfs(self):
        # Only some of the saved data is displayed. In this function, we extract the imnformation we wish to display from the larger dataframes of data we wish to save.

        for title in self.df_titles:
            if title == 'disp_sensing':
                self.dfs['disp_sensing']=(pd.concat([self.dfs['disp_sensing'], self.dfs[
                    'internal_memory'][self.dfs['disp_sensing'].columns]], ignore_index=True)).drop_duplicates(
                        ).tail(self.display_length)
                
            elif title == 'disp_cont':
                self.dfs['disp_cont']=(pd.concat([self.dfs['disp_cont'], self.dfs[
                    'internal_memory'][self.dfs['disp_cont'].columns]], ignore_index=True)).drop_duplicates(
                        ).tail(self.display_length)
    
            else:
                self.dfs[title]=self.dfs['internal_memory'][self.dfs[title].columns].copy()
        
        # Now we print tables of the data we wish to display.
        print('\n')
        vis=self.dfs['disp_sensing'].apply(pd.to_numeric, errors='coerce').round(3)
        # table format github is a little prettier than the standard
        print(tabulate(vis, headers='keys', tablefmt='github'))
        print('\n')
        vis=self.dfs['disp_cont'].apply(pd.to_numeric, errors='coerce').round(2)
        print(tabulate(vis, headers='keys', tablefmt='github'))
        
        # Print the state counter, which stores how long we have been in this specific SS/USS state for.
        print(f'\n State counter: {self.state_counter}')
      
    def gather_data(self):
        # Work through each of the devices and collect their latest stored attributes.
        tempdict={}
        for mode, subdict in self.stored_variables.items():
            for device, attrlist in subdict.items():
                for attr in attrlist:
                    readings=np.array(getattr(
                        self.observed_objects[device],attr))
                    tempdict[device+'.'+attr]=readings                    
        

        n_rows=max([len(value) for value in tempdict.values()])
        # If there is not enough data available to display, then just display zeros.
        for attr, array in tempdict.items():
            if len(array)<n_rows:
                tempdict[attr]=array+ [0 for _ in range (n_rows)]
                
        # logger acquires time of first and last datapoints from DAQ
        # then subdivides into equal increments depending how many rows of data were returned
        # for n>1, ti=t0+(i*((tn-t0)/(n-1)))
        
        reading_period=self.SS_target.last_reading_time-self.SS_target.first_reading_time
        
        timearray=[]
        if n_rows>1:
            for i in range(n_rows):
                timearray.append(self.SS_target.first_reading_time+(
                   i*(reading_period/(n_rows-1))))
        else:
            timearray.append(self.SS_target.first_reading_time+(reading_period/2))
        tempdict['t']=np.round(timearray,2)        
        
        # commits all measurements to internal memory
        self.dfs['internal_memory']=pd.concat([self.dfs['internal_memory'], pd.DataFrame(
            tempdict)], ignore_index=True)

    def log_error(self,message):
        # If an error is flagged, need to log this in the error log file.
        if self.saving==True:
            dir_name=os.path.join(self.save_path,self.folder_name,'error_logs')
            title = 'error_log'
            
            file_name=''.join([title,'_',str(self.filenumber)+'.csv'])
            complete_name=os.path.join(dir_name,file_name)
                                                  
            # walk through files in target directory, get name of each. 
            filenames = next(os.walk(dir_name), (None, None, []))[2]                   

            # create temporary dict with information for writing to csv
            tempdict={}
            
            tempdict['t']= [message[0]]
            tempdict['type']=[message[1]]
            tempdict['target']=[message[2]]
            tempdict['status']=[message[3]]
            
            errordf=pd.DataFrame(tempdict)
            # write to csv (with header if new file)
            errordf.to_csv(complete_name, mode = 'a', header = (file_name not in filenames))
            print(f'Saving {complete_name}')  
            
        else:
            pass

    async def process(self):
        try:
            while not self._shutdown.is_set():
                self.status= 'waiting 0'
                for device in self.observed_objects.values():
                    if not device.new_values.is_set():
                        await device.new_values.wait()
                self.status= 'determining state 0'
                self.determine_state()       
                self.status= 'gathering 0'
                self.gather_data()
                self.status= 'extraction/display 0'
                self.extract_dfs()
                for device in self.observed_objects.values():
                    device.new_values.clear()
                
                self.check_length()
                
        except:
            self.status=re.sub('\d','2',self.status)
            
    def save_to_file(self,state):
        # When set to save, this function will append the most recent batch of data to the relevant CSV
        if self.saving==True:
            dir_name=os.path.join(self.save_path,self.folder_name)
            
            if state=='SS':
                savelist=['SS','USS']
            else:
                savelist=['USS']
                
            for mode in savelist:
                for title in self.dfs.keys():
                    if title == mode:
                        file_name=''.join([title,'_',str(self.filenumber)+'.csv'])
                        complete_name=os.path.join(dir_name,file_name)
                        complete_name.encode('unicode_escape')
                        
                        # walk through files in target directory, get name of each. 
                        filenames = next(os.walk(dir_name), (None, None, []))[2]                   
                        
                        # if starting a new run, want to automatically generate fresh csv id number
                        if self.startup==True:
                            
                            while file_name in filenames:
                                self.filenumber+=1
                                file_name=''.join([title,'_',str(self.filenumber)])
                            
                            complete_name=os.path.join(dir_name,file_name)
                            self.startup=False
                        
                        # write to csv (with header if new file)
                        self.dfs[mode].to_csv(complete_name, mode = 'a', header = (file_name not in filenames))
                        print(f'Saving {complete_name}')  
            
        else:
            print('Saving disabled. Skipping')
    
    def stop(self):
        self.status= 'Stopping 0'
        print(f'{self.state} saved')
        self.save_to_file(self.state)
        self.status= 'Wiping memory 0'
        self.dfs['internal_memory']=pd.DataFrame(columns=self.dfs[
            'internal_memory'].columns)
        
        print(f'\n{self.name}: shutting down')
        self._shutdown.set()   