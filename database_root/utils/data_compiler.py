#data_compiler.py | user retrieves a path to data from browsedb. now they want to see the data and do shit with it. this should have functions to accomplish that

import utils.plot_tools as pt
from backend_deep import get_data
import pandas as pd
from utils.templates import default_layout
from utils.constants import COLUMN_MAP_METRIC, COLUMN_MAP_STANDARD, INVALID_COLS, MASTER_FILE
from utils.tools import returnMetric
from plotly import graph_objects as go, express as px
import h5py
import xarray as xr, numpy as np
import h5rdmtoolbox as h5tbx
from dash import dcc, html
from utils.search_tools import show_atts

#all-purpose plot function. idea is this one function would be called with diff arguments by ui anytime a plot was requested. works with get_data in backend_deep.py
def compile_plot(path, master_file, dim, 
                 target: str, metric: bool = False, plot_all_from_df: bool = False,):
    data = get_data(path, master_file)
    #print(f"[DEBUG] compile_plot(): got data of type {type(data)} with plot_all_from_df={plot_all_from_df} and target={target}")
    
    #handle all dataframe cases. option to plot all data in a dataframe and return a list. if this is false, return a single plot determined by "target" argument
    if isinstance(data, pd.DataFrame):
        print('[ROUTE]: df case')
        metric_data = returnMetric(data)
        if target is None and not plot_all_from_df:
            print("no target for plot provided")
            return None
        time_column = pt.time_column(data)
        
        if not plot_all_from_df:    #generate one plot and return. in case where user selects multiple targets, call compile_plot() function multiple times
            if dim == 2:
                return pt.generate_2D_plot_df(target, data, metric_data, metric, COLUMN_MAP_STANDARD, COLUMN_MAP_METRIC, time_column)
            else:
                return pt.generate_3D_plot_df(target, data, metric_data, metric, COLUMN_MAP_STANDARD, COLUMN_MAP_METRIC)
            
        else:                       #if dim 2, generate list of 2d plots, if dim 3 do same
            #if this piece of shit doesnt work im gonna kms
            #print([col for col in data.columns])
            invalid = set(col.strip().lower() for col in INVALID_COLS)
            target_list = [t for t in data.columns if isinstance(t, str) and t.strip().lower() not in invalid]
            '''
            target_list = [tar for tar in data.columns]
            target_list = [t for t in target_list if t not in INVALID_COLS]
            '''

            if dim == 2:
                plot_tuples = []
                for d in target_list:
                    # (name of data, plot) for later reference if user would like to select one from list to view at a time
                    plot_tuples.append((d, pt.generate_2D_plot_df(d, data, metric_data, metric, COLUMN_MAP_STANDARD, COLUMN_MAP_METRIC, time_column)))
                return plot_tuples
                
            else:
                coords_3d = ['XPos', 'YPos', 'ZPos']
                target_list = [t for t in target_list if t not in coords_3d]
                plot_tuples = []
                for d in target_list:
                    plot_tuples.append((d, pt.generate_3D_plot_df(d, data, metric_data, metric, COLUMN_MAP_STANDARD, COLUMN_MAP_METRIC))) 
                return plot_tuples
    #------------------------------ end dataframe case

    elif isinstance(data, list) and len(data) == 1 and target is not None:
        #print('[ROUTE]: Dataset is list size one')
        if len(data) == 1 and target is not None:
            name, vals = data[0]
            realname = name.split('/')[-1]
            if dim == 2:
                return pt.generate_direct_2D_plot(vals, COLUMN_MAP_STANDARD, path, master_file)
            else:
                return pt.generate_direct_3D_plot(vals, realname, COLUMN_MAP_STANDARD, path, master_file)
    
    elif isinstance(data, list):
    #attempt to filter list to match the target if present
        if target is not None:
            short_target = target.split('/')[-1]
            matching = [(n, v) for n, v in data if n.endswith('/' + short_target) or n == short_target]

            if len(matching) == 1:
                #print(f"[ROUTE] Matched single dataset: {matching[0][0]}")
                name, vals = matching[0]
                realname = name.split('/')[-1]

                if dim == 2:
                    return pt.generate_direct_2D_plot(vals, COLUMN_MAP_STANDARD, path, master_file)
                else:
                    return pt.generate_direct_3D_plot(vals, realname, COLUMN_MAP_STANDARD, path, master_file)

        #fallback: full list of datasets (plot-all case)
        #print("[ROUTE]: full list of datasets plotting all")
        plot_tuples = []
        invalid = set(col.strip().lower() for col in INVALID_COLS)

        for i, (n, v) in enumerate(data):
            if hasattr(v, 'values'):
                v = v.values
            if isinstance(v, xr.DataArray):
                v = v.values
            if not isinstance(v, (np.ndarray, list)):
                print(f"[SKIP] Dataset {n} is not a plottable array: {type(v)}")
                continue
            if isinstance(n, str) and n.strip().lower() in invalid:
                print(f"[SKIP] Skipping invalid 2D dataset: {n}")
                continue
            
            if dim == 2:
                result = pt.generate_direct_2D_plot(v, COLUMN_MAP_STANDARD, n, master_file)
                if isinstance(result, list):
                    for j, fig in enumerate(result):
                        name = f'{n}_{j}'
                        plot_tuples.append((name, fig))
                else:
                    plot_tuples.append((n, result))
            
            else:
                realname = n.split('/')[-1]
                fig = pt.generate_direct_3D_plot(v, realname, COLUMN_MAP_STANDARD, path, master_file)
                plot_tuples.append((n, fig))

        return plot_tuples

#now create plots with selected data on the same plot  
def compile_stacked_plots(stacked_vars: list, normalized_times):
    with h5tbx.File(MASTER_FILE, 'r') as master:
        try:
            fig = go.Figure()
            for i, path in enumerate(stacked_vars):
                ds = master[path]
                names = path.split('/')

                fig.add_trace(go.Scatter(
                    x = normalized_times[i],
                    y = ds[:],
                    mode = 'lines',
                    name = f'{names[-1]} (/{names[-3]}/{names[-2]})',
                ))
            
            fig.update_layout(default_layout())
            fig.update_layout(width = 1500, height = 800)
            return dcc.Graph(figure = fig), fig

        except Exception as e:
            print(f'Something went wrong, check console. {e}')
            return None, None

#compile attributes, information and send back in a format that can be interpreted by dash
def compile_atts(path):
    if path is None:
        path = '/'
    with h5tbx.File(MASTER_FILE, 'r') as master:
        if path in master: #should always be true
            node = master[path]
            if path == '/':
                name = MASTER_FILE
            else:
                name = path.split('/')[-1]
            atts = [f'{key}: {int(round(val, 0)) if isinstance(val, float) else val}' for key, val in node.attrs.items()]
            #print(atts)
            
            return html.Div([
                html.Br(),
                html.H6(f'Metrics for {name}:'),
                show_atts(atts)
            ], style = {'padding-left': '300px', 'padding-right': '300px'})

