# toplayer_funcs.py: functions to create first layers of database (processing csvs)

import pandas as pd
import numpy as np
import h5rdmtoolbox as h5tbx
import os
from utils.helpers import get_stats, save_df
from utils.constants import MACHINEFILE_HEADERS

#create master file (only needs to run once)
def create_master_file(master_path: str, metadata: dict = None):
    with h5tbx.File(master_path, 'a') as h5:
        if metadata:
            for attr, value in metadata.items():
                h5.attrs[attr] = value

#function to take csv file and convert to hdf5. attributes listed in metadata (dict). for MACHINE data 
def create_machine_hdf5(csv_path, build_id: str, filename):
    if isinstance(csv_path, str):
        df = pd.read_csv(csv_path)
    else:
        df = csv_path
    build_file = f'{build_id}.h5'
    stat_atts = get_stats(df, MACHINEFILE_HEADERS, filename)

    #puts machine data
    with h5tbx.File(build_file, 'w') as h5:
        input_group = h5.require_group(f'/machine_data')
        #create a dataset for each column in the input csv from the machine, and then assign metadata as attributes 
        for col in df.columns:
            input_group.create_dataset(col, data = df[col].dropna().values, maxshape=(None,), chunks=True)

    print(f'Created build file: {build_file}')
    return build_file, stat_atts            #stat_atts should be passed as argument in merge_build_to_master in metadata spot

#merger function (to master)
def merge_build_to_master(master_file, alloy: str, build_id:str, build_file, metadata: dict = None):
    build_path = f'/{alloy}/builds/{build_id}'
    if metadata is None:
        raise ValueError('WARNING: Each build should have metadata associated with it.')
    
    metadata.update({'id': build_id})      #give every build an attribute with its id for search purposes
    metadata.update({'alloy': alloy})

    with h5tbx.File(master_file, 'a') as master, h5tbx.File(build_file, 'r') as build:
        if f'/{alloy}/builds/{build_id}' in master and master[f'/{alloy}/builds/{build_id}'].keys() is not None:
            print(f'[SKIP] Build {build_id} already exists in master file.')
            return
        else:
            print(f'Adding build {build_id} to master file...')
            master.copy(build['/machine_data'], f'/{alloy}/builds/{build_id}/machine_data')
            print(f'Tagging {build_path}.')
            g = master.require_group(build_path)
            for attr, value in metadata.items():
                g.attrs[attr] = value
        
        if f'/{alloy}/builds/{build_id}' in master:
            print(f'{build_id} successfully merged into {master_file}.')
    
    #delete original file to keep it from clogging local directory
    os.remove(build_file)

#creates hdf5 for SENSOR data (important because it's hardcoded for sensor formatting according to Greg's formatting)
def create_sensor_hdf5(sensor_type: str, csv_path: str, metadata: dict = None): 
    if isinstance(csv_path, str):
        df = pd.read_csv(csv_path)
    else:
        df = csv_path
    sensor_file = f'{sensor_type}_output.h5'

    with h5tbx.File(sensor_file, mode = 'w') as h5:
        group = h5.create_group(f'{sensor_type}_data')
    #create a new group for each column (sensor) from the data and store as unique datasets under main group
        for col in df.columns:
            data = df[col].values
            if df[col].dtype == 'object':
                data = data.astype('S')
            if metadata:
                group.create_dataset(
                    name = col, 
                    data = data, 
                    attrs = metadata
                )
            else:
                group.create_dataset(
                    name = col, 
                    data = data
                )
            
    print(f'Created {sensor_type} file: {sensor_file}')
    return sensor_file

#add data to build file (coded with syntax saying sensor but can be used for any data)
def merge_data_to_build(sensor_file, master_file, sensor_type: str, build_id: str):
    with h5tbx.File(sensor_file, 'r') as sensor, h5tbx.File(master_file, 'a') as master:
        sensor_group = f'{sensor_type}_data'
        build_path = f'/builds/{build_id}'
        target_path = f'{build_path}/{sensor_group}'
        #print(list(sensor.keys()))  
              
        if build_path not in master:
            raise ValueError(f'{build_id} not found in master file.')
        if target_path in master:
            print(f'[SKIP] Dataset {sensor_group} already exists in {build_path}: {target_path}')
            return
        
        try:
            master.require_group(f'/builds/{build_id}')
            master.copy(sensor[f'/{sensor_type}_data'], f'/builds/{build_id}/{sensor_type}_data')
            print(f'Merged {sensor_type} data into build file: /builds/{build_id}')
        except Exception as e:
            print(f'Failed to copy sensor data: {e}')

    #delete original file to keep it from clogging local directory    
    os.remove(sensor_file)

        