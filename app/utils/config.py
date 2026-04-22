from pathlib import Path

# =========================
# BASE PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODELS_DIR = ARTIFACTS_DIR / "models"

DB_PATH = RAW_DATA_DIR / "system_metrics.db"

# =========================
# DATABASE TABLES
# =========================
METRICS_TABLE = "metrics"
ANOMALY_TABLE = "anomaly_results"

# =========================
# MODEL ARTIFACT PATHS
# =========================
MODEL_PATH = MODELS_DIR / "isolation_forest_model.joblib"
SCALER_PATH = MODELS_DIR / "scaler.joblib"

# =========================
# DEFAULT APP SETTINGS
# =========================
DEFAULT_RECENT_DAYS = 7
DEFAULT_TABLE_ROWS = 10
DEFAULT_CHART_HEIGHT = 360

# =========================
# CORE METRIC COLUMNS
# =========================
METRIC_COLUMNS = [
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "net_sent_delta_mb",
    "net_recv_delta_mb",
    "uptime_seconds",
]

# =========================
# DISPLAY LABELS
# =========================
METRIC_LABELS = {
    "cpu_percent": "CPU Usage (%)",
    "memory_percent": "Memory Usage (%)",
    "disk_percent": "Disk Usage (%)",
    "net_sent_delta_mb": "Network Sent (MB)",
    "net_recv_delta_mb": "Network Received (MB)",
    "uptime_seconds": "Uptime (Seconds)",
}

# =========================
# THRESHOLDS
# =========================
CPU_WARNING_THRESHOLD = 80
MEMORY_WARNING_THRESHOLD = 80
DISK_WARNING_THRESHOLD = 85
COLLECTION_GAP_MINUTES = 10