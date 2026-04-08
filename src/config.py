"""
Future improvement:
Create a central configuration file to standardise project paths,
table names, model settings, and dashboard thresholds.

This would improve maintainability, reduce duplicated hardcoded values,
and make the project structure more aligned with software engineering best practices.
"""

# from pathlib import Path

# # =========================
# # PROJECT ROOT
# # =========================
# # src/config.py -> project root
# PROJECT_ROOT = Path(__file__).resolve().parents[1]

# # =========================
# # DATA PATHS
# # =========================
# DATA_DIR = PROJECT_ROOT / "data"
# RAW_DATA_DIR = DATA_DIR / "raw"
# EXPORT_DIR = DATA_DIR / "daily_exports"

# DB_PATH = RAW_DATA_DIR / "system_metrics.db"

# # =========================
# # ARTIFACT PATHS
# # =========================
# ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
# MODEL_DIR = ARTIFACTS_DIR / "models"

# MODEL_PATH = MODEL_DIR / "isolation_forest_model.joblib"
# SCALER_PATH = MODEL_DIR / "scaler.joblib"

# # Optional future metadata files
# MODEL_METADATA_PATH = MODEL_DIR / "model_metadata.json"

# # =========================
# # DATABASE TABLE NAMES
# # =========================
# METRICS_TABLE = "metrics"
# ANOMALY_TABLE = "anomaly_results"

# # =========================
# # COLLECTION SETTINGS
# # =========================
# # Metrics are collected every 1 minute
# COLLECTION_INTERVAL_MINUTES = 1

# # =========================
# # MODEL FEATURES
# # =========================
# DEFAULT_FEATURES = [
#     "cpu_percent",
#     "memory_percent",
#     "disk_percent",
#     "net_sent_delta_mb",
#     "net_recv_delta_mb",
#     "uptime_seconds",
# ]

# # =========================
# # MODEL SETTINGS
# # =========================
# MODEL_CONTAMINATION = 0.02
# MODEL_RANDOM_STATE = 42
# MODEL_N_ESTIMATORS = 200

# # =========================
# # DATA CLEANING SETTINGS
# # =========================
# # Valid operating ranges for metrics
# CPU_MIN = 0
# CPU_MAX = 100

# MEMORY_MIN = 0
# MEMORY_MAX = 100

# DISK_MIN = 0
# DISK_MAX = 100

# NETWORK_DELTA_MIN = 0

# # Network outlier filtering quantiles
# NETWORK_OUTLIER_LOWER_QUANTILE = 0.01
# NETWORK_OUTLIER_UPPER_QUANTILE = 0.99

# # Keep only rows collected exactly on the minute
# FILTER_EXACT_MINUTE_TIMESTAMPS = True

# # =========================
# # PIPELINE HEALTH SETTINGS
# # =========================
# # Delay thresholds for dashboard health checks
# PIPELINE_DELAY_WARNING_MINUTES = 3
# PIPELINE_DELAY_CRITICAL_MINUTES = 10

# # Gap detection tolerance
# EXPECTED_INTERVAL_MINUTES = COLLECTION_INTERVAL_MINUTES
# MISSING_GAP_THRESHOLD_MINUTES = 2

# # =========================
# # SYSTEM HEALTH THRESHOLDS
# # =========================
# CPU_WARNING = 70
# CPU_CRITICAL = 90

# MEMORY_WARNING = 75
# MEMORY_CRITICAL = 90

# DISK_WARNING = 80
# DISK_CRITICAL = 95

# # =========================
# # DASHBOARD SETTINGS
# # =========================
# DEFAULT_RECENT_ROWS_LIMIT = 10
# DEFAULT_CHART_DAYS = 7
# DEFAULT_EXPORT_FILENAME = "anomaly_results_filtered.csv"