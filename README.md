<div align="center">
  <h1>🖥️ System Performance Data Pipeline</h1>
</div>


This project collects system performance metrics — CPU, memory, disk, and network usage — every 5 minutes and stores them in a local SQLite database. The data is exported daily and visualized in an interactive Dash app with optional dark mode and live updates.

---

## 🔧 Features

- ✅ Collects CPU, memory, disk, and network usage using `psutil`
- ✅ Stores data in a persistent SQLite database
- ✅ Exports daily CSV files with performance metrics
- ✅ Visualizes trends in a web-based dashboard
- ✅ Filters by date and hour range
- ✅ Auto-refresh every 60 seconds
- ✅ Supports dark mode toggle
- ✅ Deployable on [Render](https://render.com/)
- ✅ Automatically pushes changes to GitHub daily (optional)


---

## 📁 Project Structure

```
system-performance-pipeline/
├── daily_metrics/         # Folder storing daily CSV exports (one file per day)
├── task_scheduler/        # Folder with .xml files for Task Scheduler automation (collect, export, auto-push)
├── app.py                 # Dash app for the live dashboard (with dark mode, filters, etc.)
├── collect_metrics.py     # Collects real-time system metrics and inserts them into the SQLite database
├── create_db.py           # Initializes the SQLite database and creates the `metrics` table
├── export_daily.py        # Exports all metrics from today into a CSV file (stored in daily_metrics/)
├── LICENSE                # Project license (MIT)
├── README.md              # Project documentation
├── render.yaml            # Render deployment configuration file
├── requirements.txt       # Python dependencies needed to run the project
├── system_metrics.db      # SQLite database file that stores all collected metrics
└── view_db.py             # Utility script to view data from the database as a DataFrame
         
```
---


## 📊 Metrics collected 

> **CPU Graph**  
> Displays CPU usage (%) over time with a live line chart.

> **Memory Graph**  
> Displays memory usage (%) over time with a live line chart.

> **Disk Usage Graph**  
> Shows disk usage percentage, helping monitor storage capacity.

> **Network I/O Graph**  
> Visualizes sent and received bytes, giving insight into network activity.

These graphs refresh automatically every 5 minutes and include a time-range filter (1h, 2h, 4h, 6h, 8h, 12h, 24h), as well as dates in the calendar for real-time and historical insights.



---
---
---



## ▶️ How to Run
### 🖥️ Option 1: Run Locally and Collect Your Own Metrics

You can run this dashboard on your own machine and collect metrics every 5 minutes using Task Scheduler.

#### 🔨 Clone the Repository
```bash
git clone https://github.com/fernandes-s/System_performance_data_pipeline.git
cd System_performance_data_pipeline
```

#### ✅ Requirements
Make sure you have Python 3.9+ installed. Then run:
```bash
pip install -r requirements.txt
```

#### 🗃️ 3. Initialize the Database
```bash
python create_db.py
```

#### 📅 4. Set Up Task Scheduler (Windows)
Two automated tasks are needed:
- `collect_metrics.xml` - Collects real-time metrics every 5 minutes
- `export_daily.xml` - Exports daily metrics into CSV at 23:55   

###### ✅ How to Set Up
1. Open Task Scheduler
2. Click Import Task
3. Import the ```.xml``` files found in the ```task_scheduler/``` folder.
4. Set the correct path to ```collect_metrics.py``` and ```export_daily.py``` if your folder is located elsewhere.
5. Automatic daily updates with ```auto_git_push.py``` are optinal but encouraged (same process for previous tasks).
6. Enable both tasks.
⏰ Now your system will collect data and export it automatically.

#### 🌐 5. Run the Dashboard Locally in the CLI
```bash
python app.py
```
Then open your browser and go to:
```bash
http://127.0.0.1:8050
```


---

### ☁️ Option 2: Deploy Online with Render

If you'd prefer to host the dashboard online:

#### 🚀 1. Fork This Repository
Simply fork this repository to your own GitHub account:
```bash
https://github.com/fernandes-s/System_performance_data_pipeline
```
No need to clone or push anything — just fork and connect it to Render.

#### ⚙️ 2. Create a Web Service on Render
1. Go to https://render.com and log in.
2. Click New Web Service
3. Connect your GitHub and select your repository.
4. Use the following settings:
    - Environment: Python 3
    - Build Command: ```pip install -r requirements.txt```
    - Start Command: ```python app.py```
    - Port: 10000 (set in ```app.py```)
    - Runtime: ```render.yaml``` handles deployment configs.
Once deployed, Render will give you a public URL like:
```bash
https://system-performance-data-pipeline.onrender.com
```
Note: The online version will only visualize static or uploaded ```.csv ``` files from the ```daily_metrics/``` folder. To get live updates, you'll need to push metrics manually or sync with cloud storage.

---



## 🛠️ Troubleshooting & Tips

- **Graphs not updating?**  
  Ensure that `collect_metrics.py` is running every 5 minutes (Task Scheduler must be active) and that your system clock is accurate.

- **Dashboard resets time range or dark mode on refresh?**  
  The current version does not persist user settings across refreshes. This could be improved by integrating `dcc.Store` or browser cookies to save state.

- **File Not Found Errors?**  
  Make sure the scripts (`collect_metrics.py`, `export_daily.py`) and the SQLite database are in the correct relative paths when importing tasks in Task Scheduler or when deploying.

- **Deployment on Render is stuck or fails?**  
  Double-check that your repository includes:
  - A valid `requirements.txt`
  - A working `render.yaml` file
  - Correct port configuration (your `app.py` should have `port=10000`)

---

<div align="center">

# ⭐️ If You Found This Useful

If you like this project, consider giving the repository a ⭐️ on GitHub!  
It helps others discover it and encourages further improvements.

</div>


---

## 🧑‍💻 Author

**Daniel Fernandes**  
[GitHub](https://github.com/fernandes-s)  
[LinkedIn](https://linkedin.com/in/fernandesss-s)

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

