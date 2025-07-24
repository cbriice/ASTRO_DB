import pandas as pd
import h5rdmtoolbox as h5tbx
import os
from utils.helpers import get_stats
from utils.constants import MACHINEFILE_HEADERS
from utils.lock import master_lock

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

    print(f'[HDF5] Created build file: {build_file}')
    return build_file, stat_atts            #stat_atts should be passed as argument in merge_build_to_master in metadata spot

#merger function (to master)
def merge_build_to_master(master_file, alloy: str, build_id:str, build_file, metadata: dict = None):
    build_path = f'/{alloy}/builds/{build_id}'
    if metadata is None:
        metadata = {}
    
    metadata.update({'build_id': build_id})      #give every build an attribute with its id for search purposes
    metadata.update({'alloy': alloy})

    with master_lock:
        with h5tbx.File(master_file, 'a') as master, h5tbx.File(build_file, 'r') as build:
            if f'/{alloy}/builds/{build_id}' in master and master[f'/{alloy}/builds/{build_id}'].keys() is not None:
                print(f'[SKIP] Build {build_id} already exists in master file.')
                return
            else:
                print(f'[HDF5] Adding build {build_id} to master file...')
                master.copy(build['/machine_data'], f'/{alloy}/builds/{build_id}/machine_data')
                print(f'[HDF5] Tagging {build_path}.')
                g = master.require_group(build_path)
                for attr, value in metadata.items():
                    g.attrs[attr] = value
            
            if f'/{alloy}/builds/{build_id}' in master:
                print(f'[HDF5] {build_id} successfully merged into {master_file}.')
    
    #delete original file to keep it from clogging local directory
    os.remove(build_file)