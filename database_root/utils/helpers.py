import pandas as pd
import h5rdmtoolbox as h5tbx
import h5py, base64, io
from utils.tools import find_header_line
from utils.plot_tools import universal_decode
from dash import html
from pandas import DataFrame as df
from utils.constants import METRICS_MACHINEFILE, MASTER_FILE, COLUMN_MAP_STANDARD
import numpy as np
from utils.lock import master_lock

#save dataframe to database
def save_df(master_file, build_path, df: pd.DataFrame, name='raw_csv_data'):
    with master_lock:
        with h5tbx.File(master_file, 'a') as master:
            g = master.require_group(f'{build_path}/{name}')
            for col in df.columns:
                data = df[col].values
                g.create_dataset(name = col, data = data)

#retrieve saved dataframe. would pass "machine_data" as name argument for example to reconstruct original machine csv from where it's saved
def get_df(master_file, path, name):
    with h5tbx.File(master_file, 'r') as master:
        if f'{path}/{name}' in master:
            g = path[name]
            data = {col: g[col][:] for col in g.keys()}
            return pd.DataFrame(data)
        else:
            print(f'[ERROR]: {path}/{name} doesnt exist in {master}. Returning type None')
            return None

import dash
def ntng():
    return dash.no_update

def get_keys(file, master_file):
    with h5tbx.File(master_file, 'r') as master:
        if isinstance(file, str):
            if file == master_file:
                return [{'label': k, 'value': f'/{k}'} for k in list(master.keys())]
            
            elif file.startswith('/'):
                try:
                    return [{'label': k, 'value': f'{file}/{k}'} for k in list(master[file].keys())] if isinstance(master[file], h5py.Group) else []
                except:
                    return []
                
            else: return []
        else: return []

#helper for data upload to decide what type of file it is and how to output to be handled by add_data()
def process_upload(contents, input_string):
    if contents is None:
        return input_string
    else:
        try:
            content_type, content = contents.split(',', 1)
        except:
            content_type = None
            content = None

        if content and content_type:
            #cleaning up base64 encoding in case it breaks somewhere
            cleaned_content = content.strip().replace('\n', '').replace('\r', '')
            missing_padding = len(cleaned_content) % 4
            if missing_padding:
                cleaned_content = cleaned_content + '=' * (4 - missing_padding)
            decoded = base64.b64decode(cleaned_content)

            if content_type.startswith('data:text/csv'):
                try:
                    decoded_shit = universal_decode(decoded)
                    sio = io.StringIO(decoded_shit)
                    header_row = find_header_line(sio)
                    #print(header_row)
                    sio.seek(0)
                    return pd.read_csv(sio, skiprows = header_row)
                except Exception as e:
                    print(f'Error decoding CSV: {e}')
                    return None

            elif 'application' in content_type or 'image' in content_type:
                return io.BytesIO(decoded)

            else:
                try:
                    return io.StringIO(decoded.decode('utf-8'))
                except UnicodeDecodeError:
                    return io.BytesIO(decoded)
        
        else:
            print(f'data could not be processed. input {contents} ({type(contents)}) shit the bed')
            return None

def verify_existence(path):
    with h5tbx.File(MASTER_FILE, 'r') as master:
        if path in master:
            valid_path = False
            warnings = []
            if isinstance(master[path], h5py.Dataset):
                return html.Span(f'{path} validated.', style = {'color': 'green'}), True
            
            for key in master[path].keys():
                if isinstance(master[path][key], h5py.Dataset):
                    valid_path = True
                else:
                    warnings.append(key)

            if valid_path and not warnings:
                return html.Span(f'{path} validated.', style = {'color': 'green'}), True
            elif valid_path and warnings:
                return [html.Span(f'{path} validated. ', style = {'color': 'green'}), html.Span(f'WARNING: don\'t try to plot {warnings}, they aren\'t datasets.', style = {'color': 'orange'})], True
            else:
                return html.Span(f'No datasets found at {path}.', style = {'color': 'red'}), False
        else:
            return html.Span(f'{path} not found in {master}.', style = {'color': 'red'}), False
        
