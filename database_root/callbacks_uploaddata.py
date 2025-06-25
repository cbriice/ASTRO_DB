import os, io, base64, pandas as pd
from dash import dcc, html, Input, Output, State, ctx
from utils.helpers import ntng, process_upload, auto_assign_atts
from backend_deep import add_data, add_attrs
from layouts_uploaddata import attribute_layout1, attribute_layout2, attribute_layout3, builddata_upload_layout, exsitu_upload_layout, exsitu_coordupload_layout 
from layouts_uploaddata import exsitu_other, upload_file_section
from layouts import add_machine_atts
from utils.tools import find_header_line
import backend_top as bt
from utils.constants import AA_ALLOY_OPS, MASTER_FILE

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
                return builddata_upload_layout()
            else:
                return exsitu_upload_layout()
        
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
                if 'builds' not in parent_path:
                    return html.Span(f'Invalid path {parent_path}', style = {'color': 'red'}), ntng(), ntng(), ntng()
                
                return upload_file_section(1), parent_path, name, 'build'
            
    @app.callback(
        [Output('upload-status-1', 'children'),
         Output('attribute-adder-1', 'children'),
         Output('uploaded-filepath-1', 'data')],
        [Input('submit-upload-1', 'n_clicks'),
         Input('upload-data-1', 'contents')],
        State('upload-data-1', 'filename'),
        State('parent-path-1', 'data'),
        State('name-upload-1', 'data')
    )
    def whoevenreadsthese(n, contents, filename, parent_path, name):
        if n == 0 and not contents:
            return '', '', ntng()
        elif n == 0 and contents:
            return html.Span(f'Received {filename}', style = {'color': 'green'}), '', ntng()
        elif n > 0 and not contents:
            return html.Span('No file uploaded', style = {'color': 'red'}), '', ntng()
        
        else:
            data = process_upload(contents, None)

            try:
                success = add_data(data, MASTER_FILE, parent_path, name, False)
                if success:
                    return html.Span(f'Data {name} added to {parent_path} in {MASTER_FILE}', style={'color': 'green'}), attribute_layout1(), f'{parent_path}/{name}'
                else:
                    return html.Span(f'Failed to add {name} to {parent_path}. Check console for what happened', style={'color': 'red'}), '', ntng()
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
                return exsitu_coordupload_layout()
            else:
                return exsitu_other()
            
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
            return upload_file_section(2), address, name, html.Span(f'Generated address {address}. Name: {name}', style = {'color': 'green'}), 'exsitu-coord'

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
                success = add_data(data, MASTER_FILE, parent_path, name, False)
                if success:
                    return html.Span(f'Data {name} added to {parent_path} in {MASTER_FILE}', style={'color': 'green'}), attribute_layout1(), f'{parent_path}/{name}'
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
            return upload_file_section(3), html.Span(f'Generated address {address}. Name: {name}', style = {'color': 'green'}), address, name, 'exsitu-noncoord'

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
            return attribute_layout2(parent, path)
    
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
                return attribute_layout3(), parent
            else:
                return attribute_layout3(), path

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
            
    #------------------------------------------------ upload initial machine file
    @app.callback(
        [Output('upload-machine-result', 'children'),
         Output('machine-file-status', 'children'),
         Output('att-upload-machine', 'children'),
         Output('path-for-atts-machine', 'data')],
        [Input('submit-machine-file', 'n_clicks'),
         Input('upload-machine', 'contents')],
        State('alloy-choice', 'value'),
        State('build-id-machine', 'value'),
        State('upload-machine', 'filename'),
        State('build-fail-bool', 'value')
    )
    def machine_upload(n_clicks, contents, alloy, build_id, filename, fail):
        trigg = ctx.triggered[0]['prop_id'] if ctx.triggered else ''

        if trigg == 'upload-machine.contents':
            if contents:
                return '', html.Span(f'Received file: {filename}', style = {'color': 'green'}), '', ntng()
            else:
                return '', '', '', ntng()
            
        elif trigg == 'submit-machine-file.n_clicks':
            if not filename.endswith('csv'):
                return html.Span("Input file should be a csv", style = {'color': 'red'}), '', '', ntng()
            if not alloy or not build_id or not contents:
                return html.Span("Error: Missing required information.", style = {'color': 'red'}), '', '', ntng()
            
            try:
                failed = True if fail == 'True' else False
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                csv_io = io.StringIO(decoded.decode('utf-8'))
                
                #find where data starts in csv
                header_row = find_header_line(csv_io)
                csv_io.seek(0)

                userfile = pd.read_csv(csv_io, skiprows = header_row)
                build_file, atts = bt.create_machine_hdf5(userfile, build_id, filename)

                if failed:
                    atts.update({'failed': 'true'})
                else:
                    atts.update({'failed': 'false'})

                bt.merge_build_to_master(MASTER_FILE, alloy, build_id, build_file, atts)
                
                path = f'/{alloy}/builds/{build_id}/machine_data'
                parent = f'/{alloy}/builds/{build_id}'
                return html.Span(
                    f'Build file for {build_id} created and {filename} uploaded successfully to {path}', 
                    style = {'color': 'green'}
                ), '', add_machine_atts(parent), parent
            
            except Exception as e:
                return f'Something went wrong: {e}', '', '', ntng()
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