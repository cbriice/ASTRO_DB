import numpy as np, pandas as pd
import base64, h5py, io, json, os, time
import h5rdmtoolbox as h5tbx
import plotly.graph_objects as go
from dash import html, dash_table
import utils.plot_tools as pt
import xarray as xr
from utils.lock import master_lock
from utils.constants import EXPORT_DIR

def returnMetric(ips_file)->pd.DataFrame:
        met_df = ips_file

        met_df['FeedTrq'] = met_df['FeedTrq'] *4.448 #lbs -> Newtons, remember this is actually force

        met_df['SpinTrq'] = met_df['SpinTrq'] * 1.355 #ft-lbs to N*M
        met_df['XTrq'] = met_df['XTrq'] * 1.355 #ft-lbs to N*M
        met_df['YTrq'] = met_df['YTrq'] * 1.355 #ft-lbs to N*M
        met_df['ZTrq'] = met_df['ZTrq'] * 1.355 #ft-lbs to N*M

        met_df['FeedVel'] = met_df['FeedVel'] * 0.4233 #ipm to mm/s
        met_df['PathVel'] = met_df['PathVel'] * 0.4233 #ipm to mm/s
        met_df['XVel'] = met_df['XVel'] * 0.4233 #ipm to mm/s
        met_df['YVel'] = met_df['YVel'] * 0.4233 #ipm to mm/s
        met_df['ZVel'] = met_df['ZVel'] * 0.4233 #ipm to mm/s

        met_df['XPos'] = met_df['XPos'] * 25.4 #in to mm
        met_df['YPos'] = met_df['YPos'] * 25.4 #in to mm
        met_df['ZPos'] = met_df['ZPos'] * 25.4 #in to mm
        met_df['FeedPos'] = met_df['FeedPos'] *25.4 #in to mm
        return met_df

def scrub_file(file):
    confirm = input(f'WARNING: Calling this function will erase all data in {file}. Input "y" to continue: ')
    if confirm.lower() == 'y':
        with master_lock:
            with h5tbx.File(file, 'a') as f:
                for key in list(f.keys()):
                    del f[key]
                print(f'All top level groups in {file} have been deleted.')
    else:
        print("Scrub canceled.")
    
def find_header_line(filepath):
    for i, line in enumerate(filepath.getvalue().splitlines()):
        if line.startswith("S.No.") or line.startswith("Frame") or "Date" in line or "(Seconds)" in line:
            return i
    return 0

#sample adjustment function to match sample rates of data
def adjust_sample_rate(input_csv, target_hz):
    f = pd.read_csv(input_csv)

    target_sample = 1 / target_hz
    f['Time'] = pd.to_timedelta('00' + f['Time'].astype(str))
    f.set_index('Time', inplace=True)
    f_resample = f.resample(f'{int(1000 * target_sample)}ms').asfreq()

    continuous_cols = ['SpinVel', 'SpinTrq', 'SpinPwr', 
                   'FeedVel', 'FeedPos', 'FeedTrq', 
                   'PathVel', 'XPos', 'XVel', 'XTrq',
                   'YPos', 'YVel', 'YTrq', 'ZVel', 'ZTrq',
                   'Ktype1', 'Ktype2', 'Ktype3', 'Ktype4',
                   'ToolTemp', 'Zscale']
    f_resample[continuous_cols] = f_resample[continuous_cols].interpolate(method='linear')
    discrete_cols = ['FRO', 'ZPos', 'Gcode', 'Low', 'High']
    f_resample[discrete_cols] = f_resample[discrete_cols].ffill()

    return f_resample

#gets all attributes and returns list of strings for each k: v pair
def get_atts_list(build_file):
    with h5tbx.File(build_file, 'r') as build:
        return [f'{key}: {value}' for key, value in build.attrs.items()]
    
#decode 'bdata' from json-serialized plot stored in dcc.Store memory. for color axis adjustment on 3d plots
def decode_color_att(data):
    fig = go.Figure(data)

    for trace in fig.data:
        if hasattr(trace, 'marker') and isinstance(trace.marker.color, dict):
            color_dict = trace.marker.color
            if 'bdata' in color_dict and 'dtype' in color_dict:
                b64 = color_dict['bdata']
                dtype = np.dtype(color_dict['dtype'])
                decoded = np.frombuffer(base64.b64decode(b64), dtype = dtype)
                trace.marker.color = decoded
    return fig

def intersection(list1, list2):
    result = []
    for i in list1:
        if i in list2: 
            result.append(i)
    return result

def show_image(image_bytes, mime = 'image/png'):
    image_bytes.seek(0)
    encoded = base64.b64encode(image_bytes.read()).decode('ascii')
    return html.Img(src = f'data:{mime};base64,{encoded}', style = {'width': '100%', 'height': 'auto', 'width': 'auto'})

def text_preview(text, path, max_length: int = 1000):
    return html.Div([
                html.H6(f'First {max_length} characters of file at {path}:'), 
                html.Pre(text[:max_length])
                ], style = {'white-space': 'pre-wrap'}
            )

