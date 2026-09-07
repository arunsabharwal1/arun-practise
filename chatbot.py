"""
chatbot.py — GenAI Chatbot module for the Project Tracker dashboard.

Uses Google Gemini 2.0 Flash via the official google-genai SDK (free tier).
No local model downloads required.

Dependencies:
    pip install google-genai python-dotenv

Environment variable (in .env):
    GEMINI_API_KEY=<your-key-from-aistudio.google.com/app/apikey>
"""

from __future__ import annotations

import os
import sqlite3
import textwrap
from typing import List, Dict

from dotenv import load_dotenv
from google import genai
from google.genai import types

# ── Load environment ────────────────────────────────────────────────────────
load_dotenv()

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# ── Risk matrix helper (mirrors dashboard.py) ───────────────────────────────
_RISK_MATRIX: Dict[tuple, str] = {
    ("low", "low"): "low",       ("low", "medium"): "low",
    ("low", "high"): "medium",   ("low", "critical"): "medium",
    ("medium", "low"): "low",    ("medium", "medium"): "medium",
    ("medium", "high"): "high",  ("medium", "critical"): "critical",
    ("high", "low"): "medium",   ("high", "medium"): "high",
    ("high", "high"): "critical",("high", "critical"): "critical",
    ("critical", "low"): "medium",("critical", "medium"): "high",
    ("critical", "high"): "critical",("critical", "critical"): "critical",
}


def _risk_level(prob: str, impact: str) -> str:
    return _RISK_MATRIX.get((prob.lower(), impact.lower()), "medium")


def _fmt_usd(value: float) -> str:
    """Format a float as a readable dollar amount."""
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.2f}"


# ── Context builder ─────────────────────────────────────────────────────────

