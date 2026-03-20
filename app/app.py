import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
from datetime import datetime, timedelta
import os

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "System Performance Dashboard"

# Layout of the dashboard
app.layout = html.Div(
    id='main-container',  # Needed for dark mode callback
    style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'},

    children=[

        # Title
        html.H1("System Performance Dashboard", style={
            'textAlign': 'center',
            'fontSize': '32px',
            'fontWeight': 'bold',
            'marginBottom': '30px'
        }),

# Date and time selectors
html.Div([
    html.Div([
        html.Label("Select Date: ", id='date-label'),
        dcc.DatePickerSingle(
            id='date-picker',
            min_date_allowed=datetime(2025, 6, 1),
            date=datetime.today().date(),
            display_format='YYYY-MM-DD',
            style={'width': '200px', 'margin': '0 auto'}
        )
    ], id='date-div', style={
        'padding': '20px',
        'border': '1px solid #ccc',
        'borderRadius': '10px',
        'backgroundColor': '#f9f9f9',
        'boxShadow': '0 4px 8px rgba(0,0,0,0.05)',
        'marginRight': '1%',
        'flex': '1',
        'textAlign': 'center'
    }),
    

    html.Div([
        html.Label("Select Hour Range: ", id='hour-label'),
        dcc.Dropdown(
            id='time-range',
            options=[{'label': f'Last {h} Hours', 'value': f'{h}h'} for h in [1, 2, 4, 6, 8, 12, 24]],
            value='6h',
            clearable=False,
            style={'width': '200px', 'margin': '0 auto'},
            persistence=True,
            persisted_props=['value'],
            persistence_type='local'  # or 'session' if you want it to reset after tab is closed
        )
    ], id='hour-div', style={
        'padding': '20px',
        'border': '1px solid #ccc',
        'borderRadius': '10px',
        'backgroundColor': "#a39f9f",
        'boxShadow': '0 4px 8px rgba(0,0,0,0.05)',
        'marginRight': '1%',
        'flex': '1',
        'textAlign': 'center'
    }),

    html.Div([
        html.Label("Dark Mode:", id='dark-label'),
        dcc.Checklist(
            id='dark-mode-toggle',
            options=[{'label': 'Enable', 'value': 'dark'}],
            value=[],
            inputStyle={"margin-right": "5px"},
            persistence=True,
            persisted_props=['value'],
            persistence_type='local'
        )
    ], id='dark-div', style={
        'padding': '20px',
        'border': '1px solid #ccc',
        'borderRadius': '10px',
        'backgroundColor': '#f9f9f9',
        'boxShadow': '0 4px 8px rgba(0,0,0,0.05)',
        'flex': '1',
        'textAlign': 'center'
    }),


], id='selectors-row', style={
    'display': 'flex',
    'justifyContent': 'center',
    'marginBottom': '30px'
}),


        # Interval
        dcc.Interval(id='interval-component', interval=60000, n_intervals=0),

        html.Div([
            html.Div([
                dcc.Graph(id='cpu-graph')
            ], style={
                'width': '48%', 'display': 'inline-block', 'padding': '10px',
                'backgroundColor': "#ebebeb", 'borderRadius': '8px',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.05)'
            }),

            html.Div([
                dcc.Graph(id='memory-graph')
            ], style={
                'width': '48%', 'display': 'inline-block', 'padding': '10px',
                'backgroundColor': '#ebebeb', 'borderRadius': '8px',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.05)'
            })
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '30px'}),

        html.Div([
            html.Div([
                dcc.Graph(id='disk-graph')
            ], style={
                'width': '48%', 'display': 'inline-block', 'padding': '10px',
                'backgroundColor': '#ebebeb', 'borderRadius': '8px',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.05)'
            }),

            html.Div([
                dcc.Graph(id='network-graph')
            ], style={
                'width': '48%', 'display': 'inline-block', 'padding': '10px',
                'backgroundColor': '#ebebeb', 'borderRadius': '8px',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.05)'
            })
        ], style={'display': 'flex', 'justifyContent': 'space-between'})
    ]
)

# Fetch data from daily CSV
def fetch_data(selected_date):
    filename = f"daily_metrics/{selected_date}.csv"
    if not os.path.exists(filename):
        return pd.DataFrame()

    df = pd.read_csv(filename)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# Callback for darkmode container background + button section styles
