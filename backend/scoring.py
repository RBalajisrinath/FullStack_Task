"""Transparent 0-100 lead score: Fit (50) + Completeness (30) + Outreach readiness (20)."""
IDEAL_MIN, IDEAL_MAX = 10, 500

def score_lead(lead: dict, verify_info: dict | None = None) -> dict:
    fit = 0
    breakdown = {}
    emp = int(lead.get("employees") or 0)
    # Size fit: 25 pts — sweet spot 10-500 (SMB SaaS, best for Caprae-style value creation)
    if IDEAL_MIN <= emp <= IDEAL_MAX:
        fit += 25; breakdown["size"] = 25
    elif 1 <= emp < IDEAL_MIN:
        fit += 10; breakdown["size"] = 10
    elif emp <= 1500:
        fit += 15; breakdown["size"] = 15
    else:
        fit += 5; breakdown["size"] = 5
    # Revenue proxy: 15 pts
    rev = int(lead.get("revenue_k") or 0)
    if 500 <= rev <= 60000:
        fit += 15; breakdown["revenue"] = 15
    elif rev > 0:
        fit += 8; breakdown["revenue"] = 8
    else:
        breakdown["revenue"] = 0
    # Title seniority: 10 pts
    title = (lead.get("title") or "").lower()
    if any(k in title for k in ("ceo", "founder", "owner", "co-founder")):
        fit += 10; breakdown["seniority"] = 10
    elif any(k in title for k in ("vp", "head", "director", "cmo", "coo")):
        fit += 7; breakdown["seniority"] = 7
    else:
        fit += 4; breakdown["seniority"] = 4
    # Completeness: 30 pts
    comp = 0
    comp += 12 if lead.get("email") else 0
    comp += 8 if lead.get("phone") else 0
    comp += 6 if lead.get("linkedin") else 0
    comp += 4 if lead.get("website") else 0
    breakdown["completeness"] = comp
    # Outreach readiness: 20 pts
    ready = 0
    if verify_info and verify_info.get("email_status") == "valid":
        ready += 14
    elif lead.get("email"):
        ready += 6  # unverified but present
    if verify_info and verify_info.get("phone_status") == "valid":
        ready += 6
    elif lead.get("phone"):
        ready += 3
    breakdown["readiness"] = ready
    total = min(100, fit + comp + ready)
    tier = "A — Prioritize" if total >= 88 else ("B — Good" if total >= 73 else ("C — Nurture" if total >= 55 else "D — Skip"))
    return {"score": total, "tier": tier, "breakdown": breakdown}
