import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.config import DEFAULT_CHART_HEIGHT, METRIC_LABELS
from utils.metrics import ensure_datetime


def _get_metric_label(column_name: str) -> str:
    """
    Return a display label for a metric column.
    """
    return METRIC_LABELS.get(column_name, column_name.replace("_", " ").title())


# def _apply_standard_layout(fig, height: int = DEFAULT_CHART_HEIGHT):
#     """
#     Apply a consistent layout style across all charts.
#     """
#     fig.update_layout(
#         height=height,
#         margin=dict(l=20, r=20, t=50, b=20),
#         template="plotly_white",
#         legend_title_text="",
#     )
#     return fig

def _apply_standard_layout(fig, height: int = DEFAULT_CHART_HEIGHT):
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=60, b=20),
        template="plotly_white",
        legend_title_text="",
        font=dict(size=16),
        title_font=dict(size=22),
        xaxis=dict(
            title_font=dict(size=16),
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            title_font=dict(size=16),
            tickfont=dict(size=14),
        ),
        legend=dict(font=dict(size=14)),
    )
    return fig

def make_metric_line_chart(
    df: pd.DataFrame,
    metric: str,
    time_column: str = "timestamp",
    title: str | None = None,
    height: int = DEFAULT_CHART_HEIGHT,
):
    """
    Create a standard time-series line chart for a selected metric.

    Args:
        df (pd.DataFrame): Input DataFrame.
        metric (str): Metric column to plot.
        time_column (str): Timestamp column.
        title (str | None): Optional chart title.
        height (int): Chart height.

    Returns:
        plotly.graph_objects.Figure: Plotly figure.
    """
    if df.empty or time_column not in df.columns or metric not in df.columns:
        return go.Figure()

    chart_df = df[[time_column, metric]].copy()
    chart_df = ensure_datetime(chart_df, time_column)
    chart_df = chart_df.dropna(subset=[time_column, metric])

    if chart_df.empty:
        return go.Figure()

    fig = px.line(
        chart_df,
        x=time_column,
        y=metric,
        title=title or _get_metric_label(metric),
        labels={
            time_column: "Timestamp",
            metric: _get_metric_label(metric),
        },
    )

    fig.update_traces(mode="lines")
    return _apply_standard_layout(fig, height=height)


def make_multi_metric_line_chart(
    df: pd.DataFrame,
    metrics: list[str],
    time_column: str = "timestamp",
    title: str = "Metric Trends",
    height: int = DEFAULT_CHART_HEIGHT,
):
    """
    Create a multi-line time-series chart for multiple metrics.

    Args:
        df (pd.DataFrame): Input DataFrame.
        metrics (list[str]): Metric columns to include.
        time_column (str): Timestamp column.
        title (str): Chart title.
        height (int): Chart height.

    Returns:
        plotly.graph_objects.Figure: Plotly figure.
    """
    if df.empty or time_column not in df.columns:
        return go.Figure()

    available_metrics = [col for col in metrics if col in df.columns]
    if not available_metrics:
        return go.Figure()

    chart_df = df[[time_column] + available_metrics].copy()
    chart_df = ensure_datetime(chart_df, time_column)
    chart_df = chart_df.dropna(subset=[time_column])

    if chart_df.empty:
        return go.Figure()

    long_df = chart_df.melt(
        id_vars=time_column,
        value_vars=available_metrics,
        var_name="metric",
        value_name="value",
    )

    long_df["metric"] = long_df["metric"].map(_get_metric_label)

    fig = px.line(
        long_df,
        x=time_column,
        y="value",
        color="metric",
        title=title,
        labels={
            time_column: "Timestamp",
            "value": "Value",
            "metric": "Metric",
        },
    )

    fig.update_traces(mode="lines")
    return _apply_standard_layout(fig, height=height)