@app.callback(
    Output('main-container', 'style'),
    Output('date-div', 'style'),
    Output('hour-div', 'style'),
    Output('dark-div', 'style'),
    Input('dark-mode-toggle', 'value')
)
def toggle_dark_mode(toggle_value):
    if 'dark' in toggle_value:
        container_style = {
            'backgroundColor': '#1e1e1e',
            'color': 'white',
            'fontFamily': 'Arial, sans-serif',
            'padding': '20px'
        }
        button_style = {
            'padding': '20px',
            'border': '1px solid #444',
            'borderRadius': '10px',
            'backgroundColor': '#2c2c2c',
            'boxShadow': '0 4px 8px rgba(255,255,255,0.05)',
            'marginRight': '1%',
            'flex': '1',
            'textAlign': 'center',
            'color': 'black'
        }
    else:
        container_style = {
            'backgroundColor': '#fff',
            'color': 'black',
            'fontFamily': 'Arial, sans-serif',
            'padding': '20px'
        }
        button_style = {
            'padding': '20px',
            'border': '1px solid #ccc',
            'borderRadius': '10px',
            'backgroundColor': '#f9f9f9',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.05)',
            'marginRight': '1%',
            'flex': '1',
            'textAlign': 'center'
        }

    return container_style, button_style, button_style, button_style


# Callback 
@app.callback(
    Output('cpu-graph', 'figure'),
    Output('memory-graph', 'figure'),
    Output('disk-graph', 'figure'),
    Output('network-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('time-range', 'value'),
    Input('date-picker', 'date'),
    Input('dark-mode-toggle', 'value')
)
def update_graphs(n, time_range, selected_date, dark_mode):
    if not selected_date:
        return [{}]*4

    df = fetch_data(selected_date)
    if df.empty:
        return [{}]*4

    now = df['timestamp'].max()
    hours = int(time_range.replace('h', ''))
    df = df[df['timestamp'] > now - timedelta(hours=hours)]

    is_dark = 'dark' in dark_mode
    graph_bg = '#1e1e1e' if is_dark else '#f9f9f9'
    graph_fg = '#f9f9f9' if is_dark else '#000000'

    def make_figure(y, title, color, y_title):
        return {
            'data': [{
                'x': df['timestamp'],
                'y': df[y],
                'type': 'scatter',
                'mode': 'lines+markers',
                'line': {'color': color},
                'name': title
            }],
            'layout': {
                'title': {'text': title, 'font': {'color': graph_fg}},
                'xaxis': {'title': 'Time', 'tickformat': '%H:%M', 'showgrid': True, 'color': graph_fg},
                'yaxis': {'title': y_title, 'range': [0, 100] if '%' in y_title else None, 'showgrid': True, 'color': graph_fg},
                'plot_bgcolor': graph_bg,
                'paper_bgcolor': graph_bg,
                'font': {'color': graph_fg},
                'legend': {'orientation': 'h', 'x': 0.5, 'y': 1.15, 'xanchor': 'center', 'yanchor': 'bottom'}
            }
        }

    cpu_fig = make_figure('cpu_percent', 'CPU Usage Over Time', 'royalblue', 'CPU %')
    mem_fig = make_figure('memory_percent', 'Memory Usage Over Time', 'seagreen', 'Memory %')
    disk_fig = make_figure('disk_percent', 'Disk Usage Over Time', 'orange', 'Disk %')

    network_fig = {
        'data': [
            {
                'x': df['timestamp'],
                'y': df['net_sent'],
                'type': 'scatter',
                'mode': 'lines+markers',
                'line': {'color': 'purple'},
                'name': 'Net Sent (MB)'
            },
            {
                'x': df['timestamp'],
                'y': df['net_recv'],
                'type': 'scatter',
                'mode': 'lines+markers',
                'line': {'color': 'teal'},
                'name': 'Net Recv (MB)'
            }
        ],
        'layout': {
            'title': {'text': 'Network I/O Over Time', 'font': {'color': graph_fg}},
            'xaxis': {'title': 'Time', 'tickformat': '%H:%M', 'showgrid': True, 'color': graph_fg},
            'yaxis': {'title': 'MB Transferred', 'showgrid': True, 'color': graph_fg},
            'plot_bgcolor': graph_bg,
            'paper_bgcolor': graph_bg,
            'font': {'color': graph_fg},
            'legend': {'orientation': 'h', 'x': 0.5, 'y': 1.15, 'xanchor': 'center', 'yanchor': 'bottom'}
        }
    }

    return cpu_fig, mem_fig, disk_fig, network_fig

# To deploy on render
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)

# # To debbug, run the app locally  --- http://127.0.0.1:8050/
# if __name__ == '__main__':
#     app.run(debug=True)  