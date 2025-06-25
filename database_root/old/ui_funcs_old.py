import database_funcs as dbf
from pywebio.input import input, textarea, file_upload, select, input_group
from pywebio.output import put_text, put_buttons, put_table, put_button, clear, use_scope, put_image, put_html
from pywebio import start_server
import io, sys
import h5rdmtoolbox as h5tbx
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import numpy as np
import h5py
import plotly.graph_objs as go
from helpers import find_header_line

MASTER_FILE = 'master2.h5'
dbf.create_master_file(MASTER_FILE, {'machine': 'meld piece of shit'})

PROGRAM_OPTIONS = ['Browse directories', 
                   'Find build', 
                   'Filter by attribute', 
                   'Search specific attributes', 
                   'Upload .csv file', 
                   'Show data structure', 
                   'Edit build data']

def main_menu():
    clear(scope=None)
    with use_scope('main', clear = True):
        put_text("What would you like to do?")
        put_buttons(
            PROGRAM_OPTIONS,
            onclick = [
                lambda: browse_directory(MASTER_FILE),
                lambda: run_find_build(MASTER_FILE),
                lambda: filter_by_attribute(MASTER_FILE),
                lambda: search_attribute(MASTER_FILE),
                lambda: take_csv_upload(MASTER_FILE),
                lambda: show_hierarchy(MASTER_FILE),
                lambda: delete_build_data(MASTER_FILE)
            ]
        )

def run_find_build(master_file):
    with use_scope('main', clear=True):
        build_id = input("Enter build ID:")
        sought_build = find_build(build_id, master_file)
        if not sought_build:
            put_text('Exception: Build not found.')
            put_button('Back to main menu', onclick = lambda: main_menu())
        else:
            with h5tbx.File(master_file, 'r') as master:
                #build = master[sought_build]
                put_text(f'Data within build {sought_build}:')
                build_menu_ops(build_id, master_file)

#every build has attribute of id. search for this attribute and return path to build
def find_build(build_id: str, master_file):
    print(f'Searching for build {build_id}...')
    with h5tbx.File(master_file, 'r') as master:
        try:
            res = master.find(flt = {'id': f'{build_id}'})
            if not res:
                print('Search yielded no results.')
                return None
            print(f'{build_id} successfully located.')
            return res[0].name   #.find() method returns a list, but list should never be longer than 1 item (every build has unique id) so just index [0] hardcode
        except KeyError:
            return None

#user can click through directory and see groups for each level
def browse_directory(master_file):
    clear(scope=None)
    with use_scope('main', clear=True):
        with h5tbx.File(master_file, 'r') as master:
            input1 = input_group('Select Directories', 
                        [select('Select a directory:', 
                            options = list(master.keys()), 
                            name = 'choice1')]
                    )                                   #used this weird input_group syntax to try and fix a bug and it didnt even work but cba to change it back
            choice1 = input1['choice1']
            input2 = input_group(f'pick one mfer:', 
                        [select(f'Select from {choice1}', 
                            options = list(master[f'/{choice1}'].keys()), 
                            name = 'choice2')]
                    )       
            choice2 = input2['choice2']
            build_menu_ops(choice2, master_file)

#should show machine_data, sensor_data, etc
def build_menu_ops(build: str, master_file):
    with use_scope('main', clear=True):
        with h5tbx.File(master_file, 'r') as master:
            put_buttons(
                list(master[f'/builds/{build}'].keys()),
                onclick = lambda sub1: use_scope('main', clear=True)(lambda: dynamic_bmbs1(sub1, build, master_file))()
                )
        put_button(f'Back to directory', onclick = lambda: browse_directory(master_file))
        back_to_menu()

#shows list of columns within machine_data, sensor_data, etc
def dynamic_bmbs1(sub1, build, master_file):
    with use_scope('main', clear=True):
        with h5tbx.File(master_file, 'r') as master:
            put_buttons(
                list(master[f'/builds/{build}/{sub1}'].keys()),
                onclick = lambda y: use_scope('main', clear=True)(lambda: dynamic_bmbs2(y, sub1, build, master_file))()
            )
        put_button(f'Back to {build}', onclick = lambda: build_menu_ops(build, master_file))

