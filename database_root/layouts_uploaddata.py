import dash_bootstrap_components as dbc
from utils.helpers import get_keys
from utils.constants import X_OPS, Y_OPS, Z_OPS, AA_ALLOY_OPS
from dash import html, dcc
from utils.constants import MASTER_FILE

#this file doesn't include layout for "upload initial machine file" section bc i didnt feel like i needed to move it bc the file was still small so go look in layouts.py

def uploaddata_layout():
    return html.Div([
        html.H4("Upload data", style = {'text-align': 'center'}), 
        html.H6("Note: machine file for each build should be uploaded under the tab 'Upload initial machine file', not here. This is an all-purpose data processor.", style = {'text-align': 'center'}), html.Br(),
        
        html.Div([
            html.H6('Ex-situ or build data?'),
            dcc.RadioItems(
                id = 'data-type',
                options = [{'label': 'Build data', 'value': 'build'},
                        {'label': 'Ex-situ data (csv, bulk)', 'value': 'exsitu-csv'},
                        {'label': 'Ex-situ data (individual)', 'value': 'exsitu'}]
            ),
            html.Button('Confirm', id = 'ex-bd-button', n_clicks = 0), html.Br(),
            html.Div(id = 'upload-builddata-info'),
        ], style = {'padding-left': '300px', 'padding-bottom': '35px'}),
        
        #just dont even worry about all this shit fr it works n thats all u need to know
        dcc.Store(id ='parent-path-1', storage_type = 'session'),
        dcc.Store(id = 'name-upload-1', storage_type = 'session'),
        dcc.Store(id = 'parent-path-2', storage_type = 'session'),
        dcc.Store(id = 'name-upload-2', storage_type = 'session'),
        dcc.Store(id = 'parent-path-3', storage_type = 'session'),
        dcc.Store(id = 'name-upload-3', storage_type = 'session'),

        dcc.Store(id = 'active-upload-source', storage_type = 'session')
    ])
    

#arbitrary data upload
def builddata_upload_layout():
    return html.Div([
        html.Br(),
        html.Label('Input address and name:'), html.Br(),
        dcc.Input(
            id = 'parent-path-input', 
            type = 'text', 
            placeholder = '/ALLOY/builds/...',
            size = '40'
        ), html.Br(),
        dcc.Input(
            id = 'input-name', 
            type = 'text', 
            placeholder = 'Title for data',
            size = '40'
        ), html.Br(),

        html.Button('Submit', id = 'submit-data-button', n_clicks = 0), 
        html.Br(), html.Br(),
        html.Div(id = 'upload-output'),
        html.Br()
    ])

#---------------------------------
def upload_file_section(g_id):
    return html.Div([
        html.Label("Upload data from computer:"),
        dcc.Upload(
            id=f'upload-data-{g_id}',
            children=html.Div(html.A('Select Files')), 
            style={
                'width': '30%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '2px',
                'borderStyle': 'solid',
                'textAlign': 'center',
            },
            multiple=False
        ), html.Br(),

        html.H6('Is this a csv file that needs to be cleaned?'),
        html.Label('Raw in-situ, motion capture files should be cleaned.'), html.Br(),
        dcc.RadioItems(
            id = 'cleaned-or-not',
            options = [{'label': 'Yes', 'value': 'need-clean'},
                       {'label': 'No', 'value': 'no-clean'}],
            value = 'need-clean'
        ), html.Br(),
        html.Label('Sample rate (should match that of the associated build file):'), html.Br(),
        dcc.Input(id = 'sample-rate', type = 'number', placeholder = '1', step = 1), html.Br(), html.Br(),
        
        html.Button('Upload', id=f'submit-upload-{g_id}', n_clicks=0, style={'backgroundColor': "#b3f097"}),
        dcc.Store(id=f'uploaded-filepath-{g_id}', storage_type='session'),
        html.Div(id=f'upload-status-{g_id}'), html.Br(),
        html.Div(id=f'attribute-adder-{g_id}')
    ])

#--------------------------------- exsitu layouts
def exsitu_upload_layout():
    return html.Div([
        html.Br(),
        html.Label('Does exsitu data have coordinates?'),
        dcc.RadioItems(
            id = 'exsitu-coord-bool',
            options = [{'label': 'Yes', 'value': 'yes'},
                       {'label': 'No', 'value': 'no'}],
            value = 'yes'
        ),
        html.Button('Confirm', id = 'confirm-coord-bool', n_clicks = 0), html.Br(),
        html.Div(id = 'exsitu-upload')
    ])

