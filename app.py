import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "System Performance Dashboard"

# Layout of the dashboard
app.layout = html.Div(children=[
    html.H1("System Performance Dashboard"),
    dcc.Interval(id='interval-component', interval=60000, n_intervals=0),  # refresh every 60s

    html.Div([
        html.Label("Select Time Range:"),
        dcc.Dropdown(
            id='time-range',
            options=[
                {'label': 'Last 1 Hour', 'value': '1h'},
                {'label': 'Last 6 Hours', 'value': '6h'},
                {'label': 'Last 24 Hours', 'value': '24h'},
                {'label': 'All Data', 'value': 'all'}
            ],
            value='6h',
            clearable=False,
            style={'width': '200px'}
        )
    ]),

    html.Div([
        html.Div([
            dcc.Graph(id='cpu-graph')
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '0 1%'}),

        html.Div([
            dcc.Graph(id='memory-graph')
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '0 1%'})
    ]),

    html.Div([
        html.Div([
            dcc.Graph(id='disk-graph')
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '0 1%'}),

        html.Div([
            dcc.Graph(id='network-graph')
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '0 1%'})
    ])
])

# Fetch data from SQLite
def fetch_data():
    csv_path = os.getenv("CSV_PATH")
    
    # If CSV_PATH is defined, load from CSV instead of database
    if csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        conn = sqlite3.connect('system_metrics.db')
        df = pd.read_sql_query("SELECT * FROM metrics", conn)
        conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# Callback to update the graphs
@app.callback(
    Output('cpu-graph', 'figure'),
    Output('memory-graph', 'figure'),
    Output('disk-graph', 'figure'),
    Output('network-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('time-range', 'value')
)
def update_graphs(n, time_range):
    df = fetch_data()

    if time_range != 'all':
        now = datetime.now()
        if time_range == '1h':
            df = df[df['timestamp'] > now - timedelta(hours=1)]
        elif time_range == '6h':
            df = df[df['timestamp'] > now - timedelta(hours=6)]
        elif time_range == '24h':
            df = df[df['timestamp'] > now - timedelta(hours=24)]

    cpu_fig = {
        'data': [{
            'x': df['timestamp'],
            'y': df['cpu_percent'],
            'type': 'scatter',
            'mode': 'lines+markers',
            'line': {'color': 'royalblue'},
            'name': 'CPU Usage (%)'
        }],
        'layout': {
            'title': 'CPU Usage Over Time',
            'xaxis': {'title': 'Time', 'tickformat': '%H:%M', 'showgrid': True},
            'yaxis': {'title': 'CPU %', 'range': [0, 100], 'showgrid': True},
            'showlegend': True,
            'legend': {'orientation': 'h', 'x': 0.5, 'y': 1.15, 'xanchor': 'center', 'yanchor': 'bottom'}
        }
    }

    mem_fig = {
        'data': [{
            'x': df['timestamp'],
            'y': df['memory_percent'],
            'type': 'scatter',
            'mode': 'lines+markers',
            'line': {'color': 'seagreen'},
            'name': 'Memory Usage (%)'
        }],
        'layout': {
            'title': 'Memory Usage Over Time',
            'xaxis': {'title': 'Time', 'tickformat': '%H:%M', 'showgrid': True},
            'yaxis': {'title': 'Memory %', 'range': [0, 100], 'showgrid': True},
            'showlegend': True,
            'legend': {'orientation': 'h', 'x': 0.5, 'y': 1.15, 'xanchor': 'center', 'yanchor': 'bottom'}
        }
    }

    disk_fig = {
        'data': [{
            'x': df['timestamp'],
            'y': df['disk_percent'],
            'type': 'scatter',
            'mode': 'lines+markers',
            'line': {'color': 'orange'},
            'name': 'Disk Usage (%)'
        }],
        'layout': {
            'title': 'Disk Usage Over Time',
            'xaxis': {'title': 'Time', 'tickformat': '%H:%M', 'showgrid': True},
            'yaxis': {'title': 'Disk %', 'range': [0, 100], 'showgrid': True},
            'showlegend': True,
            'legend': {
                'orientation': 'h',
                'x': 0.5,
                'y': 1.15,
                'xanchor': 'center',
                'yanchor': 'bottom'
            }
        }
    }

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
            'title': 'Network I/O Over Time',
            'xaxis': {'title': 'Time', 'tickformat': '%H:%M', 'showgrid': True},
            'yaxis': {'title': 'MB Transferred', 'showgrid': True},
            'showlegend': True,
            'legend': {
                'orientation': 'h',
                'x': 0.5,
                'y': 1.15,
                'xanchor': 'center',
                'yanchor': 'bottom'
            }
        }
    }

    return cpu_fig, mem_fig, disk_fig, network_fig

# Run the app
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