def create_table(data):
    return html.Div([
        html.H6('Time series table of data:'),
        dash_table.DataTable(
            data = data.to_dict('records'),
            columns = [{'name': col, 'id': col} for col in data.columns],
            style_table = {'width': '300px', 'maxHeight': '800px', 'overflowY': 'scroll'},
            page_size = 50
        )
    ])

def process_data_for_preview(path, master_file):
    with h5tbx.File(master_file, 'r') as master:
        if path in master:
            node = master[path]
            if isinstance(node, h5py.Dataset):
                #grab data as scalar dataset and fallback to slicing if its not scalar
                try:
                    data = node[()]
                except ValueError as e:
                    if "scalar" in str(e).lower():
                        raise
                    else:
                        data = node[:]
                    
                #data is stored as xarray if image (i think always??) so handle that by turning it back into io.BytesIO type like it says its saved as and then process accordingly
                if isinstance(data, xr.DataArray):
                    if data.shape == () and isinstance(data.item(), bytes):
                        data = io.BytesIO(data.item())  
                    else:
                        data = data.values  

                if isinstance(data, io.BytesIO):
                    try:
                        return show_image(data), False
                    except:
                        try:
                            text = data.read().decode()
                            return text_preview(text, path), False
                        except Exception as e:
                            print(f'bytes could not be decoded as image or text: {e}')
                            return '', False
                
                elif isinstance(data, (np.ndarray, list)) and data.ndim == 1:
                    time_col = pt.find_time_column(path, master_file)
                    base_time = pd.Timestamp('00:00:00')
                    if time_col is not None:
                        time_col = base_time + pd.to_timedelta(time_col) 
                        time_col = pd.Series(time_col).dt.strftime('%H:%M:%S') 
                        df = pd.DataFrame({
                            'Time': time_col,
                            'Value': data
                        })
                        return create_table(df), True
                    else:
                        return '', False

                elif isinstance(data, str):
                    try:
                        parsed = json.loads(data)

                        if isinstance(parsed, dict):
                            df = pd.DataFrame([parsed])
                        elif isinstance(parsed, list) and all(isinstance(row, dict) for row in parsed):
                            df = pd.DataFrame(parsed)
                        else:
                            return html.Span(f'JSON parsed but format not displayable as a table.\n\n{parsed}'), False
                        
                        return dash_table.DataTable(
                            data = df.to_dict('records'),
                            columns = [{'name': c, 'id': c} for c in df.columns],
                            style_table = {'maxHeight': '500px', 'overflowY': 'auto', 'width': '1300px', 'overflowX': 'auto'},
                            page_size = 10
                        ), False
                    
                    except json.JSONDecodeError as e:
                        return html.Span(f'Failed to parse JSON: {e}'), False

                else:
                    return html.Span(f'Unsupported data type for preview: {type(data)}', style = {'color': 'red'}), False
        else:
            print(f'somehow the path passed isnt in master file. {path}')
            return None, False

def percent_diff(num1, num2):
    if isinstance(num1, (int, float)) and isinstance(num2, (int, float)):
        if (num1 == 0 and num2 != 0) or (num2 == 0 and num1 != 0):
            diff = 100
        elif num1 == num2 == 0:
            diff = 0
        else: 
            diff = ((num2 - num1) / num1) * 100
        return round(diff, 1)
    
    else:
        if num1 == num2:
            return 'Same'
        else:
            return 'Different'
    
def magnitude(vec):
    if isinstance(vec[0], tuple):
        vals = [v for _, v in vec if isinstance(v, (int, float))]
        mag = np.sqrt(sum(v * v for v in vals) / len(vals))
        return round(mag, 1)
    else:
        mag = np.sqrt(sum(vec[i] * vec[i] for i in vec))
        return round(mag, 1)

def find_index(df: pd.DataFrame, target):
    if isinstance(target, list):            #idt this case ever gets called ngl
        for i, row in df.iterrows():
            row_arr = row.values
            for tar in target:
                if tar in row_arr:
                    return i, np.where(row_arr == tar)[0][0]
    else:
        for i, row in df.iterrows():
            row_arr = row.values
            cleaned_arr = [str(val).strip().lower() for val in row_arr]
            cleaned_target = str(target).strip().lower()
            if cleaned_target in cleaned_arr:
                return i, cleaned_arr.index(cleaned_target)
            
def find_adjacent(df: pd.DataFrame, target: str):
    for _, row in df.iterrows():
        for i, val in enumerate(row):
            if pd.isna(val):
                continue
            if str(val).strip().lower() == str(target).strip().lower():
                if i + 1 < len(row):
                    return row.iloc[i + 1]
    print(f'{target} not found in any row of dataframe')
    return None

def clean_temp_exports(folder, max_age_minutes):
    now = time.time()
    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            if now - os.path.getmtime(fpath) > max_age_minutes * 60:
                os.remove(fpath)