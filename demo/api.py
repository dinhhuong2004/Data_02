# api.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
import requests

app = FastAPI()

CLICKHOUSE_URL = "http://localhost:8123/"
AUTH = ("admin", "admin123")

def query_clickhouse(sql: str):
    response = requests.get(
        CLICKHOUSE_URL,
        params={"query": sql + " FORMAT JSON"},
        auth=AUTH,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["data"]

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Login KPI</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #15181d;
      --muted: #657080;
      --line: #d9dee7;
      --blue: #2563eb;
      --green: #0f9f6e;
      --orange: #d97706;
      --red: #dc2626;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 24px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1 { margin: 0; font-size: 20px; font-weight: 700; }
    .status { color: var(--muted); font-size: 13px; }
    main {
      width: min(1280px, 100%);
      margin: 0 auto;
      padding: 20px;
    }
    .kpis {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 16px;
    }
    .kpi, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .kpi { padding: 16px; }
    .label { color: var(--muted); font-size: 13px; }
    .value { margin-top: 6px; font-size: 30px; font-weight: 750; }
    .grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 14px;
    }
    .panel { padding: 16px; min-width: 0; }
    .panel h2 { margin: 0 0 12px; font-size: 15px; }
    canvas { display: block; width: 100%; height: 300px; }
    @media (max-width: 1100px) {
      .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 860px) {
      .kpis, .grid { grid-template-columns: 1fr; }
      header { align-items: flex-start; flex-direction: column; gap: 6px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Login KPI</h1>
    <div class="status" id="status">Loading</div>
  </header>
  <main>
    <section class="kpis">
      <div class="kpi"><div class="label">DAU — Today</div><div class="value" id="dau">0</div></div>
      <div class="kpi"><div class="label">Total Logins — Last 30 Minutes</div><div class="value" id="totalLogins">0</div></div>
      <div class="kpi"><div class="label">Unique Users — Last 30 Minutes</div><div class="value" id="uniqueUsers">0</div></div>
      <div class="kpi"><div class="label">Logins — Last 5 Minutes</div><div class="value" id="last5m">0</div></div>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>Logins Per Minute</h2>
        <canvas id="minuteChart" width="900" height="300"></canvas>
      </div>
      <div class="panel">
        <h2>By Account Type</h2>
        <canvas id="accTypeChart" width="420" height="300"></canvas>
      </div>
      <div class="panel">
        <h2>By Location</h2>
        <canvas id="locationChart" width="900" height="300"></canvas>
      </div>
      <div class="panel">
        <h2>Top Locations</h2>
        <canvas id="topLocationChart" width="420" height="300"></canvas>
      </div>
    </section>
  </main>
  <script>
    const colors = ["#2563eb", "#0f9f6e", "#d97706", "#dc2626", "#7c3aed", "#0891b2", "#4d7c0f"];

    async function getJson(url) {
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) throw new Error(`${url}: ${response.status}`);
      return response.json();
    }

    function formatNumber(value) {
      return Number(value || 0).toLocaleString("en-US");
    }

    function clear(ctx, canvas) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    function drawAxes(ctx, width, height, padding) {
      ctx.strokeStyle = "#d9dee7";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padding.left, padding.top);
      ctx.lineTo(padding.left, height - padding.bottom);
      ctx.lineTo(width - padding.right, height - padding.bottom);
      ctx.stroke();
    }

    function drawLineChart(canvas, rows, xKey, yKey) {
      const ctx = canvas.getContext("2d");
      clear(ctx, canvas);
      const padding = { left: 54, right: 18, top: 16, bottom: 42 };
      const width = canvas.width;
      const height = canvas.height;
      drawAxes(ctx, width, height, padding);

      if (!rows.length) return;

      const maxY = Math.max(...rows.map(row => Number(row[yKey] || 0)), 1);
      const plotW = width - padding.left - padding.right;
      const plotH = height - padding.top - padding.bottom;

      ctx.strokeStyle = "#2563eb";
      ctx.lineWidth = 2;
      ctx.beginPath();
      rows.forEach((row, index) => {
        const x = padding.left + (rows.length === 1 ? 0 : index * plotW / (rows.length - 1));
        const y = height - padding.bottom - (Number(row[yKey] || 0) / maxY) * plotH;
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();

      ctx.fillStyle = "#2563eb";
      rows.forEach((row, index) => {
        const x = padding.left + (rows.length === 1 ? 0 : index * plotW / (rows.length - 1));
        const y = height - padding.bottom - (Number(row[yKey] || 0) / maxY) * plotH;
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      });

      ctx.fillStyle = "#657080";
      ctx.font = "12px sans-serif";
      ctx.fillText(String(maxY), 10, padding.top + 8);
      ctx.fillText("0", 22, height - padding.bottom + 4);
      const first = rows[0][xKey].slice(11, 16);
      const last = rows[rows.length - 1][xKey].slice(11, 16);
      ctx.fillText(first, padding.left, height - 14);
      ctx.textAlign = "right";
      ctx.fillText(last, width - padding.right, height - 14);
      ctx.textAlign = "left";
    }

    function drawBarChart(canvas, rows, labelKey, valueKey, limit = 12) {
      const ctx = canvas.getContext("2d");
      clear(ctx, canvas);
      const data = rows.slice(0, limit);
      const padding = { left: 48, right: 12, top: 14, bottom: 52 };
      const width = canvas.width;
      const height = canvas.height;
      drawAxes(ctx, width, height, padding);
      if (!data.length) return;

      const maxY = Math.max(...data.map(row => Number(row[valueKey] || 0)), 1);
      const plotW = width - padding.left - padding.right;
      const plotH = height - padding.top - padding.bottom;
      const gap = 8;
      const barW = Math.max(8, (plotW - gap * (data.length - 1)) / data.length);

      ctx.font = "12px sans-serif";
      data.forEach((row, index) => {
        const value = Number(row[valueKey] || 0);
        const barH = (value / maxY) * plotH;
        const x = padding.left + index * (barW + gap);
        const y = height - padding.bottom - barH;
        ctx.fillStyle = colors[index % colors.length];
        ctx.fillRect(x, y, barW, barH);
        ctx.fillStyle = "#657080";
        ctx.textAlign = "center";
        ctx.fillText(String(row[labelKey]), x + barW / 2, height - 30);
      });
      ctx.textAlign = "left";
      ctx.fillText(String(maxY), 8, padding.top + 8);
    }

    async function refresh() {
      const [summary, perMinute, byLocation, byAccType] = await Promise.all([
        getJson("/kpi/summary"),
        getJson("/kpi/logins-per-minute"),
        getJson("/kpi/by-location"),
        getJson("/kpi/by-acc-type"),
      ]);

      dau.textContent = formatNumber(summary.dau);
      totalLogins.textContent = formatNumber(summary.total_logins);
      uniqueUsers.textContent = formatNumber(summary.unique_users);
      last5m.textContent = formatNumber(summary.logins_last_5m);

      drawLineChart(minuteChart, perMinute, "minute", "login_count");
      drawBarChart(locationChart, byLocation, "location_id", "login_count", 18);
      drawBarChart(topLocationChart, byLocation, "location_id", "login_count", 8);
      drawBarChart(accTypeChart, byAccType, "acc_type", "login_count", 5);

      status.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    }

    refresh().catch(error => {
      status.textContent = error.message;
      console.error(error);
    });
    setInterval(() => refresh().catch(console.error), 5000);
  </script>
</body>
</html>
"""

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/kpi/summary")
def summary():
    sql = """
    SELECT
      uniqExact(userid)                                               AS dau,
      countIf(event_time >= now() - INTERVAL 30 MINUTE)              AS total_logins,
      uniqExactIf(userid, event_time >= now() - INTERVAL 30 MINUTE)  AS unique_users,
      countIf(event_time >= now() - INTERVAL 5 MINUTE)               AS logins_last_5m
    FROM realtime.login_events
    WHERE toDate(event_time, 'UTC') = today()
    """
    return query_clickhouse(sql)[0]

@app.get("/kpi/logins-per-minute")
def logins_per_minute():
    sql = """
    SELECT
      toStartOfMinute(event_time) AS minute,
      count() AS login_count
    FROM realtime.login_events
    WHERE event_time >= now() - INTERVAL 1 HOUR
    GROUP BY minute
    ORDER BY minute
    """
    return query_clickhouse(sql)

@app.get("/kpi/by-location")
def by_location():
    sql = """
    SELECT
      location_id,
      count() AS login_count
    FROM realtime.login_events
    WHERE event_time >= now() - INTERVAL 30 MINUTE
    GROUP BY location_id
    ORDER BY login_count DESC
    """
    return query_clickhouse(sql)

@app.get("/kpi/by-acc-type")
def by_acc_type():
    sql = """
    SELECT
      acc_type,
      count() AS login_count
    FROM realtime.login_events
    WHERE event_time >= now() - INTERVAL 30 MINUTE
    GROUP BY acc_type
    ORDER BY acc_type
    """
    return query_clickhouse(sql)
