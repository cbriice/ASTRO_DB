import os, io, base64, pandas as pd
from dash import dcc, html, Input, Output, State, ctx
from utils.helpers import ntng, process_upload, auto_assign_atts
from backend_deep import add_data, add_attrs, process_exsitu, add_exsitu
import layouts_uploaddata as lud
from layouts import add_machine_atts
from utils.tools import find_header_line
import backend_top as bt
from utils.constants import AA_ALLOY_OPS, MASTER_FILE
import h5rdmtoolbox as h5tbx

def register_upload_callbacks(app):
    @app.callback(
        Output('upload-builddata-info', 'children'),
        Input('ex-bd-button', 'n_clicks'),
        State('data-type', 'value')
    )
    def send_to_right_page(n, data_type):
        if n == 0:
            return ''
        else:
            if data_type == 'build':
                return lud.builddata_upload_layout()
            elif data_type == 'exsitu':
                return lud.exsitu_upload_layout()
            else:
                return lud.exsitu_csv_1()
        
    #------------------------------------------------- above handles choice of data, below is where shit is uploaded
    #for builds not exsitu
    @app.callback(
        [Output('upload-output', 'children'),
         Output('parent-path-1', 'data'),
         Output('name-upload-1', 'data'),
         Output('active-upload-source', 'data', allow_duplicate = True)],
        Input('submit-data-button', 'n_clicks'),
        State('parent-path-input', 'value'),
        State('input-name', 'value'),
        prevent_initial_call = True
    )
    def handle_data_submission(n, parent_path, name):
        if n == 0:
            return "", ntng(), ntng(), ntng()
        else:
            if not parent_path or not name:
                return html.Span("Error: Parent path and name are required.", style={'color': 'red'}), ntng(), ntng(), ntng()
            else:
                if not any(a in parent_path for a in AA_ALLOY_OPS):
                    return html.Span(f'Invalid path {parent_path}', style = {'color': 'red'}), ntng(), ntng(), ntng()
                if 'builds' not in parent_path or ' ' in parent_path:
                    return html.Span(f'Invalid path {parent_path}', style = {'color': 'red'}), ntng(), ntng(), ntng()
                if ' ' in name:
                    return html.Span(f'Invalid name {name}', style = {'color': 'red'}), ntng(), ntng(), ntng()
                
                return lud.upload_file_section(1), parent_path, name, 'build'
            
    #-------------------- build data upload ---------------------
    from cleaners.isd_df_cleaner import vectorized_isd_df_clean
    from cleaners.md_df_cleaner import vectorized_md_df_clean
    from cleaners.mcd_df_cleaner import gpt_clean
    from utils.helpers import process_temp

    @app.callback(
        [Output('upload-status-1', 'children'),
         Output('attribute-adder-1', 'children'),
         Output('uploaded-filepath-1', 'data')],
        [Input('submit-upload-1', 'n_clicks'),
         Input('upload-data-1', 'isCompleted')], ##
        State('upload-data-1', 'fileNames'),     ##
        State('parent-path-1', 'data'),
        State('name-upload-1', 'data'),
        State('cleaned-or-not', 'value'),
        State('sample-rate', 'value'),
        State('upload-data-1', 'upload_id')     ##
    )
    def whoevenreadsthese(n, is_complete, filename, parent_path, name, cleaned_or_not, sample_rate, upload_id):
        if n == 0 and not is_complete:
            return '', '', ntng()
        elif n == 0 and is_complete:
            return html.Span(f'Received {filename}', style = {'color': 'green'}), '', ntng()
        elif n > 0 and not is_complete:
            return html.Span('No file uploaded', style = {'color': 'red'}), '', ntng()
        
        if is_complete:
            if filename and isinstance(filename, list):
                if len(filename) > 0:
                    filename = filename[0]
            else:
                return html.Span('Error receiving file: no filename found', style={'color': 'red'}), '', ntng()
            
            print(f'[Dash] Upload {filename} [{upload_id}] received, beginning processing')
            full_path = os.path.join(UPLOAD_FOLDER_ROOT, upload_id, filename)
            data = process_temp(full_path)
            os.remove(full_path)
            print(f'[Dash] {full_path} extracted, processed as {type(data)} and flushed')

            auto_adjusted = False
            build_file = True
            low_quality_interpolation = False

            #if user selects clean, need to make sure it's a csv and then find out what kind of csv to run which kind of cleaner function
            if cleaned_or_not == 'need-clean':
                if isinstance(data, pd.DataFrame): #process_temp output a dataframe so now we can proceed with cleaning

                    if sample_rate:
                        if sample_rate > 20:
                            return html.Span('Specified sample rate is too high (should be <=20)', style = {'color': 'red'}), '', ntng()
                        if isinstance(sample_rate, float):
                            sample_rate = int(sample_rate)
                        
                        #sample rate stored as attribute on build. sample rate should be constant for all files associated with one build. handles this automatically
                        try:
                            print(f'Looking for sample rate attribute in {parent_path} to match...')
                            with h5tbx.File(MASTER_FILE, 'r') as master:
                                build_node = master[parent_path]
                                sample_att = build_node.attrs['sample_rate']
                                if sample_rate != sample_att:
                                    sample_rate = sample_att
                                    auto_adjusted = True
                        except Exception as e:
                            print(f'Sample rate attribute not found at {parent_path}, or there was an error. Continuing with data upload. {e}')

                        #check whether isd or mcd
                        if 'Force_1_Force (lbs.)' in data.columns:
                            build_file = True
                            data = vectorized_isd_df_clean(data, sample_rate)
                            print(f'In-situ data cleaned and reprocessed at {sample_rate} Hz')

                        else:
                            #idk how to safely check for mcd since the column headers are so nondescriptive so im taking the easy way out
                            try:
                                data, low_quality_interpolation = gpt_clean(data, sample_rate)
                                build_file = True
                                print(f'Motion capture data cleaned and reprocessed at {sample_rate} Hz')
                            except Exception as e:
                                build_file = False
                                print(f"You can (probably) ignore this but I'm logging it: {e}")
                                pass    #if this throws an error, its probably just a random csv and shouldnt go through a dedicated process func
                
                    else:
                        return html.Span('Can\'t clean data without specified sample rate', style = {'color': 'red'}), '', ntng()
                else:
                    print("Can't clean non-csv data. Continuing with normal data upload")
            
            try:
                success = add_data(data, MASTER_FILE, parent_path, name, False, build_file)
                if success:

                    if low_quality_interpolation:
                        from utils.lock import master_lock
                        with master_lock:
                            with h5tbx.File(MASTER_FILE, 'a') as master:
                                master[f'{parent_path}/{name}'].attrs['notice'] = 'Low quality interpolation (<= 5hz?)' 
                        
                    if auto_adjusted:
                        return html.Span(f'Data {name} added to {parent_path} in {MASTER_FILE}. Sample rate auto-adjusted to match build sample rate', style={'color': 'green'}), lud.attribute_layout1(), f'{parent_path}/{name}'
                    else:
                        return html.Span(f'Data {name} added to {parent_path} in {MASTER_FILE}.', style={'color': 'green'}), lud.attribute_layout1(), f'{parent_path}/{name}'
                else:
                    return html.Span(f'Failed to add {name} to {parent_path}. Make sure there are no naming conflicts (program will return this message instead of overwriting)', style={'color': 'red'}), '', ntng()
            except Exception as e:
                return html.Span(f'upload attempt shit the bed somehow. {e}', style={'color': 'red'}), '', ntng()
            
    #------------------------------------------------ exsitu below
    @app.callback(
        Output('exsitu-upload', 'children'),
        Input('confirm-coord-bool', 'n_clicks'),
        State('exsitu-coord-bool', 'value')
    )
    def send_to_exsitu_page(n, coords):
        if n == 0:
            return ''
        else:
            if coords == 'yes':
                return lud.exsitu_coordupload_layout()
            else:
                return lud.exsitu_other()
            
    @app.callback( #coords case
        [Output('exsitu-coord-page2', 'children'),
         Output('parent-path-2', 'data'),
         Output('name-upload-2', 'data'),
         Output('generated-address-display', 'children'),
         Output('active-upload-source', 'data', allow_duplicate = True)],
        Input('confirm-coords', 'n_clicks'),
        State('exsitu-alloy-dropdown', 'value'),
        State('x-coord-dropdown', 'value'),
        State('y-coord-dropdown', 'value'),
        State('z-coord-dropdown', 'value'),
        State('datatype-exsitu-coord', 'value'),
        State('name-exsitu-coord', 'value'),
        prevent_initial_call = True
    )
    def a(n, alloy, xcoord, ycoord, zcoord, dt, name):
        if n == 0:
            return ntng(), ntng(), ntng(), ntng(), ntng()
        else:
            address = f'/{alloy}/exsitu/{xcoord}{ycoord}{zcoord}/{dt}'
            return lud.upload_file_section(2), address, name, html.Span(f'Generated address {address}. Name: {name}', style = {'color': 'green'}), 'exsitu-coord'

    @app.callback(
        [Output('upload-status-2', 'children'),
         Output('attribute-adder-2', 'children'),
         Output('uploaded-filepath-2', 'data')],
        [Input('submit-upload-2', 'n_clicks'),
         Input('upload-data-2', 'contents')],
        State('upload-data-2', 'filename'),
        State('parent-path-2', 'data'),
        State('name-upload-2', 'data')
    )
    def exsitu_callback(n, contents, filename, parent_path, name):
        if n == 0 and not contents:
            return '', '', ntng()
        elif n == 0 and contents:
            return html.Span(f'Received {filename}', style = {'color': 'green'}), '', ntng()
        elif n > 0 and not contents:
            return html.Span('No file uploaded', style = {'color': 'red'}), '', ntng()
        
        else:
            data = process_upload(contents, None)

            try:
                success = add_data(data, MASTER_FILE, parent_path, name, False, False)
                if success:
                    return html.Span(f'Data {name} added to {parent_path} in {MASTER_FILE}', style={'color': 'green'}), lud.attribute_layout1(), f'{parent_path}/{name}'
                else:
                    return html.Span(f'Failed to add {name} to {parent_path}. Check console for what happened', style={'color': 'red'}), '', ntng()
            except Exception as e:
                return html.Span(f'upload attempt shit the bed somehow. {e}', style={'color': 'red'}), '', ntng()
            
    @app.callback(
        [Output('exsitu-attribute-adder', 'children'),
         Output('other-gen-status', 'children'),
         Output('parent-path-3', 'data'),
         Output('name-upload-3', 'data'),
         Output('active-upload-source', 'data', allow_duplicate = True)],
        Input('submit-exsitu-data', 'n_clicks'),
        State('alloy-other-exs', 'value'),
        State('exsitu-name', 'value'),
        State('datatype-exsitu-other', 'value'),
        prevent_initial_call = True
    )
    def hm(n, alloy, name, dt):
        if n == 0:
            return ntng(), ntng(), ntng(), ntng(), ntng()
        else:
            address = f'/{alloy}/exsitu/{dt}'
            return lud.upload_file_section(3), html.Span(f'Generated address {address}. Name: {name}', style = {'color': 'green'}), address, name, 'exsitu-noncoord'

    @app.callback(
        [Output('upload-status-3', 'children'),
         Output('attribute-adder-3', 'children'),
         Output('uploaded-filepath-3', 'data')],
        [Input('submit-upload-3', 'n_clicks'),
         Input('upload-data-3', 'contents')],
        State('upload-data-3', 'filename'),
        State('parent-path-3', 'data'),
        State('name-upload-3', 'data')
    )
    def nah(n, contents, filename, parent_path, name):
        return exsitu_callback(n, contents, filename, parent_path, name) #same process as for coords case after data is taken in
    
    #---------------exsitu auto-processed csv ---------------
    @app.callback(
        Output('upload-status-37', 'children'),
        [Input('submit-upload-37', 'n_clicks'),
         Input('upload-data-37', 'contents')],
        State('upload-data-37', 'filename')
    )
    def exsitu_auto(n, contents, filename):
        if n == 0 and not contents:
            return ''
        elif n == 0 and contents:
            return html.Span(f'Received {filename}', style = {'color': 'green'})
        elif n > 0 and not contents:
            return html.Span('No file uploaded', style = {'color': 'red'})
        
        else:
            data = process_upload(contents, None)
            df_list, atts = process_exsitu(data)
            success = add_exsitu(df_list, atts, MASTER_FILE)

            if success:
                return html.Span(
                    f'{filename} automatically processed and saved under "ex-situ" top-level group according to build id and temper.', 
                    style = {'color': 'green'}
                )
            else:
                return html.Span(
                    'One or more datasets threw an error. Check console for specific log - some datasets may still have been processed successfully.',
                    style = {'color': 'red'}
                )

    #--------------------------------------------
    #-------------------------------------------- atts
    @app.callback(
        Output('att-assignor', 'children'),
        Input('confirm-att-method', 'n_clicks'),
        State('how-add-atts', 'value'),
        State('parent-path-1', 'data'),
        State('name-upload-1', 'data'),
        State('parent-path-2', 'data'),
        State('name-upload-2', 'data'),
        State('parent-path-3', 'data'),
        State('name-upload-3', 'data'),
        State('active-upload-source', 'data')
    )
    def fjfj(n, howadd, path1, name1, path2, name2, path3, name3, active_path):
        if n == 0:
            return ntng()

        path_map = {
            'build': f'{path1}/{name1}',
            'exsitu-coord': f'{path2}/{name2}',
            'exsitu-noncoord': f'{path3}/{name3}'
        }
        path = path_map.get(active_path)
        parent = os.path.dirname(path)

        if howadd == 'auto-att':
            success = auto_assign_atts(path)
            if success:
                return html.Span(f'Statistical attributes auto-assigned to {parent}.', style = {'color': 'green'})
            else:
                return html.Span('Attribute assigning failed, check console.', style = {'color': 'red'})
        else:
            return lud.attribute_layout2(parent, path)
    
    #aadsasddassfd 
    @app.callback(
        [Output('manual-att-adder', 'children'),
         Output('manual-choice', 'data')],
        Input('submit-which-to-add-manual', 'n_clicks'),
        State('which-to-add-manual', 'value'),
        State('parent-path-1', 'data'),
        State('name-upload-1', 'data'),
        State('parent-path-2', 'data'),
        State('name-upload-2', 'data'),
        State('parent-path-3', 'data'),
        State('name-upload-3', 'data'),
        State('active-upload-source', 'data')
    )
    def hhh(n, manual_choice, path1, name1, path2, name2, path3, name3, active_path):
        path_map = {
            'build': f'{path1}/{name1}',
            'exsitu-coord': f'{path2}/{name2}',
            'exsitu-noncoord': f'{path3}/{name3}'
        }
        path = path_map.get(active_path)
        parent = os.path.dirname(path)

        if n == 0:
            return ntng(), ntng()
        else:
            if manual_choice == 'parent':
                return lud.attribute_layout3(), parent
            else:
                return lud.attribute_layout3(), path

    #add shit manually bor
    @app.callback(
        Output('manual-att-add-status', 'children'),
        Input('add-manual-att', 'n_clicks'),
        State('att-name-manual', 'value'),
        State('att-value-manual', 'value'),
        State('manual-choice', 'data')
    )
    def im_losing_it(n, name, value, path):
        if n == 0:
            return ""
        else:
            att = {name: value}
            success = add_attrs(MASTER_FILE, path, att)
            if success:
                return html.Span(f'Attribute {name}: {value} added to {path}.', style = {'color': 'green'})
            else:
                return html.Span(f'Attribute assignment failed. Check console.', style = {'color': 'red'})
            
    #------------------------------- upload initial machine file ---------------------------
    from utils.helpers import process_temp
    from utils.constants import UPLOAD_FOLDER_ROOT

    @app.callback(
        [Output('upload-machine-result', 'children'),
         Output('machine-file-status', 'children'),
         Output('att-upload-machine', 'children'),
         Output('path-for-atts-machine', 'data')],
        [Input('submit-machine-file', 'n_clicks'),
         Input('upload-machine', 'isCompleted')],   ##
        State('alloy-choice', 'value'),
        State('build-id-machine', 'value'),
        State('upload-machine', 'fileNames'),   ##
        State('build-fail-bool', 'value'),
        State('machine-file-hz', 'value'),
        State('upload-machine', 'upload_id')    ##
    )
    def machine_upload(n_clicks, is_completed, alloy, build_id, filename, fail, sample_rate, upload_id):
        trigg = ctx.triggered[0]['prop_id'] if ctx.triggered else ''
        if filename and isinstance(filename, list):
            if len(filename) > 0:
                filename = filename[0]

        if trigg == 'upload-machine.isCompleted':
            if is_completed:
                return '', html.Span(f'Received file: {filename}', style = {'color': 'green'}), '', ntng()
            else:
                return '', '', '', ntng()
        
        #make sure all required info exists
        elif trigg == 'submit-machine-file.n_clicks':
            if not filename.endswith('csv'):
                return html.Span("Input file should be a csv", style = {'color': 'red'}), '', '', ntng()
            if not alloy or not build_id or not is_completed or not sample_rate:
                return html.Span("Error: Missing required information.", style = {'color': 'red'}), '', '', ntng()
            if sample_rate:
                if sample_rate > 20:
                    return html.Span('Specified sample rate is too high', style = {'color': 'red'}), '', '', ntng()
                if isinstance(sample_rate, float):
                    sample_rate = int(sample_rate)
            try:
                failed = True if fail == 'True' else False
                
                print(f'[Dash] Upload {filename} [{upload_id}] received, beginning processing')
                full_path = os.path.join(UPLOAD_FOLDER_ROOT, upload_id, filename)
                userfile = process_temp(full_path)
                os.remove(full_path)
                print(f'[Dash] {full_path} extracted, processed as {type(userfile)} and flushed')

                if isinstance(userfile, pd.DataFrame):
                    print('[Dash] Beginning clean...')
                    userfile = vectorized_md_df_clean(userfile, sample_rate)
                    print(f'[Dash] Machine file cleaned and reprocessed at {sample_rate} Hz')
                else:
                    return html.Span('Error: uploaded file must be .csv', style={'color': 'red'}), '', '', ntng()

                build_file, atts = bt.create_machine_hdf5(userfile, build_id, filename)

                if failed:
                    atts.update({'failed': 'true'})
                else:
                    atts.update({'failed': 'false'})
                atts.update({'sample_rate': int(sample_rate)})

                bt.merge_build_to_master(MASTER_FILE, alloy, build_id, build_file, atts)
                
                path = f'/{alloy}/builds/{build_id}/machine_data'
                parent = f'/{alloy}/builds/{build_id}'

                from utils.lock import master_lock
                with master_lock:
                    with h5tbx.File(MASTER_FILE, 'a') as master:
                        master[path].attrs['build_id'] = build_id   #give ~/machine_data "build_id" attribute

                return html.Span(
                    f'Build file for {build_id} created and {filename} uploaded successfully to {path}', 
                    style = {'color': 'green'}
                ), '', add_machine_atts(parent), parent
            
            except Exception as e:
                return html.Span(f'Something went wrong: {e}', style={'color': 'red'}), '', '', ntng()
        else:
            return '', '', '', ntng()
        

        #ad jkltasjldkj the attributes bro!! add them here | for MACHINE
                                                        #  V
    @app.callback(
        Output('machine-att-add-status', 'children'),
        Input('add-machine-att', 'n_clicks'),
        State('att-name-machine', 'value'),
        State('att-value-machine', 'value'),
        State('path-for-atts-machine', 'data')
    )
    def help(n, name, value, path):
        if n == 0:
            return ""
        else:
            att = {name: value}
            success = add_attrs(MASTER_FILE, path, att)
            if success:
                return html.Span(f'Attribute {name}: {value} added to {path}.', style = {'color': 'green'})
            else:
                return html.Span(f'Attribute assignment failed. Check console.', style = {'color': 'red'})