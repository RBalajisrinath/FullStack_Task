"""SQLite storage: leads table seeded from CSV. Specific DB: SQLite (MVP) -> Postgres/Supabase in prod."""
import csv
import pathlib
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "leads.db"
CSV_PATH = ROOT / "data" / "leads.csv"

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY, company TEXT, domain TEXT, industry TEXT,
  city TEXT, country TEXT, employees INTEGER, revenue_k INTEGER,
  contact TEXT, title TEXT, email TEXT, phone TEXT,
  linkedin TEXT, website TEXT, tech_stack TEXT, founded INTEGER
);"""

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force: bool = False):
    if force and DB_PATH.exists():
        DB_PATH.unlink()
    conn = connect()
    conn.executescript(SCHEMA)
    count = conn.execute("SELECT COUNT(*) c FROM leads").fetchone()["c"]
    if count == 0:
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        conn.executemany(
            """INSERT INTO leads (id,company,domain,industry,city,country,employees,revenue_k,
               contact,title,email,phone,linkedin,website,tech_stack,founded)
               VALUES (:id,:company,:domain,:industry,:city,:country,:employees,:revenue_k,
               :contact,:title,:email,:phone,:linkedin,:website,:tech_stack,:founded)""",
            rows,
        )
        conn.commit()
    conn.close()

def fetch_all() -> list[dict]:
    conn = connect()
    rows = [dict(r) for r in conn.execute("SELECT * FROM leads ORDER BY id").fetchall()]
    conn.close()
    return rows
