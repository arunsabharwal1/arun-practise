# Project Management API

A production-ready REST API built with **FastAPI + SQLite** to track 10 concurrent projects — covering cost, revenue, team composition, status, and risk assessment. Structured for future AI integration.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | FastAPI |
| Database | SQLite (async via aiosqlite) |
| ORM | SQLAlchemy 2.0 (async) |
| Validation | Pydantic v2 |
| Server | Uvicorn |
| Config | python-dotenv |

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/arunsabharwal1/arun-practise.git
cd arun-practise
```

### 2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate    # Mac/Linux
# .venv\Scripts\activate     # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env if needed (defaults work for local development)
```

### 5. Seed the database with 10 sample projects
```bash
python seed_data.py
```

### 6. Start the API server
```bash
uvicorn app.main:app --reload
```

The API is now running at **http://localhost:8000**

---

## API Documentation

Interactive Swagger UI: **http://localhost:8000/docs**  
ReDoc UI: **http://localhost:8000/redoc**

---

## API Endpoints

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info and available endpoints |
| GET | `/health` | Simple health check |

---

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects` | List all projects (with team size & open risk count) |
| GET | `/projects/{id}` | Full project detail (financials + team + risks) |
| POST | `/projects` | Create a new project |
| PUT | `/projects/{id}` | Update project details or status |
| DELETE | `/projects/{id}` | Delete a project (cascades all related data) |

**Example — create a project:**
```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "client": "Acme Corp", "status": "active"}'
```

**Project statuses:** `planning` | `active` | `on_hold` | `completed` | `cancelled`

---

### Financials

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{id}/financials` | Get all financial logs (latest first) |
| POST | `/projects/{id}/financials` | Add a financial log entry |
| PUT | `/projects/{id}/financials/{log_id}` | Update a financial log |
| DELETE | `/projects/{id}/financials/{log_id}` | Delete a financial log |

**Example — log financials:**
```bash
curl -X POST http://localhost:8000/projects/1/financials \
  -H "Content-Type: application/json" \
  -d '{"budget": 500000, "actual_cost": 120000, "revenue": 600000}'
```

> Response includes computed `profit_margin` and `budget_utilization` automatically.

---

### Teams

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{id}/team` | List team members (leads first) |
| POST | `/projects/{id}/team` | Add a team member |
| PUT | `/projects/{id}/team/{member_id}` | Update a team member |
| DELETE | `/projects/{id}/team/{member_id}` | Remove a team member |

**Example — add a team member:**
```bash
curl -X POST http://localhost:8000/projects/1/team \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "role": "Developer", "email": "jane@example.com", "is_lead": false, "allocation_percentage": 100}'
```

---

### Risks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{id}/risks` | Get risk registry (with computed risk_level) |
| POST | `/projects/{id}/risks` | Register a new risk |
| PUT | `/projects/{id}/risks/{risk_id}` | Update risk status or mitigation |
| DELETE | `/projects/{id}/risks/{risk_id}` | Delete a risk |

**Example — register a risk:**
```bash
curl -X POST http://localhost:8000/projects/1/risks \
  -H "Content-Type: application/json" \
  -d '{"title": "Scope creep", "probability": "medium", "impact": "high", "mitigation_plan": "Weekly scope review meetings."}'
```

**Risk levels (probability × impact matrix):**

| Probability ↓ / Impact → | Low | Medium | High | Critical |
|--------------------------|-----|--------|------|---------|
| **Low** | low | low | medium | medium |
| **Medium** | low | medium | high | critical |
| **High** | medium | high | critical | critical |
| **Critical** | medium | high | critical | critical |

**Risk statuses:** `open` | `mitigated` | `accepted` | `closed`

---

## Project Structure

```
arun-practise/
├── app/
│   ├── main.py          # FastAPI entry point
│   ├── database.py      # SQLAlchemy async engine & session
│   ├── models.py        # ORM models (Project, FinancialLog, TeamMember, RiskEntry)
│   ├── schemas.py       # Pydantic v2 request/response schemas
│   ├── crud.py          # Database CRUD functions (AI-ready separation)
│   └── routers/
│       ├── projects.py  # /projects endpoints
│       ├── financials.py # /financials endpoints
│       ├── teams.py     # /team endpoints
│       └── risks.py     # /risks endpoints
├── seed_data.py         # Seeds 10 sample projects
├── .env.example         # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=sqlite+aiosqlite:///./projectdb.sqlite
APP_ENV=development
DEBUG=True
SECRET_KEY=your-secret-key-here

# Future AI Integration
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=...
```

> `.env` is in `.gitignore` — never committed to version control.

---

## Future AI Integration

The codebase is structured for easy AI agent integration:
- `app/crud.py` contains pure async functions — callable directly by AI agents without HTTP
- `app/models.py` and `app/schemas.py` are cleanly separated for LLM tool calling
- Planned: `/ai/summarize/{project_id}`, `/ai/risk-analysis`, `/ai/financial-forecast`
