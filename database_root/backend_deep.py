#deeplayer_funcs.py - should hopefully be robust enough for the semi-infinite database that mitch wants from me

import h5rdmtoolbox as h5tbx
import pandas as pd
from utils.helpers import save_df
import numpy as np
import json, pickle, h5py
from utils.lock import master_lock
from utils.tools import find_adjacent, find_index
from utils.constants import MAT_TESTING_TABLES

#this function might not be useful considering i have require_group lines in all of add_data to make sure no errors happen but ima leave it here anyways
def add_group(master_file, parent_path: str, name: str) -> str: 
    path = f'{parent_path}/{name}'
    with master_lock:
        with h5tbx.File(master_file, 'a') as master:
            if path in master:
                print(f'[SKIP] {path} already in {master}.')
            else:
                master.require_group(path)
                print(f'Created group: {master_file}{path}')    #assuming path is /builds/...
    return path

#should be able to handle all kinds of data and add them at any address specified by the user
#ngl half of this function is probably useless but its one of the first things i coded and i was given no direction so fuck it
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
                with master_lock:
                    with h5tbx.File(master_file, 'a') as master:
                        g = master.require_group(parent_path)
                        g.create_dataset(name, data=data, dtype = dt)
                        print(f'Saved data as {type(data)} to {path}')
                        return True
                
            #image, excel, pdf, etc
            elif isinstance(data, (bytes, bytearray)):
                with master_lock:
                    with h5tbx.File(master_file, 'a') as master:
                        g = master.require_group(parent_path)
                        g.create_dataset(name, data = np.void(data))
                        print(f'Saved data as {type(data)} to {path}')
                        return True
                
            #file (get contents and store)
            elif hasattr(data, 'read'):
                file_data = data.read()
                with master_lock:
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
                    with master_lock:
                        with h5tbx.File(master_file, 'a') as master:
                            ds_path = f'{parent_path}/{name}'
                            if ds_path in master:
                                print(f'{ds_path} already exists in database. Overwriting existing data. Hopefully this isnt accidental lol')
                                del master[ds_path]
                            g = master.require_group(parent_path)
                            g.create_dataset(name, data = j, dtype = dt)
                            print(f'Saved data (JSON) to {path}')
                            return True
                except:
                    try:
                        with master_lock:
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
                #handle exsitu csv processing logic separately
                if data.dtype == object and data.ndim == 2 and data.shape[1] == 2:
                    try:
                        d = {str(k): v for k, v in data}
                        return add_data(d, master_file, parent_path, name, False)
                    except Exception as e:
                        print(f'Could not convert (key, value) ndarray to dict: {e}')
                        return False
                #normal logic
                arr = np.array(data)
                if arr.dtype == 'object':
                    serialized = json.dumps(data)
                    dt = h5py.string_dtype(encoding='utf-8')
                    with master_lock:
                        with h5tbx.File(master_file, 'a') as master:
                            g = master.require_group(parent_path)
                            g.create_dataset(name, data = serialized, dtype = dt)
                            print(f'Saved data as {type(data)} to {path}')
                            return True
                else:
                    with master_lock:
                        with h5tbx.File(master_file, 'a') as master:
                            g = master.require_group(parent_path)
                            g.create_dataset(name, data = data)
                            print(f'Saved data as {type(data)} to {path}')
                            return True
            
            #python list
            elif isinstance(data, list):
                try:
                    arr = np.array(data)
                    with master_lock:
                        with h5tbx.File(master_file, 'a') as master:
                            g = master.require_group(parent_path)
                            g.create_dataset(name, data = arr)
                            print(f'Saved data as {type(data)} to {path}')
                            return True
                except:
                    dt = h5py.special_dtype(vlen=str)
                    with master_lock:
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
    with master_lock:
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
    
