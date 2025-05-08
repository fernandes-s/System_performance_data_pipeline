# 🖥️ System Performance Data Pipeline

This project collects real-time system performance metrics — including CPU and memory usage — and stores them in a SQLite database. It then visualizes the data using an interactive dashboard built with Dash (Plotly).

---

## 🔧 Features

- ✅ Collects CPU, memory, disk, and network usage using `psutil`
- ✅ Stores data in a persistent SQLite database
- ✅ Visualizes performance trends in a browser-based dashboard
- ✅ Filters by time range (1h, 6h, 24h, All)
- ✅ Auto-refresh every 60 seconds
- ✅ Exports the latest data sample to `sample_metrics.csv` for portability
- ✅ Deployed and accessible online via Render

---

## 📁 Project Structure
```
system-performance-pipeline/
├── collect_metrics.py     
├── create_db.py            
├── dashboard.py            
├── requirements.txt        
└── README.md              
```
---

## ⚙️ Requirements

Install dependencies using:

```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run

### 🌐 Deployed Version
You can also access the live dashboard here:  
[https://system-performance-data-pipeline.onrender.com](https://system-performance-data-pipeline.onrender.com)

### 1. Set up the database:
```bash
python create_db.py
```

### 2. Start collecting system metrics
```bash
python collect_metrics.py
```

### 3. Launch the dashboard
```bash
python dashboard.py
```

### Open your browser and go to: 
```bash
http://127.0.0.1:8050
```
---

## 📊 Sample Output

> **CPU Graph**  
> Displays CPU usage (%) over time with a live line chart.

> **Memory Graph**  
> Displays memory usage (%) over time with a live line chart.

> **Disk Usage Graph**  
> Shows disk usage percentage, helping monitor storage capacity.

> **Network I/O Graph**  
> Visualizes sent and received bytes, giving insight into network activity.

These graphs refresh automatically every 60 seconds and include a time-range filter (1h, 6h, 24h, All) for real-time and historical insights.

---

## 💡 Possible Extensions

Here are some ideas to expand this project:

- 📈 Integrate rolling averages or smoothing for clearer trends
- 🔔 Set up alerts for high CPU, memory, or disk usage

---


## 🧑‍💻 Author

**Daniel Fernandes**  
[GitHub](https://github.com/fernandes-s)  
[LinkedIn](https://linkedin.com/in/fernandesss-s)

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

