import sqlite3
import json
from datetime import datetime
import subprocess
import os

# Database path
DB_PATH = "balance.db"

# HTML output path
HTML_PATH = "index.html"

# GitHub repo path (your folder)
REPO_PATH = "/home/xenner/tracking"

def extract_data():
    """
    Extract dates and values from balance.db
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT date, total_value FROM balances ORDER BY date")
    data = cursor.fetchall()
    conn.close()
    
    if not data:
        print("No data in database")
        return [], []
    
    dates = [row[0] for row in data]
    values = [row[1] for row in data]
    return dates, values

def generate_chart_html(dates, values):
    """
    Generate a nice static HTML with Chart.js line chart
    """
    if not values:
        return
    
    current_date = dates[-1]
    current_value = values[-1]
    
    # JSON for Chart.js
    dates_json = json.dumps(dates)
    values_json = json.dumps(values)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lighter Account Performance - {current_date}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/bundle.min.js"></script>
    <style>
        body {{
            background: linear-gradient(to bottom right, #0f172a, #1e293b);
            color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            text-align: center;
            padding: 40px;
            margin: 0;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: rgba(30, 41, 59, 0.8);
            padding: 40px;
            border-radius: 24px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }}
        h1 {{
            font-size: 2.8em;
            margin-bottom: 0.5em;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        h2 {{
            font-size: 1.6em;
            color: #94a3b8;
            margin: 20px 0 40px;
            letter-spacing: 0.05em;
        }}
        canvas {{
            background: rgba(51, 65, 85, 0.6);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }}
        footer {{
            margin-top: 40px;
            color: #64748b;
            font-size: 0.9em;
            letter-spacing: 0.02em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Lighter Main Account Performance</h1>
        <h2>Current Value: ${current_value:,.2f} USDC <br><small>Updated {current_date}</small></h2>
        <canvas id="chart" height="400"></canvas>
        <footer>Auto-generated daily • Data sourced from Lighter.xyz API</footer>
    </div>
    <script>
        const ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {dates_json},
                datasets: [{{
                    label: 'Total Account Value (USDC)',
                    data: {values_json},
                    borderColor: 'rgb(34, 211, 238)',
                    backgroundColor: 'rgba(34, 211, 238, 0.2)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgb(34, 211, 238)',
                    pointBorderColor: 'rgb(15, 23, 42)',
                    pointRadius: 5,
                    pointHoverRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                interaction: {{ mode: 'index', intersect: false }},
                scales: {{
                    x: {{ grid: {{ color: 'rgba(148, 163, 184, 0.1)' }} }},
                    y: {{
                        beginAtZero: false,
                        grid: {{ color: 'rgba(148, 163, 184, 0.1)' }},
                        ticks: {{ callback: function(value) {{ return '$' + value.toLocaleString() }} }}
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{ label: function(ctx) {{ return '$' + ctx.raw.toLocaleString(undefined, {{minimumFractionDigits: 2}}) }} }},
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        titleColor: '#e2e8f0',
                        bodyColor: '#e2e8f0'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
    """

    with open(HTML_PATH, "w") as f:
        f.write(html_content)
    print(f"Generated {HTML_PATH}")

def git_push_update():
    try:
        # Commit and push HTML (optionally DB too)
        subprocess.check_call(["git", "add", HTML_PATH], cwd=REPO_PATH)
        subprocess.check_call(["git", "commit", "-m", f"Daily chart update {datetime.now().strftime('%Y-%m-%d')}"], cwd=REPO_PATH)
        subprocess.check_call(["git", "push"], cwd=REPO_PATH)
        print("Successfully pushed update to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"Git push failed: {e}")
        print("Run manually: cd ~/tracking && git add index.html && git commit -m 'update' && git push")

if __name__ == "__main__":
    # Extract data (assumes balance.db is updated)
    dates, values = extract_data()
    if not dates:
        print("No data - run fetch script first")
    else:
        generate_chart_html(dates, values)
        git_push_update()