#called when one of the buttons from bmbs1() is pressed to plot selected data
def dynamic_bmbs2(y, sub1, build, master_file):
    with use_scope('main', clear=True):
        with h5tbx.File(master_file, 'r') as master:
            node = master[f'/builds/{build}/{sub1}/{y}']

            if y in ["Date", "Time", "Timestamp", "Date&Time"]:
                put_text("cant plot time vs time bozo")

            elif isinstance(node, h5py.Dataset):
                '''try:
                    data = node[:]
                    #data = data.astype(float)
                    plot_data(data, build, sub1, y, master_file)
                except Exception as e:
                    put_text(f'Error processing dataset {y}: {e}')
                    '''
                data = node[:]
                plot_data(data, build, sub1, y, master_file)
            
            elif isinstance(node, h5py.Group):
                put_text(f'{y} is a group. Choose a sub-dataset:')
                put_buttons(
                    list(node.keys()),
                    onclick = lambda suby: dynamic_bmbs2(f'{y}/{suby}', sub1, build, master_file)
                )
            
            else:
                put_text(f'Unrecognized node type at {y}')
            
        put_button(f'Back to {sub1}', onclick = lambda: dynamic_bmbs1(sub1, build, master_file))

def take_csv_upload(master_file):
    with use_scope('main', clear=True):
        uploaded_csv = file_upload("Input .csv file:", accept='.csv') 
        decoded_csv = uploaded_csv['content'].decode('utf-8', errors='replace')
        csv_io = io.StringIO(decoded_csv)
        
        #find where data starts in csv
        header_row = find_header_line(csv_io)
        csv_io.seek(0)

        userfile = pd.read_csv(csv_io, skiprows = header_row)
        build_id = input("Enter build ID:")
        meta = {}

        choice2 = select("Machine file, sensor file or sample file?", options = ['Machine', 'Sensor', 'Sample'])
        if choice2 == 'Machine':
            build_file = dbf.create_machine_hdf5(userfile, build_id)
            dbf.merge_build_to_master(master_file, build_id, build_file, meta)
            put_text(f'File {build_file} merged to master file.')
            back_to_menu()

        elif choice2 == 'Sensor':
            sensor_type = input("Enter type of sensor (e.g. force, pyrometer, etc.):")
            sensor_dict = add_attributes()
            sensor_file = dbf.create_sensor_hdf5(sensor_type, userfile, sensor_dict)
            dbf.merge_data_to_build(sensor_file, master_file, sensor_type, build_id)
            put_text(f'Sensor data {sensor_type} merged to build {build_id} in master file.')
            back_to_menu()

        elif choice2 == 'Sample':
            sample_dict = add_attributes()
            sample_file = dbf.sample_upload(userfile, master_file, build_id, sample_dict)
            dbf.merge_data_to_build(sample_file, master_file, 'sample', build_id)
            put_text(f'Sample data merged to build {build_id} in master file.')
            back_to_menu()

def add_attributes():
    with use_scope('main', clear=True):
        meta = {}
        while True:
            key = input("Enter metadata key (or 'done' to finish):")
            if key.lower() == 'done':
                break
            value = input(f"Enter value for {key}:")
            meta[key] = value
        return meta

def plot_data(data, build, sub1, data_name, master_file):
    with use_scope('main', clear=True):
        put_text(f'Data for {data_name}')
        with h5tbx.File(master_file, 'r') as master:
            if f'/builds/{build}/{sub1}/Time' in master:
                time_raw = master[f'/builds/{build}/{sub1}/Time'][:]
            elif f'/builds/{build}/{sub1}/Timestamp' in master:
                time_raw = master[f'/builds/{build}/{sub1}/Timestamp'][:]
            elif f'/builds/{build}/{sub1}/Time (Seconds)' in master:
                time_raw = master[f'/builds/{build}/{sub1}/Time (Seconds)'][:]
            else: 
                raise ValueError(f'Time column in {master}/builds/{build}/{sub1} not formatted correctly.')
            
        if hasattr(data, 'values'):
            data = data.values
        if hasattr(time_raw, 'values'):
            time_raw = time_raw.values

        #egregiously complicated local function to robustly handle many time formats in the csvs
        def to_seconds(t):
            if isinstance(t, (int, float)):
                return float(t)
            if isinstance(t, bytes):
                t = t.decode('utf-8')
            if isinstance(t, str):
                #handle time format: 'x days h:m:s'
                if 'days' in t:
                    try:
                        parts = t.split()
                        days = int(parts[0])
                        time_part = parts[-1]
                        if ':' in time_part:
                            h, m, s = time_part.split(':')
                            h = int(h)
                            m = int(m)
                            s = float(s)
                        else:
                            h = int(parts[-1])
                            m = s = 0
                        return days * 86400 + h * 3600 + m * 60 + s
                    except Exception:
                        raise ValueError(f'Invalid time format: {t}')
                #handle other time formats 'h:m:s'
                elif ':' in t:
                    parts = list(map(float, t.split(':')))
                    if len(parts) == 2:
                        return parts[0] * 60 + parts[1]
                    elif len(parts) == 3:
                        return parts[0] * 3600 + parts[1] * 60 + parts[2]     
            raise ValueError(f'Invalid time format: {t}')
            
        time_seconds = np.array([
            to_seconds(t) for t in time_raw
            ])
        if len(time_seconds) != len(data):
            put_text('data length doesnt match')
            back_to_menu()
            return
        
        #sort to make sure data is sequential
        sorted_idx = np.argsort(time_seconds)
        time_seconds = time_seconds[sorted_idx]
        data = data[sorted_idx]

        #make data float to plot
        try:
            data = data.astype(float)
        except Exception as e:
            put_text(f"Error converting data to float: {e}")
            put_text(f"Sample values: {data[:5]}")
            return
        
        if data.ndim > 1:
            data = data.squeeze()
        if data is None:
            put_text('No data to plot.')
            back_to_menu()
            return
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x = time_seconds,
            y = data,
            mode = 'lines'
        ))

        fig.update_layout(
            title = f'Data for {data_name}',
            xaxis_title = 'Time (s)',
            yaxis_title = data_name,
            width = 900,
            height = 550
        )

        put_html(fig.to_html(include_plotlyjs = 'cdn'))
            
        
