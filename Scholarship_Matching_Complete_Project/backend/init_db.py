"""
init_db.py
Creates scholarships.db (SQLite) and seeds it with tables + sample scheme data.
Run once: python init_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "scholarships.db")


def create_tables(conn):
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scholarship_scheme (
        scheme_id INTEGER PRIMARY KEY AUTOINCREMENT,
        scheme_name TEXT NOT NULL,
        provider TEXT,
        income_limit REAL,              -- NULL means no income cap
        eligible_category TEXT,         -- comma separated, or 'All'
        min_marks REAL,                 -- 0 if none
        state_applicable TEXT,          -- 'All India' or a specific state
        course_applicable TEXT,         -- 'All' or specific course
        gender_restriction TEXT,        -- 'All' / 'Female' / 'Male'
        deadline TEXT,                  -- ISO date string
        documents_required TEXT,
        description TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_profile (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        income REAL,
        category TEXT,
        tenth_pct REAL,
        twelfth_pct REAL,
        state TEXT,
        course TEXT,
        gender TEXT,
        class_year TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS application_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        scheme_id INTEGER,
        match_score REAL,
        recommended_on TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_scheme_text (
        raw_id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_text TEXT,
        source_url TEXT,
        parsed INTEGER DEFAULT 0
    )
    """)
    conn.commit()


SEED_SCHEMES = [
    # name, provider, income_limit, category, min_marks, state, course, gender, deadline, docs, description
    ("State Merit-cum-Means Scholarship", "State Government", 250000, "All", 60, "Tamil Nadu", "All", "All", "2026-09-30",
     "Income certificate, Mark sheet, Aadhar card",
     "For meritorious students from economically weaker sections of Tamil Nadu."),
    ("OBC Post-Matric Scholarship", "Central Government", 100000, "OBC", 50, "All India", "All", "All", "2026-10-15",
     "Caste certificate, Income certificate, Mark sheet",
     "Central scheme supporting OBC students pursuing post-matriculation studies."),
    ("National Means-cum-Merit Scholarship", "Central Government", 150000, "All", 55, "All India", "All", "All", "2026-10-20",
     "Income certificate, Class 8 mark sheet",
     "Merit scholarship for economically weaker students to prevent dropout."),
    ("SC/ST Post-Matric Scholarship", "Central Government", 250000, "SC,ST", 50, "All India", "All", "All", "2026-11-01",
     "Caste certificate, Income certificate",
     "Financial assistance for SC/ST students pursuing post-matric education."),
    ("Minority Community Scholarship", "Central Government", 200000, "Minority", 50, "All India", "All", "All", "2026-10-31",
     "Minority certificate, Income certificate, Mark sheet",
     "Supports students belonging to notified minority communities."),
    ("Corporate Foundation Engineering Scholarship", "Private Trust", 600000, "All", 70, "All India", "Engineering", "All", "2026-11-05",
     "Admission letter, Mark sheet, Income proof",
     "Merit-based scholarship for engineering students from a private CSR foundation."),
    ("EWS Scholarship for Higher Education", "State Government", 800000, "EWS", 60, "Tamil Nadu", "All", "All", "2026-12-10",
     "EWS certificate, Income certificate, Mark sheet",
     "Supports Economically Weaker Section students in higher education."),
    ("Girl Child Education Scholarship", "NGO", 300000, "All", 50, "All India", "All", "Female", "2026-11-15",
     "Income certificate, Mark sheet, Bank passbook",
     "Encourages higher education among girl students from low-income families."),
    ("Differently-Abled Student Scholarship", "Central Government", 250000, "PwD", 40, "All India", "All", "All", "2026-12-01",
     "Disability certificate, Income certificate",
     "Financial support for differently-abled students pursuing higher education."),
    ("State Education Trust Scholarship", "Private Trust", 400000, "All", 65, "Tamil Nadu", "All", "All", "2026-12-20",
     "Mark sheet, Income certificate, Recommendation letter",
     "State-level private trust scholarship for meritorious students."),
    ("Central Sector Scheme of Scholarship", "Central Government", 800000, "All", 80, "All India", "All", "All", "2026-10-31",
     "Class 12 mark sheet, Income certificate",
     "Merit-based scholarship for top-performing Class 12 students entering college."),
    ("Ishan Uday Special Scholarship", "Central Government", 450000, "All", 50, "North East States", "All", "All", "2026-11-30",
     "Domicile certificate, Income certificate, Mark sheet",
     "Special scholarship scheme for students from North Eastern states."),
    ("AICTE Pragati Scholarship for Girls", "AICTE (Central Govt.)", 800000, "All", 0, "All India", "Engineering,Diploma", "Female", "2026-11-10",
     "Admission proof, Income certificate",
     "Supports girl students pursuing technical education (AICTE approved institutes)."),
    ("AICTE Saksham Scholarship", "AICTE (Central Govt.)", 800000, "PwD", 0, "All India", "Engineering,Diploma", "All", "2026-11-10",
     "Disability certificate, Admission proof, Income certificate",
     "Supports differently-abled students pursuing technical education."),
    ("State Toppers Merit Scholarship", "State Government", None, "All", 90, "Tamil Nadu", "All", "All", "2026-09-15",
     "Mark sheet, Rank certificate",
     "No income restriction; purely merit-based for state examination toppers."),
    ("Sports Quota Scholarship", "State Government", 300000, "All", 0, "Tamil Nadu", "All", "All", "2026-12-05",
     "Sports certificate, Income certificate",
     "Supports state-level and national-level sportspersons in higher education."),
    ("First Generation Learner Scholarship", "NGO", 250000, "All", 55, "All India", "All", "All", "2026-11-25",
     "Income certificate, Family education declaration, Mark sheet",
     "Supports students who are the first in their family to pursue higher education."),
    ("Engineering Excellence Award", "Private Trust", 500000, "All", 75, "All India", "Engineering", "All", "2026-12-15",
     "Mark sheet, Income certificate, Admission letter",
     "Rewards academic excellence among engineering undergraduates."),
    ("Rural Students Upliftment Scholarship", "State Government", 150000, "All", 50, "Tamil Nadu", "All", "All", "2026-11-20",
     "Rural domicile certificate, Income certificate",
     "Targeted at students from rural and remote parts of the state."),
    ("Single Girl Child Scholarship", "Central Government", 600000, "All", 50, "All India", "All", "Female", "2026-12-01",
     "Single girl child certificate, Income certificate, Mark sheet",
     "Supports only/single girl children of a family in pursuing education."),
    ("Defence Personnel Wards Scholarship", "Central Government", None, "All", 0, "All India", "All", "All", "2026-12-31",
     "Service certificate of parent, Mark sheet",
     "For wards of serving/ex-servicemen of the Indian Armed Forces."),
    ("Post Graduate Merit Scholarship", "Central Government", 600000, "All", 60, "All India", "All", "All", "2026-10-25",
     "Graduation mark sheet, Income certificate",
     "Supports meritorious students pursuing postgraduate studies."),
]


def seed_data(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM scholarship_scheme")
    if cur.fetchone()[0] > 0:
        print("Scheme data already seeded, skipping.")
        return
    cur.executemany("""
        INSERT INTO scholarship_scheme
        (scheme_name, provider, income_limit, eligible_category, min_marks,
         state_applicable, course_applicable, gender_restriction, deadline,
         documents_required, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, SEED_SCHEMES)
    conn.commit()
    print(f"Seeded {len(SEED_SCHEMES)} scholarship schemes.")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    seed_data(conn)
    conn.close()
    print(f"Database ready at {DB_PATH}")
