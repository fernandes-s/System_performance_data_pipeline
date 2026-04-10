from pathlib import Path
import sqlite3

import pandas as pd
import matplotlib.pyplot as plt


# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"
OUTPUT_PATH = BASE_DIR / "artifacts" / "figures" / "figure_5_anomaly_score_distribution.png"


# =========================
# LOAD DATA
# =========================
def load_anomaly_scores(db_path: Path) -> pd.DataFrame:
    """
    Load anomaly scores and anomaly strength labels from SQLite.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)

    query = """
        SELECT
            anomaly_score,
            anomaly_strength
        FROM anomaly_results
        WHERE anomaly_score IS NOT NULL
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        raise ValueError("No anomaly scores found in anomaly_results table.")

    return df


# =========================
# THRESHOLD EXTRACTION
# =========================
def get_strength_thresholds(df: pd.DataFrame) -> dict:
    """
    Estimate score thresholds from the anomaly_strength labels.

    Since lower Isolation Forest scores indicate more unusual observations,
    the maximum score inside each category can be used as the boundary line
    for that category.

    Returns a dictionary such as:
    {
        "weak": value,
        "moderate": value,
        "strong": value
    }
    """
    thresholds = {}

    for label in ["weak", "moderate", "strong"]:
        subset = df[df["anomaly_strength"].str.lower() == label]
        if not subset.empty:
            thresholds[label] = subset["anomaly_score"].max()

    return thresholds


# =========================
# PLOT
# =========================
def plot_anomaly_score_distribution(df: pd.DataFrame, output_path: Path) -> None:
    """
    Plot histogram of anomaly scores with threshold lines for
    weak, moderate, and strong anomalies where available.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    thresholds = get_strength_thresholds(df)

    plt.figure(figsize=(10, 6))
    plt.hist(df["anomaly_score"], bins=40, edgecolor="black")

    # Threshold lines
    if "weak" in thresholds:
        plt.axvline(
            thresholds["weak"],
            linestyle="--",
            linewidth=2,
            label=f"Weak threshold ({thresholds['weak']:.3f})"
        )

    if "moderate" in thresholds:
        plt.axvline(
            thresholds["moderate"],
            linestyle="--",
            linewidth=2,
            label=f"Moderate threshold ({thresholds['moderate']:.3f})"
        )

    if "strong" in thresholds:
        plt.axvline(
            thresholds["strong"],
            linestyle="--",
            linewidth=2,
            label=f"Strong threshold ({thresholds['strong']:.3f})"
        )

    plt.title("Distribution of Anomaly Scores")
    plt.xlabel("Anomaly Score")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.show()

    print(f"Figure saved to: {output_path}")


# =========================
# MAIN
# =========================
def main():
    df = load_anomaly_scores(DB_PATH)
    plot_anomaly_score_distribution(df, OUTPUT_PATH)


if __name__ == "__main__":
    main()