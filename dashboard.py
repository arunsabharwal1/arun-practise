"""
Streamlit GUI Dashboard for Project Management Tracking.

Reads directly from SQLite database and also calls the FastAPI backend for writes.

Run:
    streamlit run dashboard.py
"""

import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import requests
from datetime import date, datetime

# ─── Config ───────────────────────────────────────────────────────────────────

DB_PATH = "projectdb.sqlite"
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Project Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f1117; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #16213e 100%);
        border-right: 1px solid #2d3561;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e2a45 0%, #16213e 100%);
        border: 1px solid #2d3561;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    /* Headers */
    h1, h2, h3 { color: #e0e6f0 !important; }

    /* Status badges */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .badge-active    { background: #0d4a2f; color: #4ade80; border: 1px solid #4ade80; }
    .badge-planning  { background: #1e3a5f; color: #60a5fa; border: 1px solid #60a5fa; }
    .badge-on_hold   { background: #4a3000; color: #fbbf24; border: 1px solid #fbbf24; }
    .badge-completed { background: #2d1b69; color: #a78bfa; border: 1px solid #a78bfa; }
    .badge-cancelled { background: #4a1d1d; color: #f87171; border: 1px solid #f87171; }

    /* Risk badges */
    .risk-low      { background:#0d4a2f; color:#4ade80; border:1px solid #4ade80; padding:3px 10px; border-radius:12px; font-size:11px; }
    .risk-medium   { background:#4a3000; color:#fbbf24; border:1px solid #fbbf24; padding:3px 10px; border-radius:12px; font-size:11px; }
    .risk-high     { background:#4a2000; color:#fb923c; border:1px solid #fb923c; padding:3px 10px; border-radius:12px; font-size:11px; }
    .risk-critical { background:#4a1d1d; color:#f87171; border:1px solid #f87171; padding:3px 10px; border-radius:12px; font-size:11px; }

    /* Project cards */
    .project-card {
        background: linear-gradient(135deg, #1a2540 0%, #16213e 100%);
        border: 1px solid #2d3561;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 12px;
        transition: border-color 0.2s;
    }
    .project-card:hover { border-color: #6366f1; }

    /* Divider */
    hr { border-color: #2d3561 !important; }

    /* Tabs */
    [data-testid="stTab"] { color: #94a3b8; }

    /* Table */
    [data-testid="stDataFrame"] { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)


# ─── DB Helpers ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=5)
def load_projects():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM projects ORDER BY id", conn)
    conn.close()
    return df


@st.cache_data(ttl=5)
def load_financials():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM financial_logs", conn)
    conn.close()
    if not df.empty:
        df["profit_margin"] = ((df["revenue"] - df["actual_cost"]) / df["revenue"].replace(0, 1) * 100).round(1)
        df["budget_utilization"] = (df["actual_cost"] / df["budget"].replace(0, 1) * 100).round(1)
    return df


@st.cache_data(ttl=5)
def load_team():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM team_members", conn)
    conn.close()
    return df


@st.cache_data(ttl=5)
def load_risks():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM risk_entries", conn)
    conn.close()
    return df


def risk_level_from_matrix(prob, impact):
    matrix = {
        ("low","low"):"low", ("low","medium"):"low", ("low","high"):"medium", ("low","critical"):"medium",
        ("medium","low"):"low", ("medium","medium"):"medium", ("medium","high"):"high", ("medium","critical"):"critical",
        ("high","low"):"medium", ("high","medium"):"high", ("high","high"):"critical", ("high","critical"):"critical",
        ("critical","low"):"medium", ("critical","medium"):"high", ("critical","high"):"critical", ("critical","critical"):"critical",
    }
    return matrix.get((prob.lower(), impact.lower()), "medium")


def status_badge(status):
    return f'<span class="badge badge-{status}">{status.replace("_"," ").upper()}</span>'


def risk_badge(level):
    return f'<span class="risk-{level}">{level.upper()}</span>'


def api_post(endpoint, data):
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=data, timeout=5)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500


def api_put(endpoint, data):
    try:
        r = requests.put(f"{API_BASE}{endpoint}", json=data, timeout=5)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500


def api_delete(endpoint):
    try:
        r = requests.delete(f"{API_BASE}{endpoint}", timeout=5)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📊 Project Tracker")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["🏠 Overview Dashboard", "📁 All Projects", "🔍 Project Detail", "💰 Financials", "⚠️ Risk Heatmap", "➕ Add Project"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**🔗 Quick Links**")
    st.markdown("[API Docs ↗](http://localhost:8000/docs)")
    st.markdown("[Raw JSON ↗](http://localhost:8000/projects/)")

    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("<small style='color:#4a5568'>v1.0 · FastAPI + SQLite</small>", unsafe_allow_html=True)


# ─── Load Data ────────────────────────────────────────────────────────────────

projects_df = load_projects()
financials_df = load_financials()
team_df = load_team()
risks_df = load_risks()

# Merge for enriched views
if not projects_df.empty and not financials_df.empty:
    merged = projects_df.merge(financials_df[["project_id","budget","actual_cost","revenue","profit_margin","budget_utilization"]], left_on="id", right_on="project_id", how="left")
else:
    merged = projects_df.copy()

STATUS_COLORS = {
    "ACTIVE": "#4ade80", "PLANNING": "#60a5fa",
    "ON_HOLD": "#fbbf24", "COMPLETED": "#a78bfa", "CANCELLED": "#f87171"
}
RISK_COLORS = {"low": "#4ade80", "medium": "#fbbf24", "high": "#fb923c", "critical": "#f87171"}


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

if page == "🏠 Overview Dashboard":
    st.markdown("# 🏠 Project Portfolio Overview")
    st.markdown("Real-time tracking of all 10 active projects")
    st.markdown("---")

    # ── KPI Metrics Row ──
    total_budget   = financials_df["budget"].sum() if not financials_df.empty else 0
    total_cost     = financials_df["actual_cost"].sum() if not financials_df.empty else 0
    total_revenue  = financials_df["revenue"].sum() if not financials_df.empty else 0
    total_team     = len(team_df)
    open_risks     = len(risks_df[risks_df["status"] == "OPEN"]) if not risks_df.empty else 0
    avg_margin     = financials_df["profit_margin"].mean() if not financials_df.empty else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📁 Total Projects", len(projects_df))
    c2.metric("💰 Total Budget",   f"${total_budget/1e6:.1f}M")
    c3.metric("💸 Total Spent",    f"${total_cost/1e6:.1f}M",  delta=f"-${(total_budget-total_cost)/1e6:.1f}M remaining")
    c4.metric("📈 Total Revenue",  f"${total_revenue/1e6:.1f}M")
    c5.metric("👥 Team Members",   total_team)
    c6.metric("⚠️ Open Risks",     open_risks, delta_color="inverse")

    st.markdown("---")

    # ── Charts Row 1 ──
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📊 Project Status Distribution")
        status_counts = projects_df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        colors = [STATUS_COLORS.get(s, "#94a3b8") for s in status_counts["status"]]
        fig = px.pie(
            status_counts, values="count", names="status",
            color_discrete_sequence=colors,
            hole=0.55,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e6f0", legend_font_color="#e0e6f0",
            margin=dict(t=10, b=10),
        )
        fig.update_traces(textfont_color="#e0e6f0")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 💰 Budget vs Cost vs Revenue")
        if not merged.empty:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="Budget", x=merged["name"], y=merged["budget"], marker_color="#6366f1", opacity=0.85))
            fig2.add_trace(go.Bar(name="Actual Cost", x=merged["name"], y=merged["actual_cost"], marker_color="#f87171", opacity=0.85))
            fig2.add_trace(go.Bar(name="Revenue", x=merged["name"], y=merged["revenue"], marker_color="#4ade80", opacity=0.85))
            fig2.update_layout(
                barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e6f0", xaxis_tickangle=-35,
                legend=dict(font=dict(color="#e0e6f0")),
                yaxis=dict(gridcolor="#2d3561", tickprefix="$"),
                xaxis=dict(tickfont=dict(size=9)),
                margin=dict(t=10, b=80),
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ── Charts Row 2 ──
    col3, col4 = st.columns([1, 1])

    with col3:
        st.markdown("### 📉 Profit Margin by Project")
        if not merged.empty:
            merged_sorted = merged.sort_values("profit_margin", ascending=True)
            colors_bar = ["#f87171" if v < 20 else "#fbbf24" if v < 50 else "#4ade80" for v in merged_sorted["profit_margin"]]
            fig3 = go.Figure(go.Bar(
                x=merged_sorted["profit_margin"], y=merged_sorted["name"],
                orientation="h", marker_color=colors_bar,
                text=[f"{v:.1f}%" for v in merged_sorted["profit_margin"]],
                textposition="outside", textfont=dict(color="#e0e6f0"),
            ))
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e6f0", xaxis=dict(ticksuffix="%", gridcolor="#2d3561"),
                yaxis=dict(tickfont=dict(size=10)),
                margin=dict(t=10, l=10, r=60),
            )
            st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("### ⚠️ Risk Distribution")
        if not risks_df.empty:
            risks_df["risk_level"] = risks_df.apply(
                lambda r: risk_level_from_matrix(r["probability"], r["impact"]), axis=1
            )
            risk_counts = risks_df["risk_level"].value_counts().reset_index()
            risk_counts.columns = ["level", "count"]
            colors_risk = [RISK_COLORS.get(l, "#94a3b8") for l in risk_counts["level"]]
            fig4 = px.bar(risk_counts, x="level", y="count", color="level",
                          color_discrete_map=RISK_COLORS, text="count")
            fig4.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e6f0", showlegend=False,
                yaxis=dict(gridcolor="#2d3561"),
                margin=dict(t=10),
            )
            fig4.update_traces(textfont_color="#e0e6f0")
            st.plotly_chart(fig4, use_container_width=True)

    # ── Team size per project ──
    st.markdown("### 👥 Team Size per Project")
    if not team_df.empty and not projects_df.empty:
        team_counts = team_df.groupby("project_id").size().reset_index(name="team_size")
        team_merged = team_counts.merge(projects_df[["id","name"]], left_on="project_id", right_on="id")
        fig5 = px.bar(team_merged, x="name", y="team_size", color="team_size",
                      color_continuous_scale=["#2d3561","#6366f1","#a78bfa"],
                      text="team_size")
        fig5.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e6f0", showlegend=False, coloraxis_showscale=False,
            xaxis_tickangle=-30, yaxis=dict(gridcolor="#2d3561"),
            margin=dict(t=10, b=80),
        )
        fig5.update_traces(textfont_color="#e0e6f0")
        st.plotly_chart(fig5, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ALL PROJECTS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "📁 All Projects":
    st.markdown("# 📁 All Projects")

    # Filter controls
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search = st.text_input("🔍 Search projects...", placeholder="Type project or client name")
    with col_f2:
        status_filter = st.multiselect("Filter by status", ["ACTIVE","PLANNING","ON_HOLD","COMPLETED","CANCELLED"], default=[])

    filtered = merged.copy()
    if search:
        filtered = filtered[filtered["name"].str.contains(search, case=False) | filtered["client"].str.contains(search, case=False, na=False)]
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]

    st.markdown(f"**{len(filtered)} projects found**")
    st.markdown("---")

    for _, row in filtered.iterrows():
        with st.container():
            c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1.5])
            with c1:
                st.markdown(f"**{row['name']}**")
                st.markdown(f"<small style='color:#94a3b8'>👤 {row.get('client','—')}</small>", unsafe_allow_html=True)
                st.markdown(status_badge(row["status"]), unsafe_allow_html=True)
            with c2:
                budget = row.get('budget', 0) or 0
                cost = row.get('actual_cost', 0) or 0
                st.metric("Budget", f"${budget:,.0f}")
                st.metric("Spent", f"${cost:,.0f}")
            with c3:
                revenue = row.get('revenue', 0) or 0
                margin = row.get('profit_margin', 0) or 0
                st.metric("Revenue", f"${revenue:,.0f}")
                st.metric("Margin", f"{margin:.1f}%")
            with c4:
                proj_team = team_df[team_df["project_id"] == row["id"]] if not team_df.empty else pd.DataFrame()
                proj_risks = risks_df[(risks_df["project_id"] == row["id"]) & (risks_df["status"] == "OPEN")] if not risks_df.empty else pd.DataFrame()
                st.metric("👥 Team", len(proj_team))
                st.metric("⚠️ Open Risks", len(proj_risks))
            st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PROJECT DETAIL
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🔍 Project Detail":
    st.markdown("# 🔍 Project Detail")

    if projects_df.empty:
        st.warning("No projects found.")
    else:
        project_names = projects_df["name"].tolist()
        selected_name = st.selectbox("Select a project", project_names)
        proj = projects_df[projects_df["name"] == selected_name].iloc[0]
        proj_id = int(proj["id"])

        st.markdown(f"## {proj['name']}")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Client:** {proj.get('client','—')}")
            st.markdown(f"**Description:** {proj.get('description','—')}")
            start = proj.get('start_date','—')
            end = proj.get('end_date','—')
            st.markdown(f"**Timeline:** {start} → {end}")
        with col2:
            st.markdown(status_badge(proj["status"]), unsafe_allow_html=True)

        st.markdown("---")
        tab1, tab2, tab3, tab4 = st.tabs(["💰 Financials", "👥 Team", "⚠️ Risks", "✏️ Edit Project"])

        # ── Financials Tab ──
        with tab1:
            fin = financials_df[financials_df["project_id"] == proj_id]
            if fin.empty:
                st.info("No financial data logged yet.")
            else:
                f = fin.iloc[0]
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Budget", f"${f['budget']:,.0f}")
                c2.metric("Actual Cost", f"${f['actual_cost']:,.0f}", delta=f"-${f['budget']-f['actual_cost']:,.0f} remaining")
                c3.metric("Revenue", f"${f['revenue']:,.0f}")
                c4.metric("Profit Margin", f"{f['profit_margin']:.1f}%")

                # Gauge chart for budget utilization
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=f["budget_utilization"],
                    title={"text": "Budget Utilization %", "font": {"color": "#e0e6f0"}},
                    delta={"reference": 50},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
                        "bar": {"color": "#6366f1"},
                        "steps": [
                            {"range": [0, 50], "color": "#0d4a2f"},
                            {"range": [50, 80], "color": "#4a3000"},
                            {"range": [80, 100], "color": "#4a1d1d"},
                        ],
                        "threshold": {"line": {"color": "#f87171", "width": 3}, "thickness": 0.75, "value": 90},
                    },
                    number={"suffix": "%", "font": {"color": "#e0e6f0"}},
                ))
                fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#e0e6f0", height=280, margin=dict(t=30,b=10))
                st.plotly_chart(fig_gauge, use_container_width=True)

                # Add new financial log
                st.markdown("#### ➕ Update Financials")
                with st.form(f"fin_form_{proj_id}"):
                    fc1, fc2, fc3 = st.columns(3)
                    new_budget = fc1.number_input("Budget ($)", value=float(f["budget"]), step=1000.0)
                    new_cost   = fc2.number_input("Actual Cost ($)", value=float(f["actual_cost"]), step=1000.0)
                    new_rev    = fc3.number_input("Revenue ($)", value=float(f["revenue"]), step=1000.0)
                    new_notes  = st.text_area("Notes", value=f.get("notes","") or "")
                    if st.form_submit_button("💾 Save Financial Update"):
                        resp, code = api_post(f"/projects/{proj_id}/financials", {
                            "budget": new_budget, "actual_cost": new_cost,
                            "revenue": new_rev, "notes": new_notes
                        })
                        if code == 201:
                            st.success("✅ Financial log updated!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Error: {resp}")

        # ── Team Tab ──
        with tab2:
            team = team_df[team_df["project_id"] == proj_id] if not team_df.empty else pd.DataFrame()
            if team.empty:
                st.info("No team members yet.")
            else:
                for _, m in team.iterrows():
                    tc1, tc2, tc3, tc4 = st.columns([2.5, 1.5, 1, 1])
                    lead_badge = "⭐ " if m["is_lead"] else ""
                    tc1.markdown(f"**{lead_badge}{m['name']}**\n\n<small style='color:#94a3b8'>{m.get('email','')}</small>", unsafe_allow_html=True)
                    tc2.markdown(f"🎯 {m['role']}")
                    tc3.markdown(f"⏱ {int(m['allocation_percentage'])}%")
                    with tc4:
                        if st.button("🗑", key=f"del_member_{m['id']}", help="Remove member"):
                            resp, code = api_delete(f"/projects/{proj_id}/team/{m['id']}")
                            if code == 200:
                                st.success("Removed!")
                                st.cache_data.clear()
                                st.rerun()
                    st.markdown("---")

            st.markdown("#### ➕ Add Team Member")
            with st.form(f"team_form_{proj_id}"):
                ta1, ta2 = st.columns(2)
                new_name  = ta1.text_input("Name")
                new_role  = ta2.text_input("Role")
                tb1, tb2, tb3 = st.columns(3)
                new_email = tb1.text_input("Email (optional)")
                new_alloc = tb2.slider("Allocation %", 10, 100, 100, step=10)
                new_lead  = tb3.checkbox("Is Project Lead?")
                if st.form_submit_button("➕ Add Member"):
                    if new_name and new_role:
                        resp, code = api_post(f"/projects/{proj_id}/team", {
                            "name": new_name, "role": new_role,
                            "email": new_email or None,
                            "allocation_percentage": new_alloc, "is_lead": new_lead
                        })
                        if code == 201:
                            st.success(f"✅ {new_name} added to team!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Error: {resp}")
                    else:
                        st.warning("Name and Role are required.")

        # ── Risks Tab ──
        with tab3:
            risks = risks_df[risks_df["project_id"] == proj_id] if not risks_df.empty else pd.DataFrame()
            if risks.empty:
                st.info("No risks registered.")
            else:
                for _, r in risks.iterrows():
                    rl = risk_level_from_matrix(r["probability"], r["impact"])
                    rc1, rc2, rc3 = st.columns([3, 1, 1])
                    with rc1:
                        st.markdown(f"**{r['title']}**")
                        if r.get("mitigation_plan"):
                            st.markdown(f"<small style='color:#94a3b8'>🛡 {r['mitigation_plan']}</small>", unsafe_allow_html=True)
                        if r.get("owner"):
                            st.markdown(f"<small style='color:#94a3b8'>👤 Owner: {r['owner']}</small>", unsafe_allow_html=True)
                    with rc2:
                        st.markdown(risk_badge(rl), unsafe_allow_html=True)
                        st.markdown(f"<small style='color:#94a3b8'>Status: {r['status']}</small>", unsafe_allow_html=True)
                    with rc3:
                        if st.button("🗑", key=f"del_risk_{r['id']}", help="Delete risk"):
                            resp, code = api_delete(f"/projects/{proj_id}/risks/{r['id']}")
                            if code == 200:
                                st.success("Deleted!")
                                st.cache_data.clear()
                                st.rerun()
                    st.markdown("---")

            st.markdown("#### ➕ Register New Risk")
            with st.form(f"risk_form_{proj_id}"):
                new_title = st.text_input("Risk Title")
                ra1, ra2 = st.columns(2)
                new_prob   = ra1.selectbox("Probability", ["low","medium","high","critical"])
                new_impact = ra2.selectbox("Impact", ["low","medium","high","critical"])
                new_mitig  = st.text_area("Mitigation Plan")
                new_owner  = st.text_input("Risk Owner")
                computed_rl = risk_level_from_matrix(new_prob, new_impact)
                st.markdown(f"**Computed Risk Level:** {risk_badge(computed_rl)}", unsafe_allow_html=True)
                if st.form_submit_button("⚠️ Register Risk"):
                    if new_title:
                        resp, code = api_post(f"/projects/{proj_id}/risks", {
                            "title": new_title, "probability": new_prob,
                            "impact": new_impact, "mitigation_plan": new_mitig,
                            "owner": new_owner or None
                        })
                        if code == 201:
                            st.success("✅ Risk registered!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Error: {resp}")
                    else:
                        st.warning("Risk title is required.")

        # ── Edit Project Tab ──
        with tab4:
            st.markdown("#### ✏️ Edit Project Details")
            with st.form(f"edit_proj_{proj_id}"):
                ep1, ep2 = st.columns(2)
                edit_name   = ep1.text_input("Project Name", value=proj["name"])
                edit_client = ep2.text_input("Client", value=proj.get("client","") or "")
                edit_desc   = st.text_area("Description", value=proj.get("description","") or "")
                ep3, ep4, ep5 = st.columns(3)
                status_opts = ["planning","active","on_hold","completed","cancelled"]
                current_status = proj["status"].lower()
                edit_status = ep3.selectbox("Status", status_opts, index=status_opts.index(current_status))
                edit_start  = ep4.date_input("Start Date", value=pd.to_datetime(proj["start_date"]).date() if proj.get("start_date") else date.today())
                edit_end    = ep5.date_input("End Date", value=pd.to_datetime(proj["end_date"]).date() if proj.get("end_date") else date.today())
                if st.form_submit_button("💾 Update Project"):
                    resp, code = api_put(f"/projects/{proj_id}", {
                        "name": edit_name, "client": edit_client,
                        "description": edit_desc, "status": edit_status,
                        "start_date": str(edit_start), "end_date": str(edit_end),
                    })
                    if code == 200:
                        st.success("✅ Project updated!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Error: {resp}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: FINANCIALS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "💰 Financials":
    st.markdown("# 💰 Financial Overview")
    st.markdown("---")

    if merged.empty:
        st.warning("No financial data available.")
    else:
        # Summary table
        display_df = merged[["name","client","status","budget","actual_cost","revenue","profit_margin","budget_utilization"]].copy()
        display_df.columns = ["Project","Client","Status","Budget ($)","Cost ($)","Revenue ($)","Margin (%)","Budget Used (%)"]
        display_df["Budget ($)"] = display_df["Budget ($)"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
        display_df["Cost ($)"]   = display_df["Cost ($)"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
        display_df["Revenue ($)"] = display_df["Revenue ($)"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
        display_df["Margin (%)"]  = display_df["Margin (%)"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
        display_df["Budget Used (%)"] = display_df["Budget Used (%)"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        # Waterfall: total financial flow
        st.markdown("### 💧 Portfolio Financial Waterfall")
        total_budget  = financials_df["budget"].sum()
        total_cost    = financials_df["actual_cost"].sum()
        total_revenue = financials_df["revenue"].sum()
        net_profit    = total_revenue - total_cost

        fig_wf = go.Figure(go.Waterfall(
            name="", orientation="v",
            measure=["absolute","relative","relative","total"],
            x=["Total Budget", "Cost Incurred", "Revenue Earned", "Net Profit"],
            y=[total_budget, -total_cost, total_revenue, 0],
            connector={"line": {"color": "#2d3561"}},
            decreasing={"marker": {"color": "#f87171"}},
            increasing={"marker": {"color": "#4ade80"}},
            totals={"marker": {"color": "#6366f1"}},
            text=[f"${total_budget/1e6:.1f}M", f"-${total_cost/1e6:.1f}M", f"+${total_revenue/1e6:.1f}M", f"${net_profit/1e6:.1f}M"],
            textfont={"color": "#e0e6f0"},
        ))
        fig_wf.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e6f0", yaxis=dict(tickprefix="$", gridcolor="#2d3561"),
            margin=dict(t=10),
        )
        st.plotly_chart(fig_wf, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: RISK HEATMAP
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "⚠️ Risk Heatmap":
    st.markdown("# ⚠️ Risk Heatmap")
    st.markdown("Risk level = Probability × Impact matrix across all projects")
    st.markdown("---")

    if risks_df.empty:
        st.warning("No risks found.")
    else:
        risks_df["risk_level"] = risks_df.apply(
            lambda r: risk_level_from_matrix(r["probability"], r["impact"]), axis=1
        )

        # Full risk table
        risks_merged = risks_df.merge(projects_df[["id","name"]], left_on="project_id", right_on="id", suffixes=("","_proj"))
        risks_display = risks_merged[["name","title","probability","impact","risk_level","status","owner","mitigation_plan"]].copy()
        risks_display.columns = ["Project","Risk","Probability","Impact","Risk Level","Status","Owner","Mitigation"]

        # Color rows by risk level
        st.dataframe(risks_display, use_container_width=True, hide_index=True)

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            # Heatmap grid
            st.markdown("### 🔥 Risk Matrix Heatmap")
            levels = ["low","medium","high","critical"]
            z = [[0]*4 for _ in range(4)]
            for _, r in risks_df.iterrows():
                pi = levels.index(r["probability"].lower()) if r["probability"].lower() in levels else 0
                ii = levels.index(r["impact"].lower()) if r["impact"].lower() in levels else 0
                z[pi][ii] += 1

            fig_heat = go.Figure(go.Heatmap(
                z=z, x=levels, y=levels,
                colorscale=[[0,"#0d4a2f"],[0.33,"#4a3000"],[0.66,"#4a2000"],[1,"#4a1d1d"]],
                text=[[str(v) if v > 0 else "" for v in row] for row in z],
                texttemplate="%{text}",
                textfont={"color":"#e0e6f0","size":18},
                showscale=False,
            ))
            fig_heat.update_layout(
                xaxis_title="Impact", yaxis_title="Probability",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e6f0", margin=dict(t=10),
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        with col2:
            st.markdown("### 📊 Risks by Project")
            proj_risk_counts = risks_merged.groupby(["name","risk_level"]).size().reset_index(name="count")
            fig_stacked = px.bar(
                proj_risk_counts, x="name", y="count", color="risk_level",
                color_discrete_map=RISK_COLORS, barmode="stack",
            )
            fig_stacked.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e6f0", xaxis_tickangle=-35,
                legend=dict(font=dict(color="#e0e6f0")),
                yaxis=dict(gridcolor="#2d3561"),
                margin=dict(t=10, b=80),
            )
            st.plotly_chart(fig_stacked, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ADD PROJECT
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "➕ Add Project":
    st.markdown("# ➕ Add New Project")
    st.markdown("---")

    with st.form("new_project_form"):
        c1, c2 = st.columns(2)
        proj_name   = c1.text_input("Project Name *")
        proj_client = c2.text_input("Client Name")
        proj_desc   = st.text_area("Description")

        c3, c4, c5 = st.columns(3)
        proj_status = c3.selectbox("Initial Status", ["planning","active","on_hold"])
        proj_start  = c4.date_input("Start Date", value=date.today())
        proj_end    = c5.date_input("End Date", value=date.today())

        st.markdown("#### 💰 Initial Financial Data (optional)")
        f1, f2, f3 = st.columns(3)
        init_budget  = f1.number_input("Budget ($)", min_value=0.0, step=10000.0)
        init_cost    = f2.number_input("Actual Cost ($)", min_value=0.0, step=1000.0)
        init_revenue = f3.number_input("Revenue ($)", min_value=0.0, step=10000.0)

        st.markdown("#### 👤 Initial Project Lead (optional)")
        l1, l2, l3 = st.columns(3)
        lead_name  = l1.text_input("Lead Name")
        lead_role  = l2.text_input("Lead Role")
        lead_email = l3.text_input("Lead Email")

        submitted = st.form_submit_button("🚀 Create Project", type="primary")
        if submitted:
            if not proj_name:
                st.error("Project name is required.")
            else:
                # Create project
                resp, code = api_post("/projects", {
                    "name": proj_name, "client": proj_client or None,
                    "description": proj_desc or None, "status": proj_status,
                    "start_date": str(proj_start), "end_date": str(proj_end),
                })
                if code == 201:
                    new_id = resp["id"]
                    # Add financials if provided
                    if init_budget or init_cost or init_revenue:
                        api_post(f"/projects/{new_id}/financials", {
                            "budget": init_budget, "actual_cost": init_cost, "revenue": init_revenue
                        })
                    # Add lead if provided
                    if lead_name and lead_role:
                        api_post(f"/projects/{new_id}/team", {
                            "name": lead_name, "role": lead_role,
                            "email": lead_email or None, "is_lead": True, "allocation_percentage": 100
                        })
                    st.success(f"✅ Project **{proj_name}** created successfully! (ID: {new_id})")
                    st.cache_data.clear()
                    st.balloons()
                else:
                    st.error(f"Error creating project: {resp}")