def exsitu_coordupload_layout():
    return html.Div([
        html.Br(),
        html.H6('Alloy:'),
        dcc.Dropdown(
            id = 'exsitu-alloy-dropdown',
            options = [{'label': a, 'value': a} for a in AA_ALLOY_OPS],
            placeholder = 'Select alloy',
            style = {'maxWidth': '150px'}
        ), html.Br(),

        html.H6('Select coordinates corresponding to where sample was taken from:'),
        dcc.Dropdown(
            id = 'x-coord-dropdown',
            options = [{'label': x, 'value': x} for x in X_OPS],
            placeholder = 'X coordinate',
            style = {'maxWidth': '150px'}
        ),
        dcc.Dropdown(
            id = 'y-coord-dropdown',
            options = [{'label': y, 'value': y} for y in Y_OPS],
            placeholder = 'Y coordinate',
            style = {'maxWidth': '150px'}
        ),
        dcc.Dropdown(
            id = 'z-coord-dropdown',
            options = [{'label': z, 'value': z} for z in Z_OPS],
            placeholder = 'Z coordinate',
            style = {'maxWidth': '150px'}
        ), html.Br(),

        html.H6('Type of data?'),
        dcc.Dropdown(
            id = 'datatype-exsitu-coord',
            options = [{'label': 'Cross-section image', 'value': 'cross_section_img'},
                       {'label': 'Mechanical testing data', 'value' : 'mech_test_data'},
                       {'label': 'Other', 'value': 'other'}],
            placeholder = 'Type of data',
            style = {'maxWidth': '400px'}
        ), html.Br(),
        html.Label('Name for data'), html.Br(),
        dcc.Input(
            id = 'name-exsitu-coord', 
            type = 'text',
            placeholder = 'unique_name'
        ), html.Br(),
        html.Button('Generate address', id = 'confirm-coords', n_clicks = 0), html.Br(),
        html.Div(id = 'generated-address-display'), html.Br(), 
        html.Div(id = 'exsitu-coord-page2')
    ])

def exsitu_other():
    return html.Div([
        html.Br(),
        html.H6('Enter information for data'),
        html.Label('Choose alloy'), html.Br(),
        dcc.Dropdown(
            id = 'alloy-other-exs',
            options = [{'label': a, 'value': a} for a in AA_ALLOY_OPS],
            placeholder = 'Select alloy',
            style = {'maxWidth': '150px'}
        ), html.Br(),
        html.Label('Name for data'), html.Br(),
        dcc.Input(
            id = 'exsitu-name',
            type = 'text',
            placeholder = 'unique_name'
        ), html.Br(), html.Br(),

        html.H6('Type of data?'),
        dcc.Dropdown(
            id = 'datatype-exsitu-other',
            options = [{'label': 'Build image', 'value': 'buildimg'},
                       {'label': 'Other', 'value': 'other'}],
            placeholder = 'Type of data',
            style = {'maxWidth': '400px'}
        ), html.Br(),
        html.Button('Generate address', id = 'submit-exsitu-data', n_clicks = 0), html.Br(),
        html.Div(id = 'other-gen-status'), html.Br(),
        html.Div(id = 'exsitu-attribute-adder')
    ])

def exsitu_csv_1():
    return html.Div([
        html.Br(),
        html.H6('Upload ex-situ CSV'),
        html.Label('Note: Attributes and location for this data will be automatically processed. Make sure file formatting is standardized.'), html.Br(), html.Br(),
        upload_file_section(37)
    ])

#-------------------------- attribute layouts
def attribute_layout1():
    return html.Div([
        html.H6('Add attributes to the uploaded data?'),
        dcc.RadioItems(
            id = 'how-add-atts',
            options = [{'label': 'Automatically assign attributes based on file data (not recommended unless data was uploaded as a .csv with formatted output)', 'value': 'auto-att'},
                       {'label': 'Manually add attributes (good for date, conditions, things which are not explicitly defined in uploaded files)', 'value': 'manual-att'}]
        ),
        html.Button('Confirm', id = 'confirm-att-method', n_clicks = 0), html.Br(),
        html.Div(id = 'att-assignor')
    ])
    
def attribute_layout2(parent, path):
    p = parent.split('/')[-1]
    h = path.split('/')[-1]
    return html.Div([
        html.Br(),
        html.H6('Manually add attributes:'),
        html.Label('Add attributes to the group containing the data or the data itself?'), html.Br(),
        dcc.RadioItems(
            id = 'which-to-add-manual',
            options = [{'label': f'{p}', 'value': 'parent'},
                       {'label': f'{h}', 'value': 'head'}]
        ),
        html.Button('Confirm', id = 'submit-which-to-add-manual', n_clicks = 0),
        html.Div(id = 'manual-att-adder'),
        dcc.Store(id = 'manual-choice', storage_type = 'session')
    ])

def attribute_layout3():
    return html.Div([
        html.Br(),
        dcc.Input(
            id = 'att-name-manual',
            type = 'text',
            placeholder = 'Name of attribute',
            size = '40'
        ),
        dcc.Input(
            id = 'att-value-manual',
            placeholder = 'Value for attribute',
            size = '40'
        ), html.Br(),
        html.Button('Add', id = 'add-manual-att', n_clicks = 0),
        html.Div(id = 'manual-att-add-status')
    ])