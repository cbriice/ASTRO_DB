from dash import dcc, html
from utils.data_compiler import compile_atts
from utils.constants import ATT_CATEGORIES_HIGHEST

def att_main():
    return html.Div([
        html.H4('Add any attribute anywhere', style = {'text-align': 'center'}), html.Br(),
        html.Div([
            html.H6('Enter address to add attribute to:'), 
            dcc.Input(
                id = 'att-address',
                type = 'text',
                placeholder = '/some/address',
                size = '50'
            ), html.Br(),
            html.Button('Pull', id = 'pull-address-att', n_clicks = 0), html.Br(),
            dcc.Store(id = 'user-address', storage_type = 'memory'),
            html.Div(id = 'att-page-2'), html.Br(),
            html.Div(id = 'att-page-3')
        ], style = {'padding-left': '300px'})
    ], style = {'padding-bottom': '50px'})

def att_second():
    return html.Div([
        html.Br(),
        html.Button('Show current attributes', id = 'show-curr-atts', n_clicks = 0), 
        html.Button('Hide current attributes', id = 'hide-curr-atts', n_clicks = 0), html.Br(),
        html.Div(id = 'curr-atts-page')
    ])

def show_curr_atts(path):
    return html.Div([
        html.H6(f'Current atttributes of {path}:', style = {'padding-left': '480px'}),
        compile_atts(path)
    ])

def add_att():
    return html.Div([
        html.H6('Add new attribute:'),
        dcc.Dropdown(
            id = {'type': 'dropdown', 'stage': 'category'},
            options = [{'label': c, 'value': c} for c in ATT_CATEGORIES_HIGHEST],
            placeholder = 'Choose category',
            style = {'maxWidth': '200px'}
        ), html.Br(),
        html.Div(id = 'next-att-dropdown'),
        html.Div(id = 'next-next-att-dropdown'),
        html.Div(id = 'num-or-text-container'),
        dcc.Store(id = 'att-key', storage_type = 'memory')
    ])

def att_dropdown(options, stage):
    return html.Div([
        dcc.Dropdown(
            id = {'type': 'dropdown', 'stage': stage},
            options = [{'label': c, 'value': c} for c in options],
            placeholder = 'Choose subcategory',
            style = {'maxWidth': '200px'}
        ), html.Br()
    ])

def type_of_att():
    return html.Div([
        html.Label('Numerical or text data?'), html.Br(),
        dcc.RadioItems(
            id = 'num-or-text-atts',
            options = [{'label': 'Numerical', 'value': 'num'}, 
                       {'label': 'Text', 'value': 'text'}]
        ), html.Br(),
        html.Div(id = 'enter-att')
    ])

def enter_att1():
    return html.Div([
        dcc.Input(
            id = {'type': 'att-input', 'method': 'text'},
            type = 'text',
            placeholder = 'att (warning - case sensitive!)',
            size = '40'
        ),
        html.Button('Submit', id = {'type': 'submit-att', 'method': 'text'}, n_clicks = 0),
        html.Div(id = {'type': 'att-status', 'method': 'text'})
    ])

def enter_att2():
    return html.Div([
        dcc.Input(
            id = {'type': 'att-input', 'method': 'num'},
            type = 'number',
            placeholder = '0.0',
            size = '20'
        ),
        html.Button('Submit', id = {'type': 'submit-att', 'method': 'num'}, n_clicks = 0),
        html.Div(id = {'type': 'att-status', 'method': 'num'})
    ])

def enter_any():
    return html.Div([
        html.Label('Enter attribute key (WATCH SPELLING!)'), html.Br(),
        dcc.Input(
            id = 'att-name-other',
            type = 'text',
            placeholder = 'name',
            size = '40'
        ), html.Br(),
        html.Button('Confirm', id = 'confirm-name-other', n_clicks = 0), html.Br(), html.Br(),
        html.Div(id = 'att-other-continuation')
    ])