def build_db_context(db_path: str = "projectdb.sqlite") -> str:
    """
    Query all four tables and serialise the data into a structured text
    block the LLM can reason over. Numbers are formatted to match the
    dashboard exactly so chatbot answers are consistent with the UI.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT * FROM projects ORDER BY id")
        projects = cur.fetchall()

        cur.execute("""
            SELECT f.*
            FROM financial_logs f
            INNER JOIN (
                SELECT project_id, MAX(id) AS max_id
                FROM financial_logs
                GROUP BY project_id
            ) latest ON f.project_id = latest.project_id AND f.id = latest.max_id
        """)
        fin_rows = cur.fetchall()
        fin_map = {row["project_id"]: row for row in fin_rows}

        cur.execute("SELECT * FROM team_members ORDER BY project_id, is_lead DESC")
        team_rows = cur.fetchall()

        cur.execute("SELECT * FROM risk_entries ORDER BY project_id")
        risk_rows = cur.fetchall()

        conn.close()
    except Exception as exc:
        return f"[ERROR reading database: {exc}]"

    # ── Aggregate portfolio-level metrics ─────────────────────────────────
    total_budget  = sum(fin_map[p["id"]]["budget"]      for p in projects if p["id"] in fin_map)
    total_cost    = sum(fin_map[p["id"]]["actual_cost"] for p in projects if p["id"] in fin_map)
    total_revenue = sum(fin_map[p["id"]]["revenue"]     for p in projects if p["id"] in fin_map)
    net_profit    = total_revenue - total_cost
    avg_margin    = ((total_revenue - total_cost) / max(total_revenue, 1)) * 100
    open_risks    = [r for r in risk_rows if r["status"] == "OPEN"]
    total_team    = len(team_rows)

    lines: List[str] = []
    lines.append("=== PROJECT TRACKER - LIVE DATABASE SNAPSHOT ===\n")
    lines.append(f"Total Projects  : {len(projects)}")
    lines.append(f"Total Team Mbrs : {total_team}")
    lines.append(f"Open Risks      : {len(open_risks)}")
    lines.append(f"Total Budget    : {_fmt_usd(total_budget)}")
    lines.append(f"Total Spent     : {_fmt_usd(total_cost)}")
    lines.append(f"Total Revenue   : {_fmt_usd(total_revenue)}")
    lines.append(f"Net Profit      : {_fmt_usd(net_profit)}")
    lines.append(f"Portfolio Margin: {avg_margin:.1f}%\n")

    lines.append("--- PROJECTS ---")
    for p in projects:
        pid = p["id"]
        fin = fin_map.get(pid)

        budget  = fin["budget"]      if fin else 0
        cost    = fin["actual_cost"] if fin else 0
        revenue = fin["revenue"]     if fin else 0
        margin  = ((revenue - cost) / max(revenue, 1)) * 100 if fin else 0
        util    = (cost / max(budget, 1)) * 100 if fin else 0

        p_team   = [m for m in team_rows if m["project_id"] == pid]
        p_risks  = [r for r in risk_rows if r["project_id"] == pid]
        p_open_r = [r for r in p_risks   if r["status"] == "OPEN"]

        leads   = [m["name"] for m in p_team if m["is_lead"]]
        members = [m["name"] for m in p_team if not m["is_lead"]]

        lines.append(f"\n[Project #{pid}] {p['name']}")
        lines.append(f"  Client      : {p['client'] or '—'}")
        lines.append(f"  Status      : {p['status']}")
        lines.append(f"  Timeline    : {p['start_date']} -> {p['end_date']}")
        lines.append(f"  Description : {(p['description'] or '—')[:150]}")
        if fin:
            lines.append(f"  Budget      : {_fmt_usd(budget)}")
            lines.append(f"  Actual Cost : {_fmt_usd(cost)}  (remaining: {_fmt_usd(budget - cost)})")
            lines.append(f"  Revenue     : {_fmt_usd(revenue)}")
            lines.append(f"  Profit Mrgn : {margin:.1f}%")
            lines.append(f"  Budget Used : {util:.1f}%")
            if fin["notes"]:
                lines.append(f"  Notes       : {fin['notes'][:100]}")
        else:
            lines.append("  Financials  : no data")

        lines.append(f"  Team Size   : {len(p_team)}" +
                     (f" (Lead: {', '.join(leads)})" if leads else ""))
        if members:
            lines.append(f"  Members     : {', '.join(members[:8])}" +
                         (" ..." if len(members) > 8 else ""))

        lines.append(f"  Risks Total : {len(p_risks)}  Open: {len(p_open_r)}")
        for r in p_risks:
            rl = _risk_level(r["probability"], r["impact"])
            line = (f"    - [{r['status']:7}] [{rl.upper():8}] {r['title']}"
                    + (f" - Owner: {r['owner']}" if r["owner"] else ""))
            lines.append(line)
            if r["mitigation_plan"]:
                lines.append(f"        Mitigation: {r['mitigation_plan'][:120]}")

    lines.append("\n=== END OF SNAPSHOT ===")
    return "\n".join(lines)


# ── System prompt ────────────────────────────────────────────────────────────

def _build_system_prompt(db_context: str) -> str:
    return textwrap.dedent(f"""
        You are an intelligent project management assistant embedded in a
        real-time dashboard for a software consultancy.

        Your job is to answer questions about the company's projects,
        financials, team members, and risks using ONLY the data provided
        below. Do not invent numbers. If a question cannot be answered
        from the data, say so politely and explain what data is available.

        Formatting rules:
        - Be concise and direct.
        - Use bullet points or markdown tables where helpful.
        - Format currency with $ signs (e.g. $1.2M, $450K).
        - Format percentages with % signs.
        - Bold important figures using **value**.

        CURRENT DATABASE SNAPSHOT (as of this query):
        {db_context}
    """).strip()


# ── Chatbot entrypoint ────────────────────────────────────────────────────────

def ask_chatbot(
    user_question: str,
    db_path: str = "projectdb.sqlite",
    chat_history: List[Dict[str, str]] | None = None,
) -> str:
    """
    Send `user_question` to Gemini 2.0 Flash with a live database snapshot.

    Args:
        user_question:  The user's message.
        db_path:        Path to the SQLite database file.
        chat_history:   List of previous messages with 'role' and 'content' keys.
                        Roles should be 'user' or 'assistant'.

    Returns:
        The assistant's response as a markdown string.
    """
    if not _GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not configured.\n"
            "1. Get a free key at https://aistudio.google.com/app/apikey\n"
            "2. Add GEMINI_API_KEY=<your-key> to your .env file\n"
            "3. Restart the Streamlit app"
        )

    db_context   = build_db_context(db_path)
    system_prompt = _build_system_prompt(db_context)

    # Build the conversation history in google-genai format
    history: List[types.Content] = []
    if chat_history:
        for msg in chat_history:
            role = "user" if msg["role"] == "user" else "model"
            history.append(
                types.Content(role=role, parts=[types.Part(text=msg["content"])])
            )

    try:
        client = genai.Client(api_key=_GEMINI_API_KEY)

        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=history + [
                types.Content(
                    role="user",
                    parts=[types.Part(text=user_question)]
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,       # low temp = more factual, less hallucination
                max_output_tokens=1024,
            ),
        )
        return response.text

    except Exception as exc:
        err = str(exc)
        if any(k in err.upper() for k in ("API_KEY", "INVALID_ARGUMENT", "401", "403")):
            return (
                "**API key error.** Please check that `GEMINI_API_KEY` in your "
                "`.env` file is valid and not expired.\n\n"
                f"_Details: {err}_"
            )
        if "quota" in err.lower() or "429" in err or "RESOURCE_EXHAUSTED" in err.upper():
            return (
                "**Rate limit reached.** The free Gemini tier has per-minute "
                "request limits. Please wait a moment and try again.\n\n"
                f"_Details: {err}_"
            )
        return f"**Unexpected error calling Gemini API:**\n\n```\n{err}\n```"
