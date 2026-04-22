# System Performance Data Pipeline

A Python-based end-to-end monitoring project that collects system performance metrics, stores them in a SQLite database, applies anomaly detection to identify unusual behaviour, and presents the results through an interactive Streamlit dashboard.

---

## Project Overview

This project was developed as a final-year computing project to demonstrate the design and implementation of a small but complete data pipeline for system monitoring.

The pipeline automates the collection of system-level performance data, stores it locally, prepares it for analysis, applies an unsupervised anomaly detection model, and displays both historical trends and anomaly-related insights in a dashboard.

Rather than focusing only on visualisation or only on machine learning, the project combines data collection, storage, preprocessing, modelling, persistence of outputs, and dashboard integration in one workflow.

---

## Objectives

The main objectives of the project were to:

- collect system performance data automatically at regular intervals
- store the data in a structured local database
- export daily snapshots for backup and external analysis
- clean and prepare the data for modelling
- detect unusual system behaviour using anomaly detection
- build an interactive dashboard to support monitoring and interpretation
- demonstrate a practical end-to-end data pipeline using Python

---

## Key Features

- Automated system metric collection using Python and `psutil`
- Local storage of raw metrics in SQLite
- Daily CSV export of collected records
- Data cleaning and preprocessing pipeline
- Isolation Forest anomaly detection model
- Saved model artefacts using `joblib`
- Anomaly results written back into the database
- Multi-page Streamlit dashboard for monitoring and analysis
- Modular project structure for maintainability and extension

---

## Metrics Collected

The pipeline collects the following system-level metrics:

- CPU usage percentage
- Memory usage percentage
- Disk usage percentage
- Total network sent (MB)
- Total network received (MB)
- Network sent delta between collections (MB)
- Network received delta between collections (MB)
- System uptime in seconds
- Timestamp of each reading

---

## Project Structure

```text
System_performance_data_pipeline/
├── app/                     # Streamlit dashboard application
│   ├── main.py
│   ├── pages/
│   │   ├── anomalies.py
│   │   ├── model_diagnostics.py
│   │   └── system_info.py
│   └── utils/
│       ├── __init__.py
│       ├── anomaly.py
│       ├── charts.py
│       ├── config.py
│       ├── db.py
│       ├── formatters.py
│       ├── metrics.py
│       ├── queries.py
│       └── ui_helpers.py
├── artifacts/
│   └── models/
│       ├── isolation_forest_model.joblib
│       └── scaler.joblib
├── data/
│   ├── daily_exports/       # Generated CSV outputs
│   └── raw/                 # Source database
│       └── system_metrics.db
├── scripts/                 # Operational scripts and automation
│   ├── auto_git_push.py
│   ├── collect_metrics.py
│   ├── create_db.py
│   ├── db_checker.py
│   ├── export_daily.py
│   └── view_db.py
├── src/
│   └── models/
│       ├── anomaly_model.py
│       ├── preprocessing.py
│       └── train_model.py
├── task_scheduler/          # Windows Task Scheduler configurations
│   ├── auto_git_push.xml
│   ├── CollectSystemMetrics.xml
│   └── ExportDailyMetrics.xml
├── requirements.txt
└── README.md
```
---

## How the Pipeline Works

### 1. Data Collection

System performance metrics are collected from the local machine using Python. The collection process captures real-time measurements such as CPU usage, memory usage, disk usage, network traffic, and system uptime.

### 2. Data Storage

The collected metrics are stored in a SQLite database located at:

