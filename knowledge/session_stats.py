"""Session performance statistics for active bots."""

CATEGORY = "Monitoring"

import sqlite3
import time
from typing import Any
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pydantic import BaseModel, Field

INSTANCES_DIR = Path.home() / "hummingbot-api/bots/instances"

CLOSE_TYPES = {1: "TP", 2: "SL", 3: "TimeLimit", 4: "TrailingStop", 5: "EarlyStop"}
SESSIONS = [("Asia", 0, 8), ("Europe", 8, 15), ("USA", 15, 21), ("Night", 21, 24)]


class Config(BaseModel):
    """Session performance analytics for active bots."""
    min_filled_quote: float = Field(default=0.0, description="Min filled_amount_quote filter")


def _get_sqlite_files():
    return sorted(INSTANCES_DIR.glob("*/data/*.sqlite"))


def _read_executors(db_path):
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, close_type, net_pnl_quote, filled_amount_quote,
                   CAST(strftime('%H', datetime(timestamp, 'unixepoch')) AS INT) as hour
            FROM Executors WHERE filled_amount_quote > 0 AND close_type IS NOT NULL
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except:
        return []


def _session_name(hour):
    for name, start, end in SESSIONS:
        if start <= hour < end:
            return name
    return "Night"


def _analyze(rows):
    data = {}
    for r in rows:
        session = _session_name(r["hour"])
        ct = CLOSE_TYPES.get(r["close_type"], f"Type{r['close_type']}")
        key = (session, ct)
        if key not in data:
            data[key] = {"cnt": 0, "pnl": 0.0}
        data[key]["cnt"] += 1
        data[key]["pnl"] += r["net_pnl_quote"]
    return data


async def run(config: Config, context: Any = None) -> str:
    files = _get_sqlite_files()
    if not files:
        return "No SQLite files found"

    all_text = []
    all_tables = []
    all_figs = []
    session_order = ["Asia", "Europe", "USA", "Night"]
    ct_order = ["TP", "SL", "TimeLimit", "EarlyStop", "TrailingStop"]
    colors = {"TP": "#3fb950", "SL": "#f85149", "TimeLimit": "#58a6ff",
               "EarlyStop": "#d29922", "TrailingStop": "#bc8cff"}

    for db_path in files:
        bot_name = db_path.parent.parent.name
        rows = _read_executors(db_path)
        if not rows:
            continue

        stats = _analyze(rows)
        total_pnl = sum(r["net_pnl_quote"] for r in rows)
        total_cnt = len(rows)

        all_text.append(f"\n📊 {bot_name[-30:]}")
        all_text.append(f"   Total: {total_cnt} | PNL: {total_pnl:+.4f} USDT")

        for session in session_order:
            session_data = {ct: v for (s, ct), v in stats.items() if s == session}
            if not session_data:
                continue
            s_pnl = sum(v["pnl"] for v in session_data.values())
            s_cnt = sum(v["cnt"] for v in session_data.values())
            all_text.append(f"   [{session}] {s_cnt} | {s_pnl:+.4f} USDT")
            for ct in ct_order:
                if ct in session_data:
                    v = session_data[ct]
                    all_text.append(f"      {ct:12s} x{v['cnt']:3d}  {v['pnl']:+.4f}")
            for session in session_order:
                for ct in ct_order:
                    v = stats.get((session, ct))
                    if v:
                        all_tables.append({"Bot": bot_name[-20:], "Session": session,
                                           "Type": ct, "Count": v["cnt"], "PNL": f"{v['pnl']:+.4f}"})

        fig = make_subplots(rows=1, cols=1)
        for ct in ct_order:
            x_vals, y_vals = [], []
            for session in session_order:
                v = stats.get((session, ct))
                if v:
                    x_vals.append(session)
                    y_vals.append(round(v["pnl"], 4))
            if x_vals:
                fig.add_trace(go.Bar(name=ct, x=x_vals, y=y_vals,
                    marker_color=colors.get(ct, "#8b949e"),
                    text=[f"{v:+.4f}" for v in y_vals], textposition="outside"))
        fig.update_layout(title=f"PNL by Session — {bot_name[-25:]}",
            barmode="group", paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
            font=dict(color="#e6edf3"),
            yaxis=dict(gridcolor="#30363d", zeroline=True, zerolinecolor="#58a6ff"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(t=80, b=40, l=50, r=20))
        all_figs.append((bot_name, fig, total_pnl))

    try:
        from condor.reports import ReportBuilder
        total_all = sum(p for _, _, p in all_figs)
        builder = ReportBuilder("Session Analytics")
        builder.source("routine", "session_stats").tags(["monitoring", "sessions"])
        builder.kpi("Bots", str(len(all_figs)))
        builder.kpi("Total PNL", f"{total_all:+.4f} USDT", trend="up" if total_all >= 0 else "down")
        builder.kpi("Updated", time.strftime("%H:%M UTC", time.gmtime()))
        for bot_name, fig, pnl in all_figs:
            builder.markdown(f"### {bot_name[-30:]}")
            builder.plotly(fig)
        if all_tables:
            builder.markdown("### All Executions by Session")
            builder.table(all_tables)
        builder.save()
    except Exception as e:
        all_text.append(f"Report error: {e}")

    all_text.append(f"\n{time.strftime('%H:%M:%S UTC', time.gmtime())}")
    return "\n".join(all_text)