def show_hierarchy(master_file):
    with use_scope('main', clear=True):
        with h5tbx.File(master_file, 'r') as master:
            put_text(list(master.keys()))
            build_list = list(master['/builds'].keys())
            put_text(build_list)
            put_text('\n')
            for build in build_list:
                put_text(build)
                put_text(list(master[f'/builds/{build}'].keys()))
        back_to_menu()

def print_results(result):
    with use_scope('main', clear=True):
        if not result:
            put_text('No results found.')
        else:
            for res in result:
                put_text(res.name)
        back_to_menu()

def explore_results(result, master_file):
    with use_scope('main', clear = True):
        choice = select(
            f'List of item locations which match search query (select to view):',
            options = [res.name for res in result]
        )

        with h5tbx.File(master_file, 'r') as master:
            if '/builds' in choice:
                build_id = choice.split('/')[2]
                build_menu_ops(build_id, master_file)
            else:
                thing = dbf.gather_info_from_att_search(choice)
                for item in thing:
                    put_text(item)
                back_to_menu()

#lets user search for all items in the database which have some attribute
def filter_by_attribute(master_file):
    with use_scope('main', clear = True):
        att = input("Input attribute to search for:")
        result = dbf.search_attribute(master_file, att)
        whatdo = ['show results', 'explore results']

        if not result:
            put_text("Query returned no results.")
            back_to_menu()
        else: 
            put_buttons(
                whatdo,
                onclick = [
                    lambda: print_results(result),
                    lambda: explore_results(result, master_file)
                ]
            )

def search_attribute(master_file):
    target = add_attributes()
    if not target:
        with use_scope('main', clear=True):
            put_text("I said enter metadata dumbass")
            back_to_menu()
        return
    
    result = dbf.filter_attributes(master_file, target) 

    if not result:
            put_text("Query returned no results.")
            back_to_menu()
    else: 
        whatdo = ['show results', 'explore results']
        with use_scope('main', clear=True):
            put_buttons(
                    whatdo,
                    onclick = [
                        lambda: print_results(result),
                        lambda: explore_results(result, master_file)
                    ]
                )

def delete_build_data(master_file):
    with use_scope('main', clear=True):
        with h5tbx.File(master_file, 'a') as master:
            
            build = input("Input build file to be edited:")
            path = f'/builds/{build}'
            
            if path not in master:
                put_text(f'Build {build} not found.')
                back_to_menu()
                return
            else:
                contents = list(master[path].keys())
                choice = input("Delete whole build file? y/n")

                if choice.lower() == 'y':
                    del master[path]
                    put_text(f'File {path} deleted from master file.')
                    back_to_menu()
                elif choice.lower() == 'n':
                    choice2 = select("Select data to delete:", options = contents)
                    if choice2:
                        del master[path][choice2]
                        put_text(f'File {choice2} deleted from {path}.')
                        back_to_menu()
                    else:
                        put_text("no selection made (idk why you did that)")
                        back_to_menu()
            

def back_to_menu():
    put_button(f'Back to main menu', onclick = lambda: main_menu())