#goal here: store each row as a dataset under the folder defined by coordinates, name is Build Name. alloy, build/test temper, test dir are default atts
#--------these functions are going to be hardcoded as shit to template so if formatting changes for exsitu csvs this will have to change too-----------
def process_exsitu(df):
    if not isinstance(df, pd.DataFrame):
        print(f'idk how u fucked this up but {type(df)} shouldve been a dataframe from process_upload()')
        return False
    
    #assuming all of these values are in csv like [Build Name | Name] where | separates two columns in the same row. these values are for atts
    atts_dict = {}
    build_name = find_adjacent(df, 'Build ID') or find_adjacent(df, 'Build Name')
    atts_dict.update({'build_id': build_name})
    alloy = find_adjacent(df, 'Build Alloy') or find_adjacent(df, 'Alloy')
    if 'AA' not in alloy:
        alloy = 'AA' + alloy
    atts_dict.update({'build_alloy': alloy})
    build_temper = find_adjacent(df, 'Build Temper')
    atts_dict.update({'build_temper': build_temper})
    test_temper = find_adjacent(df, 'Test Temper')
    atts_dict.update({'test_temper': test_temper})

    #separate file into sub-dataframes for each test table in template
    df_list = []
    for title in MAT_TESTING_TABLES:
        row_start, col_start = find_index(df, title)
        header_row = row_start + 1   #shift down one to exclude title cell in trimmed df
        data_start = header_row + 1  #data starts here
        new_cols = df.iloc[header_row, col_start:].values   #get table headers and assign as cols of trimmed df
        trimmed_df = df.iloc[data_start:, col_start:]
        trimmed_df.columns = new_cols

        valid_rows_mask = trimmed_df.notna().any(axis = 1)
        row_end = row_start + valid_rows_mask.idxmin() if not valid_rows_mask.all() else len(df)

        valid_cols_mask = trimmed_df.notna().any(axis = 0)
        if not valid_cols_mask.all():
            first_blank_col_label = valid_cols_mask.idxmin()
            first_blank_col_index = trimmed_df.columns.get_loc(first_blank_col_label)
            col_end = col_start + first_blank_col_index
        else:
            col_end = len(df.columns)           #too scared to get rid of this code even tho its not used bc i just got it to work smh

        final_trim = trimmed_df.iloc[:row_end - trimmed_df.index[0], :valid_cols_mask.sum()]
        df_list.append((title, final_trim))
    
    return df_list, atts_dict

#then this function gets called and cycles through for each df stored in df list
def add_exsitu(df_list, atts: dict, master_file):
    status_tracker = []
    status_tracker_atts = []
    illegal = ['Test direction', 'Test number']

    for (title, df) in df_list:
        #cycle through each row and create a dataset to be processed using add_data() 
        for r, _ in df.iterrows():
            if r == 1:
                continue
            values = []
            for col in df.columns:
                val = df.loc[r, col]          #access cell at row number r, column name col
                values.append((col, val))
            arr = np.array(values, dtype = object)      #get 2 column array

            #first 3 values of table should be coordinates
            _, x = values[0]
            _, y = values[1]
            _, z = values[2]
            coords = f'{x}-{y}-{z}'
            if 'nan' in coords:
                continue        #im not abt to figure out why pandas grabs nan rows but i can just skip them lol
            #columns [3] and [4] should always be test direction and test number according to template
            _, test_dir = values[3]
            _, test_num = values[4]
            name = f'{test_dir}-{test_num}'
            if any(il.strip().lower() in name.strip().lower() for il in illegal):
                continue        #skip if program grabs table headers instead of actual data (once again idk why it does but i can catch it)
            
            atts.update({'coordinates': coords})
            atts.update({'test_direction': test_dir})
            new_title = title.replace(' ', '-')
            build_info = f"{atts['build_id']}-{atts['build_temper']}"
            address = f"/{atts['build_alloy']}/ex-situ/{new_title}/{build_info}"
            full_path = f'{address}/{name}'

            #add each 2 column array to database and tag all with the same atts derived from original uploaded file
            success = add_data(arr, master_file, address, name, False)
            atts_success = add_attrs(master_file, full_path, atts)

            status_tracker.append(success)
            status_tracker_atts.append(atts_success)
    
    if False in status_tracker:
        return False
    
    if False in status_tracker_atts:
        return False

    return True
    
        