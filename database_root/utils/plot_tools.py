#plot_tools.py | generates plots and shit idk. functions called in data_compiler.py mostly
#lowkey the _df functions dont even get called a single time in my code somehow even though i intended for them to so they might be junk but ima leave em bc fuck it

#btw fuck github this piece of shit is impossible to use and unintuitive as fuck. not even gpt can help me do u understand how crazy that is
import pandas as pd
from plotly import graph_objects as go, express as px
from utils.constants import COLUMN_MAP_METRIC, COLUMN_MAP_STANDARD, MASTER_FILE
from utils.templates import default_layout
import h5rdmtoolbox as h5tbx
import h5py, os, io, numpy as np
import xarray as xr

#generates 2d plot for target data within dataframe
def generate_2D_plot_df(target: str, df: pd.DataFrame, metric_df: pd.DataFrame, metric: bool, column_map_standard, column_map_metric, time_column):
    #print('[ROUTE] generate_2d_plot_df')
    if target.startswith('/'):
        target = target.split('/')[-1]
    elif target not in df.columns:
        print(f'[PLOT ERROR]: Invalid target data to plot, {target} not in {list(df.columns)}. Try different file? Returning object type "None"')
        return None
    
    if metric:
        plot_df = metric_df
        column_map = column_map_metric
    else:
        plot_df = df
        column_map = column_map_standard
    
    layout = default_layout()
    plot = px.line(plot_df, x = time_column, y = target, 
                    labels = {time_column.name: "Time", target: column_map.get(target, target)})
    plot.update_layout(**layout)

    return plot 

#called if user inputs path which directly leads to data which can be plotted, not a dataframe
def generate_direct_2D_plot(data, column_map_standard, path, master_file):
    #print('[ROUTE] generate_DIRECT_2d_plot')
    time_column = find_time_column(path, master_file)
    column_map = column_map_standard
    layout = default_layout()

    if isinstance(data, list):
        plots = []
        for name, values in data:
            fig = px.line(
                x = time_column, 
                y = values, 
                labels = {"x": "Time", "y": column_map.get(name, name)}
            )
            fig.update_layout(**layout)
            plots.append(fig)
        return plots
    
    else:
        try:
            column_name = os.path.basename(path)
            plot = px.line(
                x = time_column, 
                y = data.values if hasattr(data, 'values') else data, 
                labels = {"x": "Time", "y": column_map.get(column_name, column_name)})
            return plot
        except Exception as e:
            print(f'Plot failed. data: {data}, type: {type(data)}. Returning None. | {e}')
            return None

#read the function name
def generate_3D_plot_df(target: str, df: pd.DataFrame, metric_df: pd.DataFrame, metric: bool, column_map_standard, column_map_metric):
    #print('[ROUTE] generate_3d_plot_df')
    if target.startswith('/'):
        target = target.split('/')[-1]
    elif target not in df.columns:
        print(f'[PLOT ERROR]: Invalid target data to plot, {target} not in {list(df.columns)}. Try different file? Returning object type "None"')
        return None
    
    if "XPos" not in df.columns or "YPos" not in df.columns or "ZPos" not in df.columns:
        print(f'[PLOT ERROR]: Either XPos, YPos or ZPos not detected in dataframe, unable to generate 3D plot. {list(df.columns)} Returning object type "None"')
        return None
    
    if metric:
        plot_df = metric_df
        column_map = column_map_metric
    else:
        plot_df = df
        column_map = column_map_standard

    scatterplot = px.scatter_3d(plot_df, x="XPos", y="YPos", z="ZPos", color = target, color_continuous_scale = 'Viridis',
                                labels = {
                                    "XPos": "X Position (mm)" if metric else 'X Position (inches)',
                                    "YPos": "Y Position (mm)" if metric else 'Y Position (inches)',
                                    "ZPos": "Z Position (mm)" if metric else 'Z Position (inches)',
                                    target: column_map[target] if target in column_map else target
                                })
    scatterplot = scatterplot.update_layout(height = 600, width = 850)
    scatterplot = scatterplot.update_scenes(aspectmode = "data")

    return scatterplot

#generate a scatterplot for individual dataset not given a dataframe
def generate_direct_3D_plot(data, name, column_map_standard, path, master_file):
    #print('[ROUTE] generate_DIRECT_3d_plot')
    column_map = column_map_standard
    xpos, ypos, zpos = find_xyz(path, master_file)
    realname = name.split('/')[-1]

    if xpos is not None and ypos is not None and zpos is not None:
        if hasattr(data, 'values'):
            data = data.values
        if isinstance(data, xr.DataArray):
            data = data.values
        if isinstance(data[0], bytes):
            print(f"[SKIP] Data contains bytes — not plottable as color. Data: {data[:5]}")
            return None
        color_data = np.array(data)

        scatterplot = go.Figure(
            data = [go.Scatter3d(
                x = xpos, y = ypos, z = zpos, mode = 'markers', 
                marker = dict(
                    size = 3,
                    color = color_data,
                    colorscale = 'Viridis',
                    colorbar = dict(title = column_map.get(realname, realname))
                )
            )]
        )
        scatterplot.update_layout(
            scene = dict(aspectmode = 'data'),
            height = 600, width = 850
        )
        return scatterplot
    
    else:
        return None

