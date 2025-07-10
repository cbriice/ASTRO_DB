import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from utils.helpers import get_keys
from utils.constants import AA_ALLOY_OPS
from utils.constants import MASTER_FILE

def edit_db_layout():
    return html.Div([
        html.H4("Edit database", style = {'text-align': 'center'}), 
        html.Div([
            html.Button('Create a folder', id = 'create-folder', n_clicks = 0),
            html.Button('Delete/move files', id = 'del-or-move', n_clicks = 0), html.Br(), html.Br()
        ], style = {'textAlign': 'center'}),
        html.Div(id = 'edit-db-container')
    ])

def creategroup_layout():
    return html.Div([
        html.H6('Initialize a folder'),
        html.Label("[IMPORTANT] Input desired location for group separated by / (i.e. /AAXXXX/builds/data1/something/etc)"), html.Br(),

        dcc.Input(
            id = 'created-path', 
            type = 'text', 
            placeholder = 'File: /example/like/this'
        ), html.Br(), html.Br(),

        html.Label("Input name of your folder:"), html.Br(),
        dcc.Input(
            id = 'created-name',
            type = 'text',
            placeholder = 'A_unique_name'
        ), html.Br(), html.Br(),

        html.Button('Submit', id = 'submit-group-creation', n_clicks = 0), html.Br(),
        html.Div(id = 'group-creation-output')
    ],
    style = {'padding': '20px 35px'}
    )

def del_or_move():
    return html.Div([
        html.Label('Address:'), html.Br(),
        dcc.Input(
            id = 'address-to-edit',
            type = 'text',
            placeholder = '/',
            size = '50'
        ), html.Br(),
        html.Button('Move', id = 'move-sm', n_clicks = 0),
        html.Button('Delete', id = 'delete-sm', n_clicks = 0), html.Br(),
        html.Div(id = 'edit-page-2')
    ], style = {'padding-left': '300px'})

#----------------------------------------------------------
def browsedb_layout():
    return html.Div([
        html.H4("Browse database", style = {'text-align': 'center'}), 
        html.Div(id = 'dropdown-container', children =[
            dcc.Dropdown(
                id = {'type': 'dynamic-dropdown', 'index': 0}, 
                options = get_keys(MASTER_FILE, MASTER_FILE), 
                placeholder = 'Select top-level group'),
        ],
            style = {'padding': '30px 300px'}
        ), 
        html.Div(id = 'end-of-chain', style = {'padding-left': '300px'}), 
        html.Div(id = 'selected-path', style = {'padding-left': '300px'}), html.Br(),
        dcc.Store(id = 'selected-path-store', storage_type = 'memory'),

        html.Div(
            dcc.Clipboard(
                id = 'clipboard', 
                target_id = 'selected-path',
                style = {
                    'fontSize': '24px',
                    'backgroundColor': "#c8e9b8",
                    'color': 'black',
                    'textAlign': 'center',
                    'width': '100px'
                },
                html_content = "Copy Address"
                ),
            style = {'padding-left': '300px'}
        ), html.Br(),

        html.Div([
            html.Button('Show details', id = 'show-atts-bd', n_clicks = 0), 
            html.Button('Export dataset as .csv', id = 'export-ds-csv', n_clicks = 0)
        ], style = {'padding-left': '300px'}),
        html.Div(id = 'csv-download-link', style = {'padding-left': '300px'}),
        html.Div(id = 'details-bd', style = {'padding-left': '300px', 'padding-right': '300px'})
    ])

#display data from browsedb
def display_data_info(formatted_atts, stored_data, graph):
    return html.Div([
        html.H5('Formatted attributes:', style = {'text-align': 'center'}),
        formatted_atts if formatted_atts else html.Span('No attributes found.'),
        html.H5('Stored data:', style = {'text-align': 'center'}),
        html.Div([
            html.Div(stored_data, style = {'display': 'inline-block', 'width': '45%'}), 
            html.Div(graph, style = {'display': 'inline-block'})
            ], style = {'display': 'flex', 'justifyContent': 'space-between'}),
        html.Br()
    ], style = {'padding-bottom': '75px'})

#-------------------------------- upload initial machine file layouts
def uploadmachine_layout():
    return html.Div([
        html.H4("Initialize build file with machine data", style = {'text-align': 'center'}),
        html.Label("Drag and drop or click and upload machine .csv file."),
        dcc.Upload(
            id = 'upload-machine',
            children = html.Div(html.A('Select Files')), 
            style = {
                'width': '30%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '2px',
                'borderStyle': 'solid',
                'textAlign': 'center',
            },
            multiple = False
        ),
        html.Div(id = 'machine-file-status'), html.Br(),

        html.Label('Alloy:'), html.Br(),
        dcc.Dropdown(
            id = 'alloy-choice',
            options = AA_ALLOY_OPS,
            placeholder = 'Select alloy used in build',
            style = {'maxWidth': '300px'}
            ), html.Br(),

        html.Label('Did the build fail?'), html.Br(),
        dcc.Dropdown(
            id = 'build-fail-bool',
            options = [{'label': 'Yes', 'value': 'True'}, {'label': 'No', 'value': 'False'}],
            placeholder = 'Yes or No',
            style = {'maxWidth': '150px'}
        ), html.Br(),

        html.Label("Input build ID"), html.Br(),
        dcc.Input(
            id = 'build-id-machine', 
            type = 'text',
            placeholder = 'B1234'
            ), html.Br(), html.Br(),

        html.Label('Desired sample rate'), html.Br(),
        dcc.Input(
            id = 'machine-file-hz',
            type = 'number',
            placeholder = '1',
            step = 1
        ), html.Br(), html.Br(),
            
        html.Button('Submit', id = 'submit-machine-file', n_clicks = 0), html.Br(),
        dcc.Store('path-for-atts-machine', storage_type = 'memory'),
        html.Div(id = 'upload-machine-result'), html.Br(),
        html.Div(id = 'att-upload-machine')
    ],
        style = {'padding': '30px 300px'}
    )

def add_machine_atts(parent):
    name = parent.split('/')[-1]
    return html.Div([
        html.H6(f'Add attributes to {name}: (optional)'),
        dcc.Input(
            id = 'att-name-machine',
            type = 'text',
            placeholder = 'Name of attribute',
            size = '40'
        ),
        dcc.Input(
            id = 'att-value-machine',
            placeholder = 'Value for attribute',
            size = '40'
        ), html.Br(),
        html.Button('Add', id = 'add-machine-att', n_clicks = 0),
        html.Div(id = 'machine-att-add-status')
    ])
#-----------------------------------

def admin_layout():
    return html.Div([
        html.H4('Admin tools', style = {'padding-left': '815px'}),
        html.Br(),
        html.Div(html.Button("Generate bypass link", id = 'bypass-gen', n_clicks = 0), style = {'padding-left': '800px'}), html.Br(),
        html.Div(id = 'bypass-link-output'),
    ], style = {'padding-left': '50px', 'padding-right': '50px'})