import plotly.express as px
import plotly.graph_objects as go


# =========================
# BASIC LINE CHART
# =========================
def make_line_chart(df, y_col, title, y_label, height=360):
    fig = px.line(
        df,
        x="timestamp",
        y=y_col,
        title=title
    )

    fig.update_layout(
        xaxis_title="Timestamp",
        yaxis_title=y_label,
        height=height,
        margin=dict(l=20, r=20, t=60, b=20),
        title_x=0.02
    )

    return fig


# =========================
# ANOMALY CHART
# =========================
def make_anomaly_chart(
    df,
    y_col,
    title,
    y_label,
    anomaly_flag_col="anomaly_flag",
    height=420
):
    fig = go.Figure()

    # Main line
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df[y_col],
            mode="lines",
            name=title
        )
    )

    # Anomaly markers
    if anomaly_flag_col in df.columns:
        anomaly_df = df[df[anomaly_flag_col] == 1]

        if not anomaly_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=anomaly_df["timestamp"],
                    y=anomaly_df[y_col],
                    mode="markers",
                    name="Anomalies",
                    marker=dict(size=8, symbol="x")
                )
            )

    fig.update_layout(
        title=title,
        xaxis_title="Timestamp",
        yaxis_title=y_label,
        height=height,
        margin=dict(l=20, r=20, t=60, b=20),
        title_x=0.02
    )

    return fig