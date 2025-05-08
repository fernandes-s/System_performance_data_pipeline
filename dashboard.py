import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import sqlite3

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "System Performance Dashboard"

# Layout of the dashboard
app.layout = html.Div(children=[
    html.H1("System Performance Dashboard"),
    dcc.Interval(id='interval-component', interval=60000, n_intervals=0),  # refresh every 60s

    dcc.Graph(id='cpu-graph'),
    dcc.Graph(id='memory-graph')
])

# Fetch data from SQLite
def fetch_data():
    conn = sqlite3.connect('system_metrics.db')
    df = pd.read_sql_query("SELECT * FROM metrics", conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# Callback to update the graphs
@app.callback(
    Output('cpu-graph', 'figure'),
    Output('memory-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graphs(n):
    df = fetch_data()

    cpu_fig = {
        'data': [{
            'x': df['timestamp'],
            'y': df['cpu_percent'],
            'type': 'line',
            'name': 'CPU %'
        }],
        'layout': {
            'title': 'CPU Usage Over Time',
            'xaxis': {'title': 'Timestamp'},
            'yaxis': {'title': 'CPU %'}
        }
    }

    mem_fig = {
        'data': [{
            'x': df['timestamp'],
            'y': df['memory_percent'],
            'type': 'line',
            'name': 'Memory %'
        }],
        'layout': {
            'title': 'Memory Usage Over Time',
            'xaxis': {'title': 'Timestamp'},
            'yaxis': {'title': 'Memory %'}
        }
    }

    return cpu_fig, mem_fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

