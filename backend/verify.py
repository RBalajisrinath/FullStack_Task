"""Offline email/phone validation + dedupe. No network calls (demo-safe)."""
import re
from difflib import SequenceMatcher

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
DISPOSABLE = {"mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com", "trashmail.com"}
ROLE_PREFIXES = {"info", "support", "admin", "sales", "hello", "contact", "noreply"}
PHONE_RE = re.compile(r"^\+?[\d\-\s().]{7,20}$")

def verify_email(email: str) -> dict:
    e = (email or "").strip().lower()
    if not e:
        return {"email_status": "missing", "reason": "no email on record"}
    if not EMAIL_RE.match(e):
        return {"email_status": "invalid", "reason": "fails RFC-style syntax check"}
    domain = e.split("@")[1]
    local = e.split("@")[0]
    if domain in DISPOSABLE or "bad-domain" in domain:
        return {"email_status": "invalid", "reason": f"disposable/blocked domain ({domain})"}
    if local in ROLE_PREFIXES:
        return {"email_status": "risky", "reason": "role-based address, low reply rate"}
    if len(local) < 2 or ".." in e:
        return {"email_status": "risky", "reason": "suspicious local part"}
    return {"email_status": "valid", "reason": "syntax + domain checks passed"}

def verify_phone(phone: str) -> dict:
    p = (phone or "").strip()
    if not p:
        return {"phone_status": "missing", "reason": "no phone on record"}
    digits = re.sub(r"\D", "", p)
    if not PHONE_RE.match(p) or not (7 <= len(digits) <= 15):
        return {"phone_status": "invalid", "reason": "bad format/length"}
    return {"phone_status": "valid", "reason": "format check passed"}

def verify_lead(lead: dict) -> dict:
    em = verify_email(lead.get("email", ""))
    ph = verify_phone(lead.get("phone", ""))
    out = {**em, **ph}
    out["ok"] = em["email_status"] in ("valid", "risky") or ph["phone_status"] == "valid"
    return out

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def dedupe(leads: list[dict]) -> tuple[list[dict], int]:
    """Dedupe by (normalized email) then (domain + fuzzy company). Returns (unique, removed)."""
    seen_email, seen_key, unique = set(), set(), []
    removed = 0
    for L in leads:
        em = (L.get("email") or "").strip().lower()
        dom = (L.get("domain") or "").strip().lower()
        comp = _norm(L.get("company", ""))
        if em and em in seen_email:
            removed += 1
            continue
        key = (dom, comp[:12])
        dup = False
        if dom and key in seen_key:
            dup = True
        else:  # fuzzy company fallback
            for u in unique[-50:]:
                if _norm(u.get("company", ""))[:12] == comp[:12] and SequenceMatcher(None, u.get("company", ""), L.get("company", "")).ratio() > 0.92:
                    dup = True
                    break
        if dup:
            removed += 1
            continue
        if em:
            seen_email.add(em)
        if dom:
            seen_key.add(key)
        unique.append(L)
    return unique, removed
