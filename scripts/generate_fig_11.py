from pathlib import Path
import sqlite3

import pandas as pd
import matplotlib.pyplot as plt


# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"
OUTPUT_PATH = BASE_DIR / "artifacts" / "figures" / "figure_11_example_anomaly_output.png"


# =========================
# LOAD DATA
# =========================
def load_anomaly_data(db_path: Path) -> pd.DataFrame:
    """
    Load timestamped anomaly results from SQLite.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)

    query = """
        SELECT
            timestamp,
            net_sent_delta_mb,
            anomaly_score,
            is_anomaly,
            anomaly_strength,
            top_driver
        FROM anomaly_results
        WHERE timestamp IS NOT NULL
          AND net_sent_delta_mb IS NOT NULL
        ORDER BY timestamp
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        raise ValueError("No data found in anomaly_results.")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).copy()

    return df


# =========================
# WINDOW SELECTION
# =========================
def select_best_window(df: pd.DataFrame, window_days: int = 7) -> pd.DataFrame:
    """
    Select a time window with the highest number of anomalies.
    This makes the figure more informative than plotting the entire timeline.
    """
    df = df.sort_values("timestamp").copy()

    anomaly_df = df[df["is_anomaly"] == 1].copy()
    if anomaly_df.empty:
        return df.tail(500).copy()

    start_time = df["timestamp"].min()
    end_time = df["timestamp"].max()

    best_count = -1
    best_start = start_time
    best_end = start_time + pd.Timedelta(days=window_days)

    current_start = start_time

    while current_start <= end_time:
        current_end = current_start + pd.Timedelta(days=window_days)
        count = anomaly_df[
            (anomaly_df["timestamp"] >= current_start) &
            (anomaly_df["timestamp"] < current_end)
        ].shape[0]

        if count > best_count:
            best_count = count
            best_start = current_start
            best_end = current_end

        current_start += pd.Timedelta(days=1)

    window_df = df[
        (df["timestamp"] >= best_start) &
        (df["timestamp"] < best_end)
    ].copy()

    if window_df.empty:
        return df.tail(500).copy()

    return window_df


# =========================
# PLOT
# =========================
def plot_example_anomaly_output(df: pd.DataFrame, output_path: Path) -> None:
    """
    Plot a cleaner anomaly figure using a selected time window
    with the highest density of anomalies.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # -------------
    # set days here 
    # -------------

    plot_df = df[df["timestamp"] >= (df["timestamp"].max() - pd.Timedelta(days=3))].copy()
    anomaly_df = plot_df[plot_df["is_anomaly"] == 1].copy()

    plt.figure(figsize=(12, 6))

    # Main metric line
    plt.plot(
        plot_df["timestamp"],
        plot_df["net_sent_delta_mb"],
        linewidth=1.2,
        alpha=0.85,
        label="Network sent delta"
    )

    # Highlight anomalies
    if not anomaly_df.empty:
        plt.scatter(
            anomaly_df["timestamp"],
            anomaly_df["net_sent_delta_mb"],
            s=40,
            alpha=0.95,
            label="Flagged anomalies"
        )

    plt.title("Example Anomaly Output")
    plt.xlabel("Timestamp")
    plt.ylabel("Network Sent Delta (MB)")
    plt.legend()

    if not anomaly_df.empty:
        start_label = plot_df["timestamp"].min().strftime("%Y-%m-%d")
        end_label = plot_df["timestamp"].max().strftime("%Y-%m-%d")

        note = (
            f"Selected {start_label} to {end_label} to show a representative period "
            f"with concentrated flagged anomalies."
        )
    else:
        note = "No flagged anomalies were available in the selected plotting window."

    plt.figtext(
        0.5,
        0.01,
        note,
        ha="center",
        fontsize=10,
        style="italic"
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(output_path, dpi=300)
    plt.show()

    print(f"Figure saved to: {output_path}")


# =========================
# MAIN
# =========================
def main():
    df = load_anomaly_data(DB_PATH)
    plot_example_anomaly_output(df, OUTPUT_PATH)


if __name__ == "__main__":
    main()