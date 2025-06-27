from dash import dcc, html
import h5rdmtoolbox as h5tbx
from utils.tools import intersection, percent_diff, magnitude
from collections import defaultdict
from utils.constants import COLUMN_MAP_STANDARD
import numpy as np
import h5py
from utils.lock import master_lock
   
#find shit that meets certain attribute conditions
def lowerbound_search(master_file, att, lowerbound, groupsonly):
    if groupsonly:
        try:
            return h5tbx.database.find(master_file, {att: {'$gte': lowerbound}}, objfilter = 'group')
        except TypeError as e:
            print(f'Skipping attribute {att}, type mismatch: {e}')
    else:
        try:
            return h5tbx.database.find(master_file, {att: {'$gte': lowerbound}})
        except TypeError as e:
            print(f'Skipping attribute {att}, type mismatch: {e}')

def upperbound_search(master_file, att, upperbound, groupsonly):
    if groupsonly:
        try:
            return h5tbx.database.find(master_file, {att: {'$lte': upperbound}}, objfilter = 'group')
        except TypeError as e:
            print(f'Skipping attribute {att}, type mismatch: {e}')
    else:
        try:
            return h5tbx.database.find(master_file, {att: {'$lte': upperbound}})
        except TypeError as e:
            print(f'Skipping attribute {att}, type mismatch: {e}')
    
#find shit that meets certain attribute conditions
def search_for_att(master_file, att: str, groupsonly: bool, lowerbound = None, upperbound = None, exactvalue = None):
    if exactvalue:
        if isinstance(exactvalue, str):
            if groupsonly:
                return  h5tbx.database.find(master_file, {att: {'$eq': exactvalue}}, objfilter = 'group')
            else:
                return h5tbx.database.find(master_file, {att: {'$eq': exactvalue}})
        else:
            exactvalue = np.float64(exactvalue)
            if groupsonly:
                return  h5tbx.database.find(master_file, {att: {'$eq': exactvalue}}, objfilter = 'group')
            else:
                return h5tbx.database.find(master_file, {att: {'$eq': exactvalue}})
    
    elif lowerbound is not None and upperbound is not None:
        lowerbound = np.float64(lowerbound)
        upperbound = np.float64(upperbound)
        res_lower = lowerbound_search(master_file, att, lowerbound, groupsonly)
        res_upper = upperbound_search(master_file, att, upperbound, groupsonly)
        if res_lower and res_upper:
            return intersection(res_lower, res_upper)
        else:
            return []
            
    elif lowerbound is not None and upperbound is None:
        lowerbound = np.float64(lowerbound)
        return lowerbound_search(master_file, att, lowerbound, groupsonly)
    
    elif upperbound is not None and lowerbound is None:
        upperbound = np.float64(upperbound)
        return upperbound_search(master_file, att, upperbound, groupsonly)
        
    else:
        if groupsonly:
            return  h5tbx.database.find(master_file, {att: {'$exists': True}}, objfilter = 'group')
        else:
            return h5tbx.database.find(master_file, {att: {'$exists': True}})
        
#show atts of selected build or file or whatever
def show_atts(atts):
    metric_dict = defaultdict(dict)
    misc = []

    #separate into numerical and other attributes
    for att in atts:
        key, val = att.split(':', 1)
        key = key.strip()
        key = key.replace(':', '')
        val = val.strip()

        if any(key.endswith(suffix) for suffix in ['_min', '_max', '_avg']):
            if '_' in key:
                base, suffix = key.rsplit('_', 1)
                if suffix in ['min', 'max', 'avg']:
                    metric_dict[base][suffix] = val
                    continue
            misc.append(att)
        else:
            misc.append(att)

    metric_rows = [
        html.Tr([
            html.Td(COLUMN_MAP_STANDARD.get(metric, metric)),
            html.Td(stats.get('min', '—')),
            html.Td(stats.get('max', '—')),
            html.Td(stats.get('avg', '—')),
        ]) for metric, stats in sorted(metric_dict.items())
    ]
    metric_table = html.Table([
        html.Thead(html.Tr([
            html.Th("Metric"), html.Th("Min"), html.Th("Max"), html.Th("Avg")
        ])),
        html.Tbody(metric_rows)
    ], style = {'border': '1px solid black', 'borderCollapse': 'collapse', 'width': '70%', 'marginBottom': '20px'})

    misc_list = html.Ul([html.Li(att) for att in misc])
    return html.Div([metric_table, html.Hr(), html.H6("Other Attributes:"), misc_list])

def recursive_search(path, master):
    #open file before calling initial function
    dataset_list = []
    if path in master:
        node = master[path]
        if isinstance(node, h5py.Group):
            for name, obj in node.items():
                if isinstance(obj, h5py.Group):
                    dataset_list.extend(recursive_search(obj.name, master))
                elif isinstance(obj, h5py.Dataset):
                    dataset_list.append(obj.name)
        elif isinstance(node, h5py.Dataset):
            dataset_list.append(node.name)
        return dataset_list

def show_datasets(path, master_file):
    with h5tbx.File(master_file, 'r') as master:
        datasets = sorted(recursive_search(path, master))
        if not datasets:
            return html.Div([html.Span(f'No datasets found in {path}')])
    name = path.split('/')[-1]

    return html.Div([
        dcc.Dropdown(
        id = {'type': 'dataset-dropdown', 'group': path},
        options = [{'label': f"{ds.split('/')[-2]}/{ds.split('/')[-1]}", 'value': ds} for ds in datasets],
        placeholder = f'View datasets within {name}',
    ),html.Br(),
        html.Div(id = {'type': 'dataset-preview', 'group': path})
    ])
    
#more generalized version of add_attrs() in backend_deep.py which only handles dict case
#basically i forgot that other function was there and wrote this one and ima just leave them 
def add_attribute(path, att_name, att_value, master_file):
    with master_lock:
        with h5tbx.File(master_file, 'a') as master:
            if path not in master:
                print(f'{path} not found in {master}')
                return False
            node = master[path]
            node.attrs[att_name] = att_value
            print(f'Attribute [{att_name}: {att_value}] added to {path}')
            return True
        
#conformance comp for comparing two builds or data or whatever
def conformance_comp(path1, path2, master_file):
    percent_list = []
    with h5tbx.File(master_file, 'r') as master:
        node = master[path1]
        node_atts = node.attrs.items()
        comp = master[path2]
        comp_atts = comp.attrs.items()

        for key, val in node_atts:
            if key in comp_atts:
                percent_list.append((key, percent_diff(node.attrs[key], comp.attrs[key])))

    normalized_diff = magnitude(percent_list)
    return percent_list, normalized_diff