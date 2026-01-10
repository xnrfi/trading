import sqlite3
from flask import Flask, render_template_string

app = Flask(__name__)

DB_PATH = "balance.db"

@app.route('/')
def home():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT date, total_value FROM balances ORDER BY date")
    data = cursor.fetchall()
    conn.close()
    
    dates = [row[0] for row in data]
    values = [row[1] for row in data]
    
    html = """
    <!DOCTYPE html>
    <html><head><title>Lighter Performance</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>body{background:#111;color:#eee;text-align:center;padding:40px;font-family:Arial}
    .box{background:#222;padding:30px;border-radius:15px;max-width:900px;margin:auto}</style>
    </head><body>
    <div class="box">
    <h1>Lighter Main Account Performance</h1>
    <h2>Current: ${{ "%.2f" % values[-1] }} USDC ({{ dates[-1] }})</h2>
    <canvas id="c" height="400"></canvas>
    </div>
    <script>
    new Chart(document.getElementById('c'), {
      type: 'line',
      data: {labels: {{ dates|tojson }}, datasets: [{label: 'Total Value (USDC)', data: {{ values|tojson }}, borderColor: '#4bc0c0', fill: true, tension: 0.3}]},
      options: {responsive: true}
    });
    </script>
    </body></html>
    """
    return render_template_string(html, dates=dates, values=values)

if __name__ == "__main__":
    app.run()
