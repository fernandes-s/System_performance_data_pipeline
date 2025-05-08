# 🖥️ System Performance Data Pipeline

This project collects real-time system performance metrics — including CPU and memory usage — and stores them in a SQLite database. It then visualizes the data using an interactive dashboard built with Dash (Plotly).

---

## 🔧 Features

- ✅ Collects CPU and memory usage every minute using `psutil`
- ✅ Stores data in a persistent SQLite database
- ✅ Visualizes performance trends in a browser-based dashboard
- ✅ Refreshes dashboard automatically every 60 seconds
- ✅ Easy to set up and run locally

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

These graphs refresh every 60 seconds and help visualize your system's resource usage trends.

---

## 💡 Possible Extensions

Here are some ideas to expand this project:

- 📦 Add additional metrics like disk usage or network activity
- 🧼 Implement data cleaning or outlier detection before plotting
- ☁️ Deploy the dashboard using platforms like Render or Streamlit Cloud
- ⚠️ Set up alerts for high CPU or memory usage
- 🧪 Export data to CSV or integrate with external monitoring tools

---

## 🧑‍💻 Author

**Daniel Fernandes**  
[GitHub](https://github.com/fernandes-s)  
[LinkedIn](https://linkedin.com/in/fernandesss-s)

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

