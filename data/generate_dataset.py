"""Generate a synthetic but realistic SaaS-lead dataset (500 rows).
No external deps — stdlib only. Safe to commit (no real PII).
Run: python data/generate_dataset.py
"""
import csv
import random
import pathlib

random.seed(42)
OUT = pathlib.Path(__file__).parent / "leads.csv"

INDUSTRIES = [
    "SaaS - CRM", "SaaS - HR Tech", "SaaS - FinTech", "SaaS - MarTech",
    "SaaS - DevTools", "SaaS - HealthTech", "SaaS - EdTech", "SaaS - E-commerce",
    "SaaS - Cybersecurity", "SaaS - Analytics",
]
CITIES = [
    ("Austin", "USA"), ("New York", "USA"), ("San Francisco", "USA"), ("Glendale", "USA"),
    ("London", "UK"), ("Berlin", "Germany"), ("Toronto", "Canada"), ("Bangalore", "India"),
    ("Singapore", "Singapore"), ("Sydney", "Australia"),
]
FIRST = ["Ava", "Liam", "Maya", "Noah", "Priya", "Sofia", "Ethan", "Lucas", "Amara", "Kenji",
         "Olivia", "Raj", "Elena", "Marcus", "Zoe", "Daniel", "Nina", "Omar", "Hannah", "Vikram"]
LAST = ["Chen", "Patel", "Garcia", "Kim", "Novak", "Sharma", "Muller", "Johnson", "Ali", "Smith",
        "Khan", "Lopez", "Nguyen", "Brown", "Singh", "Weber", "Costa", "Park", "Adams", "Rao"]
TITLES = ["CEO", "Founder", "VP Sales", "Head of Growth", "CMO", "COO", "Sales Director", "RevOps Manager"]
TECH = ["React+Node", "Python+Django", "Rails", "Go+K8s", "PHP+Laravel", "Java+Spring", ".NET+Azure"]
COMPANY_ADJ = ["Bright", "Swift", "Clear", "Prime", "Nova", "Blue", "Hyper", "Smart", "Rapid", "Solid"]
COMPANY_NOUN = ["Stack", "Flow", "Desk", "Loop", "Base", "Pilot", "Scale", "Sync", "Grid", "Forge"]
DISPOSABLE = ["mailinator.com", "tempmail.com", "10minutemail.com"]
ROLE_PREFIX = ["info", "support", "admin", "sales", "hello"]


def company_name(i: int) -> str:
    return f"{random.choice(COMPANY_ADJ)}{random.choice(COMPANY_NOUN)} {random.choice(['Labs', 'HQ', 'Systems', 'Cloud', 'AI'])}"


def main(n: int = 500):
    rows = []
    seen_domains = set()
    for i in range(1, n + 1):
        cname = company_name(i)
        slug = "".join(c for c in cname.lower() if c.isalnum())[:16] + str(i)
        domain = f"{slug}.com"
        # force a few duplicates + bad emails to demo dedupe/verify
        if i % 97 == 0 and rows:
            domain = rows[-3]["domain"]  # intentional duplicate domain
        if i % 61 == 0:
            domain = domain  # keep, bad email below
        industry = random.choice(INDUSTRIES)
        city, country = random.choice(CITIES)
        employees = int(random.choice([
            random.randint(2, 15), random.randint(11, 60),
            random.randint(51, 250), random.randint(200, 1200),
        ]))
        revenue_k = int(employees * random.uniform(60, 220))  # rough $k ARR proxy
        contact = f"{random.choice(FIRST)} {random.choice(LAST)}"
        title = random.choice(TITLES)
        if i % 61 == 0:
            email = f"{random.choice(ROLE_PREFIX)}@{random.choice(DISPOSABLE)}"  # low quality
        elif i % 23 == 0:
            email = f"{contact.split()[0].lower()}.{contact.split()[1].lower()}@{domain}".replace(" ", "")
            email = email.replace("@", "@bad-domain-")  # malformed-ish
        elif random.random() < 0.12:
            email = ""  # missing email
        else:
            email = f"{contact.split()[0].lower()}.{contact.split()[1].lower()}@{domain}".replace(" ", "")
        phone = "" if random.random() < 0.25 else f"+1-{random.randint(200,989)}-{random.randint(200,989)}-{random.randint(1000,9999)}"
        linkedin = "" if random.random() < 0.2 else f"https://linkedin.com/company/{slug}"
        website = f"https://{domain}"
        tech = random.choice(TECH)
        founded = random.randint(2012, 2024)
        rows.append({
            "id": i, "company": cname, "domain": domain, "industry": industry,
            "city": city, "country": country, "employees": employees,
            "revenue_k": revenue_k, "contact": contact, "title": title,
            "email": email, "phone": phone, "linkedin": linkedin,
            "website": website, "tech_stack": tech, "founded": founded,
        })
    # add one exact duplicate row to demo dedupe
    rows.append(dict(rows[5], id=n + 1))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows -> {OUT}")


if __name__ == "__main__":
    main()
