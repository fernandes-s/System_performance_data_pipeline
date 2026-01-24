import psutil
import time
from datetime import datetime

# ---- persistent state (module-level or loaded from DB/file) ----
prev_net_sent = None
prev_net_recv = None
prev_timestamp = None


def collect_metrics():
    global prev_net_sent, prev_net_recv, prev_timestamp

    timestamp = datetime.now()

    # CPU (non-blocking, better for schedulers)
    cpu_percent = psutil.cpu_percent(interval=None)

    # Memory
    memory_percent = psutil.virtual_memory().percent

    # Disk (root partition)
    disk_percent = psutil.disk_usage('/').percent

    # Network counters (cumulative)
    net = psutil.net_io_counters()
    net_sent = net.bytes_sent
    net_recv = net.bytes_recv

    # Uptime (seconds)
    uptime_seconds = time.time() - psutil.boot_time()

    # ---- network deltas (MB per interval) ----
    if prev_net_sent is None or prev_net_recv is None:
        net_sent_delta_mb = 0.0
        net_recv_delta_mb = 0.0
    else:
        net_sent_delta_mb = (net_sent - prev_net_sent) / (1024 * 1024)
        net_recv_delta_mb = (net_recv - prev_net_recv) / (1024 * 1024)

    # Update previous values
    prev_net_sent = net_sent
    prev_net_recv = net_recv
    prev_timestamp = timestamp

    return {
        "timestamp": timestamp.isoformat(),
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "disk_percent": disk_percent,
        "net_sent_mb": net_sent_delta_mb,
        "net_recv_mb": net_recv_delta_mb,
        "uptime_seconds": uptime_seconds
    }
