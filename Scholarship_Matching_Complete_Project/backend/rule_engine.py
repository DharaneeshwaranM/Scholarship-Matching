"""
rule_engine.py
Hard, transparent eligibility rules. A scheme survives only if every
applicable condition is satisfied. Each rejection records a human-readable
reason so the frontend can explain *why* a scheme was excluded.
"""


def check_eligibility(student, scheme):
    """
    student: dict with income, category, tenth_pct, twelfth_pct, state, course, gender
    scheme: sqlite3.Row (or dict) for a scholarship_scheme row
    Returns (is_eligible: bool, reasons: list[str])
    """
    reasons = []

    # Income condition
    if scheme["income_limit"] is not None:
        if student["income"] > scheme["income_limit"]:
            reasons.append(
                f"Family income (₹{student['income']:,.0f}) exceeds the scheme's "
                f"limit of ₹{scheme['income_limit']:,.0f}"
            )

    # Category condition
    elig_cat = (scheme["eligible_category"] or "All").strip()
    if elig_cat.lower() != "all":
        allowed = [c.strip().lower() for c in elig_cat.split(",")]
        if student["category"].strip().lower() not in allowed:
            reasons.append(
                f"Restricted to category: {elig_cat} (your category: {student['category']})"
            )

    # Marks condition (checked against 12th / qualifying-exam percentage)
    if scheme["min_marks"] and student["twelfth_pct"] < scheme["min_marks"]:
        reasons.append(
            f"Requires minimum {scheme['min_marks']}% in 12th / qualifying exam "
            f"(your 12th marks: {student['twelfth_pct']}%)"
        )

    # State condition
    state_app = (scheme["state_applicable"] or "All India").strip()
    if state_app.lower() not in ("all india",):
        if student["state"].strip().lower() != state_app.strip().lower():
            reasons.append(
                f"Only open to students domiciled in {state_app} (your state: {student['state']})"
            )

    # Course condition
    course_app = (scheme["course_applicable"] or "All").strip()
    if course_app.lower() != "all":
        allowed_courses = [c.strip().lower() for c in course_app.split(",")]
        if student["course"].strip().lower() not in allowed_courses:
            reasons.append(
                f"Only open to courses: {course_app} (your course: {student['course']})"
            )

    # Gender condition
    gender_app = (scheme["gender_restriction"] or "All").strip()
    if gender_app.lower() != "all":
        student_gender = (student.get("gender") or "").strip().lower()
        if student_gender != gender_app.lower():
            reasons.append(f"Only open to: {gender_app} applicants")

    return (len(reasons) == 0, reasons)


def filter_eligible_schemes(student, all_schemes):
    """Returns list of scheme dicts that pass all hard conditions."""
    eligible = []
    for scheme in all_schemes:
        ok, _ = check_eligibility(student, scheme)
        if ok:
            eligible.append(scheme)
    return eligible
