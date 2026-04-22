"""
Utility package for shared dashboard logic.

This package contains reusable helpers for:
- configuration
- database access
- SQL/data loading
- formatting
- metric summaries
- anomaly processing
- chart generation
- Streamlit UI helpers
"""

from .config import DB_PATH, METRICS_TABLE, ANOMALY_TABLE

from .db import get_connection, run_query

from .queries import (
    get_table_names,
    load_metrics,
    load_anomaly_results,
    load_latest_metrics,
    load_recent_metrics,
)

from .formatters import (
    format_timestamp,
    format_percentage,
    format_large_number,
    format_duration,
)

from .metrics import (
    get_latest_timestamp,
    get_time_range,
    get_summary_metrics,
    get_recent_window,
    calculate_collection_gaps,
    calculate_system_health,
)

from .anomaly import (
    prepare_features,
    get_anomaly_count,
    get_anomaly_rate,
    get_anomaly_rows,
    get_top_anomaly_drivers,
    classify_anomaly_severity,
)

from .charts import (
    make_metric_line_chart,
    make_anomaly_timeline_chart,
    make_score_distribution_chart,
    make_driver_bar_chart,
)

from .ui_helpers import (
    show_kpi_card,
    show_status_badge,
    show_empty_state,
    section_header,
)

__all__ = [
    # config
    "DB_PATH",
    "METRICS_TABLE",
    "ANOMALY_TABLE",

    # database
    "get_connection",
    "run_query",

    # queries
    "get_table_names",
    "load_metrics",
    "load_anomaly_results",
    "load_latest_metrics",
    "load_recent_metrics",

    # formatters
    "format_timestamp",
    "format_percentage",
    "format_large_number",
    "format_duration",

    # metrics
    "get_latest_timestamp",
    "get_time_range",
    "get_summary_metrics",
    "get_recent_window",
    "calculate_collection_gaps",
    "calculate_system_health",

    # anomalies
    "prepare_features",
    "get_anomaly_count",
    "get_anomaly_rate",
    "get_anomaly_rows",
    "get_top_anomaly_drivers",
    "classify_anomaly_severity",

    # charts
    "make_metric_line_chart",
    "make_anomaly_timeline_chart",
    "make_score_distribution_chart",
    "make_driver_bar_chart",

    # ui helpers
    "show_kpi_card",
    "show_status_badge",
    "show_empty_state",
    "section_header",
]