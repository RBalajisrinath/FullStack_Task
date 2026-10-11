"""SaaSquatch v2 — AI-Ready Lead Engine API. Run: python -m uvicorn backend.main:app --reload --port 8000"""
import csv
import io
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend.database import init_db, fetch_all
from backend.scoring import score_lead
from backend.verify import verify_lead, dedupe

app = FastAPI(title="SaaSquatch v2 — AI-Ready Lead Engine", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

init_db()
LEADS: list[dict] = fetch_all()

# Simple in-process cache: key -> filtered+scored payload (60s TTL omitted for brevity — LRU by key)
_CACHE: dict = {}

def enriched(verify: bool = False) -> list[dict]:
    out = []
    for L in LEADS:
        v = verify_lead(L) if verify else {"email_status": "unknown", "phone_status": "unknown"}
        s = score_lead(L, v if verify else None)
        out.append({**L, "verify": v, "score": s["score"], "tier": s["tier"], "breakdown": s["breakdown"]})
    return out

def apply_filters(rows, q, industry, country, min_emp, max_emp, min_score, tier):
    q = (q or "").lower()
    res = []
    for r in rows:
        if q and q not in f"{r['company']} {r['domain']} {r['contact']} {r['email']}".lower():
            continue
        if industry and r["industry"] != industry:
            continue
        if country and r["country"] != country:
            continue
        if min_emp and (r["employees"] or 0) < min_emp:
            continue
        if max_emp and (r["employees"] or 0) > max_emp:
            continue
        if min_score and r["score"] < min_score:
            continue
        if tier and r["tier"] != tier:
            continue
        res.append(r)
    return res

@app.get("/api/health")
def health():
    return {"ok": True, "leads": len(LEADS)}

@app.get("/api/facets")
def facets():
    return {
        "industries": sorted({r["industry"] for r in LEADS}),
        "countries": sorted({r["country"] for r in LEADS}),
        "tiers": ["A — Prioritize", "B — Good", "C — Nurture", "D — Skip"],
    }

@app.get("/api/stats")
def stats():
    rows = enriched(verify=True)
    by_ind, by_tier = {}, {}
    for r in rows:
        by_ind[r["industry"]] = by_ind.get(r["industry"], 0) + 1
        by_tier[r["tier"]] = by_tier.get(r["tier"], 0) + 1
    valid = sum(1 for r in rows if r["verify"]["email_status"] == "valid")
    return {"total": len(rows), "avg_score": round(sum(r["score"] for r in rows) / max(1, len(rows)), 1),
            "valid_emails": valid, "by_industry": by_ind, "by_tier": by_tier}

@app.get("/api/leads")
def list_leads(q: str = "", industry: str = "", country: str = "", tier: str = "",
               min_emp: int = 0, max_emp: int = 0, min_score: int = 0,
               sort: str = "score_desc", page: int = 1, page_size: int = 25,
               verify: bool = False, dedupe_on: bool = True):
    key = (q, industry, country, tier, min_emp, max_emp, min_score, sort, verify, dedupe_on)
    if key in _CACHE:
        rows = _CACHE[key]
    else:
        rows = enriched(verify=verify)
        if dedupe_on:
            rows, _ = dedupe(rows)
        _CACHE[key] = rows
    rows = apply_filters(rows, q, industry, country, min_emp or 0, max_emp or 0, min_score, tier)
    reverse = sort.endswith("desc")
    skey = {"score_desc": "score", "score_asc": "score", "employees_desc": "employees",
            "employees_asc": "employees", "revenue_desc": "revenue_k"}.get(sort, "score")
    rows = sorted(rows, key=lambda r: (r.get(skey) or 0), reverse=reverse)
    total = len(rows)
    start = (page - 1) * page_size
    return {"total": total, "page": page, "page_size": page_size,
            "removed_duplicates": len(enriched(False)) - len(_CACHE[key]),
            "items": rows[start:start + page_size]}

@app.get("/api/leads/{lead_id}")
def get_lead(lead_id: int):
    row = next((L for L in LEADS if L["id"] == lead_id), None)
    if not row:
        return {"error": "not found"}
    v = verify_lead(row)
    s = score_lead(row, v)
    return {**row, "verify": v, "score": s["score"], "tier": s["tier"], "breakdown": s["breakdown"]}

@app.post("/api/verify")
def verify_batch(payload: dict):
    ids: list = payload.get("ids", [])
    rows = [L for L in LEADS if not ids or L["id"] in ids][:500]
    return {"results": [{**L, "verify": verify_lead(L), **score_lead(L, verify_lead(L))} for L in rows]}

@app.get("/api/export")
def export(q: str = "", industry: str = "", country: str = "", min_score: int = 0, verify: bool = True):
    rows = enriched(verify=verify)
    rows, removed = dedupe(rows)
    rows = apply_filters(rows, q, industry, country, 0, 0, min_score, "")
    rows = sorted(rows, key=lambda r: r["score"], reverse=True)
    buf = io.StringIO()
    fields = ["id", "company", "domain", "industry", "city", "country", "employees", "revenue_k",
              "contact", "title", "email", "phone", "linkedin", "website", "score", "tier"]
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=saasquatch_v2_leads.csv",
                                      "X-Deduped-Removed": str(removed)})

# Serve the static frontend from the same origin (zero-CORS demo)
FRONT = Path(__file__).resolve().parent.parent / "frontend"
if FRONT.exists():
    app.mount("/", StaticFiles(directory=str(FRONT), html=True), name="frontend")
