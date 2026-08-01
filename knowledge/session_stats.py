"""Session performance statistics for active bots."""

CATEGORY = "Monitoring"

import sqlite3
import time
from typing import Any
from pathlib import Path

import yaml
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pydantic import BaseModel, Field

INSTANCES_DIR = Path.home() / "hummingbot-api/bots/instances"

CLOSE_TYPES = {1: "TimeLimit", 2: "SL", 3: "TP", 5: "EarlyStop", 6: "TrailingStop", 8: "Failed"}
SESSIONS = [("Asia", 0, 8), ("Europe", 8, 15), ("USA", 15, 21), ("Night", 21, 24)]


class Config(BaseModel):
    """Session performance analytics for active bots."""
    min_filled_quote: float = Field(default=0.0, description="Min filled_amount_quote filter")


def _get_sqlite_files():
    return sorted(INSTANCES_DIR.glob("*/data/*.sqlite"))


def _read_controller_config(instance_dir: Path) -> dict:
    """Read first controller config yml found in conf/controllers/."""
    configs = list((instance_dir / "conf" / "controllers").glob("*.yml"))
    if not configs:
        return {}
    try:
        with open(configs[0]) as f:
            data = yaml.safe_load(f) or {}
        data["_config_name"] = configs[0].stem  # имя файла без .yml
        return data
    except Exception:
        return {}


def _format_config_value(val) -> str:
    if val is None:
        return "—"
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    if isinstance(val, dict):
        return " | ".join(f"{k}={v}" for k, v in val.items())
    if isinstance(val, float):
        return f"{val:.4f}" if val < 1 else str(val)
    return str(val)


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
    except Exception:
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

    session_order = ["Asia", "Europe", "USA", "Night"]
    ct_order = ["TP", "SL", "TimeLimit", "EarlyStop", "TrailingStop"]
    colors = {
        "TP": "#3fb950", "SL": "#f85149", "TimeLimit": "#58a6ff",
        "EarlyStop": "#d29922", "TrailingStop": "#bc8cff"
    }

    # --- Собираем данные по всем ботам ---
    bots = []
    for db_path in files:
        instance_dir = db_path.parent.parent
        bot_name = instance_dir.name
        rows = _read_executors(db_path)
        cfg = _read_controller_config(instance_dir)
        stats = _analyze(rows) if rows else {}
        total_pnl = sum(r["net_pnl_quote"] for r in rows) if rows else 0.0
        bots.append({
            "name": bot_name,
            "short": bot_name[-30:],
            "rows": rows,
            "cfg": cfg,
            "stats": stats,
            "total_pnl": total_pnl,
            "total_cnt": len(rows),
        })

    try:
        from condor.reports import ReportBuilder

        total_all = sum(b["total_pnl"] for b in bots)
        builder = ReportBuilder("Session Analytics")
        builder.source("routine", "session_stats").tags(["monitoring", "sessions"])
        builder.kpi("Bots", str(len(bots)))
        builder.kpi("Total PNL", f"{total_all:+.4f} USDT", trend="up" if total_all >= 0 else "down")
        builder.kpi("Updated", time.strftime("%H:%M UTC", time.gmtime()))

        # ── 1. СВОДНАЯ ТАБЛИЦА БОТОВ ─────────────────────────────────────────
        builder.markdown("## 📋 Боты — конфиги и результаты")

        summary_rows = []
        for b in bots:
            cfg = b["cfg"]
            summary_rows.append({
                "Bot": b["short"],
                "Config": cfg.get("_config_name", "—"),
                "Pair": cfg.get("trading_pair", "—"),
                "Connector": cfg.get("connector_name", "—"),
                "Quote $": cfg.get("total_amount_quote", "—"),
                "Lev": cfg.get("leverage", "—"),
                "Spreads buy": _format_config_value(cfg.get("buy_spreads")),
                "Spreads sell": _format_config_value(cfg.get("sell_spreads")),
                "TP": cfg.get("take_profit", "—"),
                "SL": cfg.get("stop_loss", "—"),
                "Trailing": _format_config_value(cfg.get("trailing_stop")),
                "Interval": cfg.get("interval", "—"),
                "Trades": b["total_cnt"],
                "PNL": f"{b['total_pnl']:+.4f}" if b["total_cnt"] else "—",
            })
        builder.table(summary_rows)

        # ── 2. ДЕТАЛИ ПО КАЖДОМУ БОТУ ────────────────────────────────────────
        builder.markdown("---")
        builder.markdown("## 📊 Детали по каждому боту")

        for b in bots:
            if not b["rows"]:
                continue

            cfg = b["cfg"]
            builder.markdown(f"### {b['short']}")
            builder.markdown(
                f"**Trades:** {b['total_cnt']} &nbsp;|&nbsp; "
                f"**PNL:** {b['total_pnl']:+.4f} USDT &nbsp;|&nbsp; "
                f"**Pair:** {cfg.get('trading_pair', '—')} &nbsp;|&nbsp; "
                f"**Leverage:** {cfg.get('leverage', '—')}x &nbsp;|&nbsp; "
                f"**Spreads:** {_format_config_value(cfg.get('buy_spreads'))} / "
                f"{_format_config_value(cfg.get('sell_spreads'))}"
            )

            # Таблица по сессиям
            session_table = []
            for session in session_order:
                session_data = {ct: v for (s, ct), v in b["stats"].items() if s == session}
                if not session_data:
                    continue
                s_pnl = sum(v["pnl"] for v in session_data.values())
                s_cnt = sum(v["cnt"] for v in session_data.values())
                for ct in ct_order:
                    if ct in session_data:
                        v = session_data[ct]
                        session_table.append({
                            "Session": session,
                            "Type": ct,
                            "Count": v["cnt"],
                            "PNL": f"{v['pnl']:+.4f}",
                        })
                session_table.append({
                    "Session": f"▶ {session} total",
                    "Type": "—",
                    "Count": s_cnt,
                    "PNL": f"{s_pnl:+.4f}",
                })

            builder.table(session_table)

            # График
            fig = make_subplots(rows=1, cols=1)
            for ct in ct_order:
                x_vals, y_vals = [], []
                for session in session_order:
                    v = b["stats"].get((session, ct))
                    if v:
                        x_vals.append(session)
                        y_vals.append(round(v["pnl"], 4))
                if x_vals:
                    fig.add_trace(go.Bar(
                        name=ct, x=x_vals, y=y_vals,
                        marker_color=colors.get(ct, "#8b949e"),
                        text=[f"{v:+.4f}" for v in y_vals],
                        textposition="outside"
                    ))
            fig.update_layout(
                title=f"PNL by Session — {b['short'][-25:]}",
                barmode="group",
                paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
                font=dict(color="#e6edf3"),
                yaxis=dict(gridcolor="#30363d", zeroline=True, zerolinecolor="#58a6ff"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                margin=dict(t=80, b=40, l=50, r=20)
            )
            builder.plotly(fig)
            builder.markdown("---")

        builder.save()

    except Exception as e:
        return f"Report error: {e}"

    return f"✅ Session Analytics — {len(bots)} ботов | {time.strftime('%H:%M:%S UTC', time.gmtime())}"
