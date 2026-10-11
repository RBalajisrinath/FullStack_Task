# SaaSquatch v2 — AI-Ready Lead Engine (Caprae 5-Hour Challenge)

Rebuild of [saasquatchleads.com](https://www.saasquatchleads.com/) focused on the two highest-ROI gaps: **(1) transparent lead prioritization** and **(2) data-quality (verify + dedupe + CRM-ready export)**.

Demo: run backend → open `http://localhost:8000` (API + UI same origin).

## Why these 2 features
SaaSquatch scrapes well but sales teams drown in flat lists. Real value = **call the right 20% first with working emails**. So:
1. **Smart Score (0-100 + A/B/C/D tier)** — Fit 50 (size 25 + revenue 15 + seniority 10) + Completeness 30 + Readiness 20. SMB SaaS 10–500 emp favored (Caprae-style buy-and-build sweet spot). Fully explainable in UI.
2. **Verify + Dedupe + Export** — offline email syntax + disposable-domain blocklist + role-address penalty, phone format check, normalized-email → domain+company fuzzy dedupe, one-click CSV export with current filters.

## Quickstart
```powershell
python data/generate_dataset.py
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --port 8000
# open http://localhost:8000
# API docs: http://localhost:8000/docs
```

## API
- `GET /api/health`, `/api/facets`, `/api/stats`
- `GET /api/leads?q=&industry=&country=&tier=&min_emp=&max_emp=&min_score=&sort=score_desc&page=1&page_size=25&verify=true&dedupe_on=true`
- `GET /api/leads/{id}`, `POST /api/verify {"ids":[...]}`, `GET /api/export?...` (CSV download)

Try: `/api/leads?min_score=73&verify=true` → only A/B outreach-ready; `/api/export?industry=SaaS%20-%20FinTech`.

## Architecture (as required)
- **Stack:** Python 3.14 FastAPI + stdlib sqlite3/csv, vanilla JS + Tailwind CDN frontend. No build step.
- **Data storage:** SQLite `data/leads.db` seeded from `data/leads.csv` (501 synthetic rows, no real PII). Prod path: Postgres on Supabase/RDS — same SQL, swap connection string; add Alembic migration.
- **Caching/perf:** in-process dict cache on (filters+verify+dedupe) key, pagination (25/page), sorted server-side, debounced UI; stateless so horizontally scalable. Next: Redis 60s TTL + CDN for frontend.
- **Hosting:** single FastAPI process serves API + static `frontend/` (zero-CORS). Static vs serverless: UI is static (Vercel/Netlify), API serverless-ready (Vercel function / Render / Fly). Deploy: `uvicorn backend.main:app` behind Gunicorn; Docker + GitHub Actions → Vercel (frontend) + Render (API) + Supabase (DB).
- **Cloud:** AWS/GCP-agnostic; reference: Vercel (frontend) + Render/Fly (API) + Supabase Postgres + S3 for CSV exports.

## Ethics
Synthetic seed data only; verify is format/blocklist heuristics (no SMTP probing); scraper path would respect robots.txt + rate limits + opt-out.