text
data/raw/system_metrics.db
```

The main raw data is stored in the `metrics` table. SQLite was selected because it is lightweight, portable, and appropriate for a local monitoring pipeline.

### 3. Daily Export

A daily export script saves collected records into CSV format. This provides a simple backup mechanism and also allows the data to be reviewed outside the dashboard or database environment.

### 4. Data Preprocessing

Before training the model, the raw data is cleaned and filtered. This stage includes:

- timestamp filtering
- removal of missing values
- handling of invalid or unrealistic metric ranges
- filtering of problematic network readings
- removal of selected outliers

This step is important because raw monitoring data can contain noise and misleading values that reduce the quality of anomaly detection.

### 5. Anomaly Detection

The project uses an Isolation Forest model to identify observations that behave differently from the normal system pattern.

The modelling pipeline includes:

- feature selection
- scaling with `StandardScaler`
- anomaly scoring
- classification of records as normal or anomalous
- saving model artefacts for reuse
- writing anomaly results back into SQLite

Because this is an unsupervised anomaly detection task, the model is used to highlight unusual system behaviour rather than to make supervised accuracy claims.

### 6. Dashboard Integration

The final stage of the pipeline is a Streamlit dashboard that presents:

- system performance trends
- recent metric behaviour
- anomaly summaries
- model diagnostics
- supporting system and database information

This allows the project to move from raw collected data to an interpretable user-facing monitoring tool.

---

## Dashboard Pages

### Main Dashboard

The main dashboard provides a high-level overview of the dataset and recent system activity. It is designed to summarise the current state of the pipeline and recent trends in key metrics.

### Anomalies Page

The anomalies page focuses on records flagged by the anomaly detection pipeline. It helps users inspect unusual behaviour and review anomaly-related summaries from the stored model results.

### System Info Page

The system info page presents supporting operational information such as latest readings, environment details, and pipeline-related monitoring context.

### Model Diagnostics Page

The model diagnostics page is used to inspect saved model artefacts, anomaly score behaviour, and supporting details related to the modelling stage.

---

## Technologies Used

- Python
- SQLite
- Pandas
- Scikit-learn
- Joblib
- Streamlit
- Plotly
- Psutil

---

## Installation

Clone the repository:

```bash
git clone https://github.com/fernandes-s/System_performance_data_pipeline.git
cd System_performance_data_pipeline
```

Install the required packages:

```bash
pip install -r requirements.txt
```

---

## How to Run the Project

### Step 1: Create the database

```bash
python scripts/create_db.py
```

### Step 2: Collect system metrics

```bash
python scripts/collect_metrics.py
```

This script can also be scheduled to run automatically at fixed intervals using Windows Task Scheduler.

### Step 3: Export daily metrics

```bash
python scripts/export_daily.py
```

### Step 4: Train the anomaly detection model

```bash
python src/models/train_model.py
```

This step cleans the data, builds the feature matrix, scales the selected features, trains the Isolation Forest model, saves the model artefacts, and writes anomaly results into the database.

### Step 5: Launch the dashboard

```bash
streamlit run app/main.py
```

---

## Outputs Generated

The project produces several outputs during execution:

- raw system metrics stored in SQLite
- daily CSV export files
- trained model artefacts in `artifacts/models/`
- anomaly detection results saved to the database
- interactive dashboard views for monitoring and interpretation

---

## Design Decisions

A number of design choices were made to keep the project practical, lightweight, and easy to maintain:

- **SQLite** was chosen for simple local storage without requiring a separate database server.
- **Streamlit** was used to build a fast and clear dashboard interface.
- **Isolation Forest** was selected because it is suitable for unsupervised anomaly detection where labelled anomaly data is not available.
- **Modular file structure** was used to separate data collection, preprocessing, modelling, and dashboard logic.
- **Saved model artefacts** were included to support reuse and reproducibility.

---

## Limitations

This project has some important limitations:

- the anomaly detection model is unsupervised, so flagged anomalies are unusual observations rather than confirmed faults
- the project is designed for local system monitoring and does not currently support distributed monitoring across multiple machines
- system behaviour can vary depending on usage patterns, meaning anomaly results should always be interpreted in context
- the project does not use labelled ground truth data for formal supervised evaluation

These limitations are expected in a project of this scope and were considered as part of the design.

---

## Future Improvements

Possible future improvements include:

- support for monitoring multiple machines
- configurable collection intervals through a settings file
- automated alerting for high-risk anomalies
- improved feature engineering for model performance
- stronger model comparison across multiple unsupervised methods
- deployment of the dashboard and pipeline in a cloud environment

---

## Conclusion

This project demonstrates the design of a complete data pipeline for local system performance monitoring. It moves from raw metric collection to storage, preprocessing, anomaly detection, and dashboard presentation in one integrated workflow.

The main value of the project is not only the anomaly model itself, but the full pipeline that supports data collection, analysis, persistence of outputs, and interpretation through an accessible dashboard.

---

## Author

**Daniel Fernandes**
BSc (Hons) Computing Big Data & Data Analytics