#gets time column from dataframe to be used in plot functions
def time_column(df: pd.DataFrame):
    if 'Timestamp' in df.columns:
        return pd.to_datetime(df['Timestamp'])
    elif 'Time (Seconds)' in df.columns or 'Time' in df.columns:
        
        if 'Time (Seconds)' in df.columns:
            col = df['Time (Seconds)']
            if isinstance(col.iloc[0], bytes):
                col = col.str.decode('utf-8')
            return pd.to_timedelta(col)
        
        else:
            col = df['Time']
            if isinstance(col.iloc[0], bytes):
                col = col.str.decode('utf-8')
            return pd.to_timedelta(col)
        
    #if none of those triggered
    print("[FORMAT ERROR] Error reading time column, check labeling and case sensitivity. Returning object type 'None'")
    return None
    
#called when direct plot function is called. all datasets should have a time dataset in the same folder the way i coded them to be processed, this finds it
def find_time_column(path: str, master_file):
    with h5tbx.File(master_file, 'r') as master:
        parent = os.path.dirname(path)
        sisters = list(master[parent].keys())

        if 'Timestamp' in sisters:
            return pd.to_datetime(master[parent]['Timestamp'][:])
        
        #gotta decode time columns to be processed correctly on backend after being stored in dcc.Store
        elif 'Time (Seconds)' in sisters or 'Time' in sisters:
            key = 'Time' if 'Time' in sisters else 'Time (Seconds)'
            col = master[parent][key][:]

            raw = col.values if hasattr(col, 'values') else col[:]
            raw = np.array(raw)

            if isinstance(raw[0], bytes):
                decoded = [universal_decode(v) for v in raw]
                raw = np.array(decoded)

            try:
                return pd.to_timedelta(raw)
            except ValueError:
                #handle weird time format mm:ss.fs
                time_col = parse_fractional_time(raw)
                sorted_idx = time_col.argsort()
                time_col = time_col.iloc[sorted_idx]
                return pd.to_timedelta(time_col)
        
        print(f'Time column not found in same location as data. {path}: {sisters}. Returning None')
        return None

def find_xyz(path, master_file):
    with h5tbx.File(master_file, 'r') as master:
        node = master[path]
        if isinstance(node, h5py.Dataset):
            parent = master[os.path.dirname(path)]
            if isinstance(parent, h5py.Group):
                sisters = list(parent.keys())
            else: 
                print('hell fuckin nah bro')
                return None, None, None
            if 'XPos' in sisters and 'YPos' in sisters and 'ZPos' in sisters:
                xpos = parent['XPos'][:]
                ypos = parent['YPos'][:]
                zpos = parent['ZPos'][:]
                return xpos, ypos, zpos
            else:
                return deeper_xyz_search(master, path)

        else: #should be group
            sisters = list(node.keys())
            if 'XPos' in sisters and 'YPos' in sisters and 'ZPos' in sisters:
                xpos = node['XPos'][:]
                ypos = node['YPos'][:]
                zpos = node['ZPos'][:]
                return xpos, ypos, zpos
            else:
                return deeper_xyz_search(master, path)
            
#go to build level and find machine_data, then go inside and look for xpos, ypos, zpos
#"master" must be an opened file object 
def deeper_xyz_search(master, ds_path): 
    build_path = get_build_path(ds_path)
    build_file = master[build_path]
    if 'machine_data' in list(build_file.keys()):
        node = build_file['machine_data']
        datasets = list(node.keys())

        if 'XPos' in datasets and 'YPos' in datasets and 'ZPos' in datasets:
            xpos = node['XPos'][:]
            ypos = node['YPos'][:]
            zpos = node['ZPos'][:]
            return xpos, ypos, zpos
        else:
            print(f'[Exception] XPos, YPos or ZPos not found at {build_path}/machine_data')
            return None, None, None
    else:
        print(f'"machine_data" not found at {build_path}') 
        return None, None, None       
    
def get_build_path(path):
    parts = path.strip('/').split('/')
    if 'builds' in parts:
        idx = parts.index('builds')
        return '/' + '/'.join(parts[:idx+2])
    return path

def normalize_times(stack):
    raw_times = [find_time_column(path, MASTER_FILE) for path in stack]
    return [(t - t.iloc[0]) if hasattr(t, 'iloc') else (t - t[0]) for t in raw_times]

def parse_fractional_time(series):
    def convert(x):
        try:
            minutes, sec_frac = str(x).split(':')
            seconds = float(sec_frac)
            total_seconds = int(minutes) * 60 + seconds
            return pd.Timedelta(seconds = total_seconds)
        except Exception:
            return pd.Timedelta(0)
    return pd.Series(series).apply(convert)

#not really a plot tool but putting it here to avoid circular imports
def universal_decode(blob, fallback_encodings=['utf-8', 'latin1', 'windows-1252']):
    if isinstance(blob, bytes):
        for enc in fallback_encodings:
            try:
                return blob.decode(enc)  #text
            except Exception:
                continue
        return blob  #fallback: return raw bytes if decode fails
    
    elif isinstance(blob, io.BytesIO):
        try:
            blob.seek(0)
            return blob.read().decode('utf-8')
        except Exception:
            blob.seek(0)
            return blob.read()  #raw bytes

    elif isinstance(blob, str):
        return blob

    elif isinstance(blob, (np.ndarray, list)):
        return str(blob)

    else:
        raise TypeError(f"Can't decode object of type {type(blob)}")