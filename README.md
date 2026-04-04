# System Performance Data Pipeline

A Python-based system monitoring and anomaly detection project that collects performance metrics, stores them in SQLite, exports daily snapshots, and presents the results through a Streamlit dashboard.

## Project Overview

This project was built as a final year computing project to demonstrate the design of a small end-to-end data pipeline for system monitoring. It automates the collection of system metrics, stores the data locally, prepares it for analysis, and applies anomaly detection to identify unusual behaviour in system performance over time.

The project combines data collection, storage, preprocessing, modelling, and dashboarding in one workflow.

## Features

- Automated system metric collection
- SQLite database storage
- Daily metric exports to CSV
- Data cleaning and preprocessing pipeline
- Isolation Forest anomaly detection
- Streamlit dashboard for monitoring and analysis
- Modular project structure for easier maintenance and extension

## Metrics Collected

The pipeline currently collects the following system-level metrics:

- CPU usage percentage
- Memory usage percentage
- Disk usage percentage
- Total network sent (MB)
- Total network received (MB)
- Network sent delta between collections (MB)
- Network received delta between collections (MB)
- System uptime in seconds
- Timestamp for each reading

## Project Structure

```text
System_performance_data_pipeline/
├── app/
│   ├── main.py
│   ├── utils/
│   │   ├── db.py
│   │   └── helpers.py
│   └── pages/
│       ├── anomalies.py
│       ├── model_diagnostics.py
│       └── system_info.py
├── artifacts/
│   └── models/
│       ├── isolation_forest_model.joblib
│       └── scaler.joblib
├── data/
│   ├── exports/
│   └── raw/
│       └── system_metrics.db
├── notebooks/
├── scripts/
│   ├── collect_metrics.py
│   ├── create_db.py
│   ├── db_checker.py
│   ├── export_daily.py
│   └── quick_db_test.py
├── src/
│   └── models/
│       ├── anomaly_model.py
│       ├── preprocessing.py
│       └── train_model.py
├── requirements.txt
└── README.md
```

## How the Pipeline Works

### 1. Data Collection

The pipeline collects system performance metrics at regular intervals using Python. These metrics are gathered from the local machine and inserted into a SQLite database.

### 2. Data Storage

Collected metrics are stored in the `metrics` table inside `data/raw/system_metrics.db`. SQLite was used because it is lightweight, simple to manage, and suitable for a local monitoring project.

### 3. Daily Export

A daily export script saves collected metrics into CSV format for backup and external analysis.

### 4. Data Preprocessing

Before modelling, the data is cleaned and filtered to remove missing values, unrealistic values, and invalid network readings.

### 5. Anomaly Detection

The project uses an Isolation Forest model to identify unusual system behaviour. The model is trained on historical system metrics and saves anomaly results back into the database.

### 6. Dashboarding

A Streamlit dashboard displays key metrics, trends, and anomaly-related information in an interactive format.

## Technologies Used

- Python
- SQLite
- Pandas
- Scikit-learn
- Joblib
- Streamlit
- Psutil
- Plotly

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

## How to Run the Project

### Step 1: Create the database

```bash
python scripts/create_db.py
```

### Step 2: Collect system metrics

```bash
python scripts/collect_metrics.py
```

This script can also be scheduled to run automatically at fixed intervals using Task Scheduler.

### Step 3: Export daily metrics

```bash
python scripts/export_daily.py
```

### Step 4: Train the anomaly detection model

```bash
python src/models/train_model.py
```

### Step 5: Run the dashboard

```bash
streamlit run app/main.py
```

## Dashboard Pages

### Main Dashboard

The main dashboard provides a high-level overview of the latest system activity and recent trends.

### Anomalies Page

The anomalies page is intended to show unusual system behaviour and anomaly-related summaries.

### System Info Page

This page focuses on data collection consistency, database records, and system monitoring information.

### Model Diagnostics Page

This page is used to inspect model-related results, anomaly scoring behaviour, and supporting diagnostics.

## Current Stage of the Project

The project currently includes:

- working metric collection
- local SQLite storage
- export functionality
- preprocessing and anomaly detection code
- saved model artefacts
- a multi-page Streamlit dashboard structure

The project is currently in the final integration and presentation stage. The main remaining work is focused on polishing, aligning documentation with the latest codebase, and making sure all dashboard pages are fully connected to real model outputs.

## Challenges Faced

Some of the main challenges in the project included:

- designing a clean project structure as the project expanded
- managing paths across scripts, app pages, and data folders
- handling network counter resets and invalid values
- moving from a simple dashboard to a modular multi-page app
- integrating machine learning output into a monitoring dashboard

## Future Improvements

Possible improvements for the project include:

- connecting all dashboard pages directly to final model outputs
- adding more robust evaluation metrics for anomaly detection
- improving model explainability
- adding automated tests
- deploying the dashboard online
- storing model metadata and training logs
- adding alerting functionality for critical anomalies

## Learning Outcomes

This project helped develop skills in:

- data pipeline design
- data collection and automation
- database handling with SQLite
- preprocessing and feature preparation
- anomaly detection with machine learning
- dashboard development with Streamlit
- structuring and documenting a complete technical project

## Author

Daniel Fernandes

## Repository

This project is available on GitHub:

`https://github.com/fernandes-s/System_performance_data_pipeline`
