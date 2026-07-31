"""
app.py
Flask backend for the AI-Based Scholarship Eligibility Matching System.
Serves both the REST API and the static frontend, so the whole project
deploys as a single free-tier web service (Render / Railway / PythonAnywhere).
"""
import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory, Response

from rule_engine import check_eligibility, filter_eligible_schemes
from ranking_engine import rank_schemes, DEFAULT_WEIGHTS
from nlp_parser import parse_eligibility_text
from autofill import generate_summary_text
import init_db

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "scholarships.db")
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_db_ready():
    """Auto-create + seed the DB on first run (handy for free-tier deploys
    where you can't always run a separate init step)."""
    conn = sqlite3.connect(DB_PATH)
    init_db.create_tables(conn)
    init_db.seed_data(conn)
    conn.close()


# ---------------------------------------------------------------
# FRONTEND
# ---------------------------------------------------------------
@app.route("/")
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, "index.html")


# ---------------------------------------------------------------
# API: match schemes for a student profile
# ---------------------------------------------------------------
@app.route("/api/match", methods=["POST"])
def match_scholarships():
    data = request.get_json(force=True) or {}

    required = ["income", "category", "twelfth_pct", "state", "course"]
    missing = [f for f in required if f not in data or data[f] in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    student = {
        "name": data.get("name", "Student"),
        "income": float(data["income"]),
        "category": str(data["category"]),
        "tenth_pct": float(data["tenth_pct"]) if data.get("tenth_pct") not in (None, "") else None,
        "twelfth_pct": float(data["twelfth_pct"]),
        "state": str(data["state"]),
        "course": str(data["course"]),
        "gender": data.get("gender", ""),
    }

    conn = get_db()
    all_schemes = conn.execute("SELECT * FROM scholarship_scheme").fetchall()

    eligible = filter_eligible_schemes(student, all_schemes)
    ranked = rank_schemes(student, eligible, DEFAULT_WEIGHTS)

    # Also compute why each ineligible scheme was excluded (for transparency)
    excluded = []
    for scheme in all_schemes:
        ok, reasons = check_eligibility(student, scheme)
        if not ok:
            excluded.append({"scheme_name": scheme["scheme_name"], "reasons": reasons})

    # log matches
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO student_profile (name, income, category, tenth_pct, twelfth_pct, state, course, gender) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (student["name"], student["income"], student["category"], student["tenth_pct"],
         student["twelfth_pct"], student["state"], student["course"], student["gender"]),
    )
    student_id = cur.lastrowid
    for item in ranked:
        cur.execute(
            "INSERT INTO application_log (student_id, scheme_id, match_score) VALUES (?, ?, ?)",
            (student_id, item["scheme"]["scheme_id"], item["match_score"]),
        )
    conn.commit()
    conn.close()

    return jsonify({
        "student_id": student_id,
        "eligible_count": len(ranked),
        "results": ranked,
        "excluded_count": len(excluded),
        "excluded": excluded,
    })


# ---------------------------------------------------------------
# API: auto-fill summary sheet (plain text download)
# ---------------------------------------------------------------
@app.route("/api/summary", methods=["POST"])
def summary_sheet():
    data = request.get_json(force=True) or {}
    student = data.get("student", {})
    ranked_results = data.get("results", [])

    text = generate_summary_text(student, ranked_results)
    return Response(
        text,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=scholarship_summary.txt"},
    )


# ---------------------------------------------------------------
# API: list all schemes (admin / browse view)
# ---------------------------------------------------------------
@app.route("/api/schemes", methods=["GET"])
def list_schemes():
    conn = get_db()
    rows = conn.execute("SELECT * FROM scholarship_scheme ORDER BY scheme_name").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ---------------------------------------------------------------
# API: add a scheme manually, or from raw text via the NLP parser
# ---------------------------------------------------------------
@app.route("/api/schemes", methods=["POST"])
def add_scheme():
    data = request.get_json(force=True) or {}

    if data.get("raw_text"):
        parsed = parse_eligibility_text(data["raw_text"])
        scheme_name = data.get("scheme_name", "Untitled Scheme")
        provider = data.get("provider", "Unknown")
        deadline = data.get("deadline")
        documents = data.get("documents_required", "")
        income_limit = parsed["income_limit"]
        eligible_category = parsed["eligible_category"]
        min_marks = parsed["min_marks"]
        state_applicable = parsed["state_applicable"]
        course_applicable = data.get("course_applicable", "All")
        gender_restriction = data.get("gender_restriction", "All")
        description = data["raw_text"]
    else:
        scheme_name = data.get("scheme_name")
        provider = data.get("provider", "")
        income_limit = data.get("income_limit")
        eligible_category = data.get("eligible_category", "All")
        min_marks = data.get("min_marks", 0)
        state_applicable = data.get("state_applicable", "All India")
        course_applicable = data.get("course_applicable", "All")
        gender_restriction = data.get("gender_restriction", "All")
        deadline = data.get("deadline")
        documents = data.get("documents_required", "")
        description = data.get("description", "")

    if not scheme_name:
        return jsonify({"error": "scheme_name is required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO scholarship_scheme
        (scheme_name, provider, income_limit, eligible_category, min_marks,
         state_applicable, course_applicable, gender_restriction, deadline,
         documents_required, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (scheme_name, provider, income_limit, eligible_category, min_marks,
          state_applicable, course_applicable, gender_restriction, deadline,
          documents, description))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({"scheme_id": new_id, "message": "Scheme added successfully"}), 201


# ---------------------------------------------------------------
# API: simple analytics (admin dashboard)
# ---------------------------------------------------------------
@app.route("/api/analytics", methods=["GET"])
def analytics():
    conn = get_db()
    total_students = conn.execute("SELECT COUNT(*) c FROM student_profile").fetchone()["c"]
    total_schemes = conn.execute("SELECT COUNT(*) c FROM scholarship_scheme").fetchone()["c"]
    top_matches = conn.execute("""
        SELECT s.scheme_name, COUNT(*) as match_count, AVG(a.match_score) as avg_score
        FROM application_log a JOIN scholarship_scheme s ON a.scheme_id = s.scheme_id
        GROUP BY a.scheme_id ORDER BY match_count DESC LIMIT 5
    """).fetchall()
    conn.close()
    return jsonify({
        "total_students": total_students,
        "total_schemes": total_schemes,
        "top_matched_schemes": [dict(r) for r in top_matches],
    })


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    ensure_db_ready()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
else:
    # also runs when started via gunicorn on a free host
    ensure_db_ready()
