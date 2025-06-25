#deeplayer_funcs.py - should hopefully be robust enough for the semi-infinite database that mitch wants from me

import h5rdmtoolbox as h5tbx
import pandas as pd
from utils.helpers import save_df
import numpy as np
import json, pickle, utils.tools, h5py
from dash import html

#this function might not be useful considering i have require_group lines in all of add_data to make sure no errors happen but ima leave it here anyways
def add_group(master_file, parent_path: str, name: str) -> str: 
    path = f'{parent_path}/{name}'
    with h5tbx.File(master_file, 'a') as master:
        if path in master:
            print(f'[SKIP] {path} already in {master}.')
        else:
            master.require_group(path)
            print(f'Created group: {master_file}{path}')    #assuming path is /builds/...
    return path

#should be able to handle all kinds of data and add them at any address specified by the user
def add_data(data, master_file, parent_path, name, data_isfilename: bool) -> bool:  #returns bool which indicates success of adding data
    path = f'{parent_path}/{name}'
    
    #is the user passing a file path in the directory? this accesses the file instead of passing the string on to be stored literally
    if data_isfilename:
        if isinstance(data, str):
            if data.endswith('csv'):
                file = pd.read_csv(data)
                save_df(master_file, parent_path, file, name)
                print(f'Saved data as {type(data)} to {path}')
                return True
            #else: handle other file type cases here. not sure which would be necessary
        else:
            print(f'[ERROR]: Argument "data_isfilename" was passed as True, but "data" was not passed as a string filename. Datatype: {type(data)}')
            return False

    else:
        try:
            #dataframe
            if isinstance(data, pd.DataFrame):
                save_df(master_file, parent_path, data, name)
                print(f'Saved data as {type(data)} to {path}')
                return True
            
            #string
            elif isinstance(data, str):
                dt = h5py.string_dtype(encoding = 'utf-8')
                with h5tbx.File(master_file, 'a') as master:
                    g = master.require_group(parent_path)
                    g.create_dataset(name, data=data, dtype = dt)
                    print(f'Saved data as {type(data)} to {path}')
                    return True
                
            #image, excel, pdf, etc
            elif isinstance(data, (bytes, bytearray)):
                with h5tbx.File(master_file, 'a') as master:
                    g = master.require_group(parent_path)
                    g.create_dataset(name, data = np.void(data))
                    print(f'Saved data as {type(data)} to {path}')
                    return True
                
            #file (get contents and store)
            elif hasattr(data, 'read'):
                file_data = data.read()
                with h5tbx.File(master_file, 'a') as master:
                    g = master.require_group(parent_path)
                    g.create_dataset(name, data = np.void(file_data))
                    print(f'Saved data as {type(data)} to {path}')
                    return True
            
            #dict
            elif isinstance(data, dict):
                try:
                    j = json.dumps(data)
                    dt = h5py.string_dtype(encoding='utf-8')
                    with h5tbx.File(master_file, 'a') as master:
                        g = master.require_group(parent_path)
                        g.create_dataset(name, data = j, dtype = dt)
                        print(f'Saved data (JSON) to {path}')
                        return True
                except:
                    try:
                        with h5tbx.File(master_file, 'a') as master:
                            g = master.require_group(parent_path)

                            for k, v in data.items():
                                if isinstance(v, (int, float, str, np.ndarray, list)):
                                    if isinstance(v, list):
                                        v = np.array(v)
                                    g.create_dataset(name=k, data=v)
                                else:
                                    #dict has some freaky shit in it if we get here. pickle (?) the weird stuff
                                    g.create_dataset(name=k, data = np.void(pickle.dumps(v)))

                            print(f'Saved data (per-key) to {path}')
                            return True
                    except Exception as e:
                        print(f'Dict contents cant be processed. {e}')
                        return False
                
            #array
            elif isinstance(data, np.ndarray):
                arr = np.array(data)
                if arr.dtype == 'object':
                    serialized = json.dumps(data)
                    dt = h5py.string_dtype(encoding='utf-8')
                    with h5tbx.File(master_file, 'a') as master:
                        g = master.require_group(parent_path)
                        g.create_dataset(name, data = serialized, dtype = dt)
                        print(f'Saved data as {type(data)} to {path}')
                        return True
                else:
                    with h5tbx.File(master_file, 'a') as master:
                        g = master.require_group(parent_path)
                        g.create_dataset(name, data = data)
                        print(f'Saved data as {type(data)} to {path}')
                        return True
            
            #python list
            elif isinstance(data, list):
                try:
                    arr = np.array(data)
                    with h5tbx.File(master_file, 'a') as master:
                        g = master.require_group(parent_path)
                        g.create_dataset(name, data = arr)
                        print(f'Saved data as {type(data)} to {path}')
                        return True
                except:
                    dt = h5py.special_dtype(vlen=str)
                    with h5tbx.File(master_file, 'a') as master:
                        g = master.require_group(parent_path)
                        g.create_dataset(name, data = str(data), dtype = dt)
                        print(f'Saved data as {type(data)} to {path}')
                        return True
        
        except Exception as e:
            print(f'[ERROR]: Failed to add {name} at {path}. Unexpected datatype {type(data)}. "{e}"')
            return False
            
#function to add attributes if presented in dict form. search_tools.py has more general function
def add_attrs(master_file, path, atts):
    with h5tbx.File(master_file, 'a') as master:
        if isinstance(atts, dict):
            if path in master:
                for k, v in atts.items():
                    master[path].attrs[k] = v
                return True
            else:
                print(f'[ERROR]: Failed to add attributes, {path} not in {master}')
                return False
        else:
            print(f'[ERROR]: Atts should be in dict form, not {type(atts)}')
            return False

#retrieve data given path. pairs to outputs of add_data()
def get_data(path, master_file): 
    with h5tbx.File(master_file, 'r') as master:
        node = master[path]

        if isinstance(node, h5py.Dataset):
            name = path.split('/')[-1]
            return [(name, node[:])]

        elif isinstance(node, h5py.Group):
            keys = list(node.keys())
            if not keys:
                print(f"Empty group: {path}")
                return []

            #mixed or all-dataset group
            data_arr = []
            for k in keys:
                try:
                    item = node[k]
                    if isinstance(item, h5py.Dataset):
                        data_arr.append((f'{path}/{k}', item[:]))

                except Exception as e:
                    print(f"Error accessing {path}/{k}: {e}")

            if not data_arr:
                print(f"No datasets found in {path}. Contents: {keys}")
            return data_arr

        else:
            print(f"Unrecognized object type at {path}: {type(node)}")
            return []
    