def verify_stack(path, stack):
    #catch groups and reject
    with h5tbx.File(MASTER_FILE, 'r') as master:
        if path in master:
            node = master[path]
            if isinstance(node, h5py.Group):
                return html.Span(f'{path} is a group, stacked plot addresses must be datasets.', style = {'color': 'red'}), False
     
    validation, check = verify_existence(path)
    if path in stack:
        return html.Span(f'{path} cannot be stored twice.', style = {'color': 'red'}), False
    else:
        return validation, check
        
def generate_plot_list(plot_dict):
    asdf = []
    for n in plot_dict.keys():
        name = n.split('/')[-1]
        asdf.append({'label': name, 'value': n})
    return asdf

def display_stack(stack):
    namelist = [s.split('/')[-1] for s in stack]
    return f'{namelist}'

def generate_dset_list(stack):
    with h5tbx.File(MASTER_FILE, 'r') as master:
        return [master[path] for path in stack]
    
#get stats and package to be added as attributes. for machine files because mets is a predefined list of metrics that machine files have, not automatically driven
def get_stats(userfile: pd.DataFrame, mets, csv_path) -> dict:
    stats = {}
    for met in mets:
        if met in userfile.columns:
            stats[f'{met}_max'] = float(userfile[met].max())
            stats[f'{met}_min'] = float(userfile[met].min())
            stats[f'{met}_avg'] = float(userfile[met].mean())
        else:
            print(f'Warning: {met} not found in userfile columns. Skipping.')
    if csv_path:
        stats.update({'csv_path': f'{csv_path}'})             
    return stats

def to_float(val):
    try:
        return np.float64(val.item())
    except AttributeError:
        return np.float64(val)    

#assume path passed here is the parent of the dataset
def auto_assign_atts(path):
    with master_lock:
        with h5tbx.File(MASTER_FILE, 'a') as master:
            if path in master:
                node = master[path]
                if isinstance(node, h5py.Group):    #should always be true but sanity check

                    for name, ds in node.items():
                        if isinstance(ds, h5py.Dataset) and np.issubdtype(ds.dtype, np.number):    #only do this for datasets not subgroups
                            data = ds[:]
                            node.attrs[f'{name}_min'] = to_float(np.min(data))
                            node.attrs[f'{name}_max'] = to_float(np.max(data))
                            node.attrs[f'{name}_avg'] = to_float(np.mean(data))
                            print(f'Stats for {name} processed')
                        else:
                            print(f'Skipped non-numeric dataset: {name}')
                    
                    return True
                else:
                    print(f'{path} not a group and it should be so idk what u doing')
                    return False
            else:
                print(f'{path} not in {master}')
                return False
                
def get_all_att_keys():
    att_keys = set()
    with h5tbx.File(MASTER_FILE, 'r') as master:
        def collect_attrs(name, obj):
            att_keys.update(obj.attrs.keys())
        
        master.visititems(collect_attrs)
    return sorted(att_keys)

def analysis_table(comp_list, normalized_diff):
    table_rows = []
    for key, val in comp_list:
        table_rows.append(html.Tr([
            html.Td(COLUMN_MAP_STANDARD.get(key, key), style = {'border': '1px solid black'}), 
            html.Td(val, style = {'border': '1px solid black', 'text-align': 'right'})
        ]))
    table_rows.append(
        html.Tr([
            html.Td('Normalized difference:', style = {'fontWeight': 'bold', 'border': '1px solid black'}), 
            html.Td(normalized_diff, style = {'fontWeight': 'bold', 'border': '1px solid black'})
        ])
    )

    return html.Table([
        html.Thead(
            html.Tr([html.Th('Metric'), html.Th('% Difference')])),
            html.Tbody(table_rows)
    ], style = {
        'borderCollapse': 'collapse',
        'border': '1px solid black'
        })