def make_anomaly_timeline_chart(
    df: pd.DataFrame,
    metric: str,
    time_column: str = "timestamp",
    flag_column: str = "anomaly_flag",
    title: str | None = None,
    height: int = DEFAULT_CHART_HEIGHT,
):
    """
    Create a time-series line chart with anomaly points highlighted.

    Args:
        df (pd.DataFrame): Input DataFrame.
        metric (str): Metric column to plot.
        time_column (str): Timestamp column.
        flag_column (str): Anomaly flag column.
        title (str | None): Optional chart title.
        height (int): Chart height.

    Returns:
        plotly.graph_objects.Figure: Plotly figure.
    """
    required_columns = {time_column, metric, flag_column}
    if df.empty or not required_columns.issubset(df.columns):
        return go.Figure()

    chart_df = df[[time_column, metric, flag_column]].copy()
    chart_df = ensure_datetime(chart_df, time_column)
    chart_df = chart_df.dropna(subset=[time_column, metric])

    if chart_df.empty:
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart_df[time_column],
            y=chart_df[metric],
            mode="lines",
            name=_get_metric_label(metric),
        )
    )

    anomaly_df = chart_df[chart_df[flag_column] == 1].copy()

    if not anomaly_df.empty:
        fig.add_trace(
            go.Scatter(
                x=anomaly_df[time_column],
                y=anomaly_df[metric],
                mode="markers",
                name="Anomalies",
                marker=dict(size=8, symbol="circle"),
            )
        )

    fig.update_layout(
        title=title or f"{_get_metric_label(metric)} with Anomalies",
        xaxis_title="Timestamp",
        yaxis_title=_get_metric_label(metric),
    )

    return _apply_standard_layout(fig, height=height)


def make_score_distribution_chart(
    df: pd.DataFrame,
    score_column: str = "anomaly_score",
    title: str = "Anomaly Score Distribution",
    height: int = DEFAULT_CHART_HEIGHT,
):
    """
    Create a histogram of anomaly scores.

    Args:
        df (pd.DataFrame): Input DataFrame.
        score_column (str): Column containing anomaly scores.
        title (str): Chart title.
        height (int): Chart height.

    Returns:
        plotly.graph_objects.Figure: Plotly figure.
    """
    if df.empty or score_column not in df.columns:
        return go.Figure()

    chart_df = df[[score_column]].copy()
    chart_df[score_column] = pd.to_numeric(chart_df[score_column], errors="coerce")
    chart_df = chart_df.dropna(subset=[score_column])

    if chart_df.empty:
        return go.Figure()

    fig = px.histogram(
        chart_df,
        x=score_column,
        nbins=40,
        title=title,
        labels={score_column: "Anomaly Score"},
    )

    return _apply_standard_layout(fig, height=height)


def make_driver_bar_chart(
    driver_df: pd.DataFrame,
    feature_column: str = "feature",
    value_column: str = "avg_abs_zscore",
    title: str = "Top Anomaly Drivers",
    height: int = DEFAULT_CHART_HEIGHT,
):
    """
    Create a bar chart showing the strongest anomaly drivers.

    Args:
        driver_df (pd.DataFrame): Driver summary DataFrame.
        feature_column (str): Feature name column.
        value_column (str): Driver strength column.
        title (str): Chart title.
        height (int): Chart height.

    Returns:
        plotly.graph_objects.Figure: Plotly figure.
    """
    required_columns = {feature_column, value_column}
    if driver_df.empty or not required_columns.issubset(driver_df.columns):
        return go.Figure()

    chart_df = driver_df.copy()
    chart_df[feature_column] = chart_df[feature_column].map(_get_metric_label)

    fig = px.bar(
        chart_df,
        x=value_column,
        y=feature_column,
        orientation="h",
        title=title,
        labels={
            value_column: "Average Absolute Z-Score",
            feature_column: "Feature",
        },
    )

    fig.update_layout(yaxis=dict(categoryorder="total ascending"))
    return _apply_standard_layout(fig, height=height)


def make_severity_bar_chart(
    df: pd.DataFrame,
    severity_column: str = "severity",
    title: str = "Anomaly Severity Breakdown",
    height: int = DEFAULT_CHART_HEIGHT,
):
    """
    Create a bar chart showing counts by anomaly severity.

    Args:
        df (pd.DataFrame): Input anomaly DataFrame.
        severity_column (str): Severity label column.
        title (str): Chart title.
        height (int): Chart height.

    Returns:
        plotly.graph_objects.Figure: Plotly figure.
    """
    if df.empty or severity_column not in df.columns:
        return go.Figure()

    counts = (
        df[severity_column]
        .value_counts(dropna=False)
        .rename_axis(severity_column)
        .reset_index(name="count")
    )

    fig = px.bar(
        counts,
        x=severity_column,
        y="count",
        title=title,
        labels={
            severity_column: "Severity",
            "count": "Count",
        },
    )

    return _apply_standard_layout(fig, height=height)