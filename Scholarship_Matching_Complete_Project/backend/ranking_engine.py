"""
ranking_engine.py
Weighted match-score ranking for schemes that already passed rule_engine's
hard eligibility filter. No heavy ML library required -- pure Python math,
so it stays within free hosting resource limits.
"""
from datetime import datetime, date

DEFAULT_WEIGHTS = {"w1": 0.35, "w2": 0.30, "w3": 0.20, "w4": 0.15}


def _clip(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def income_margin_score(student_income, income_limit):
    """Higher score when the student is comfortably within the income cap."""
    if income_limit is None or income_limit == 0:
        return 1.0
    margin = (income_limit - student_income) / income_limit
    return _clip(0.5 + margin)  # midpoint-shifted so borderline cases still score ~0.5


def marks_margin_score(student_marks, min_marks):
    """Higher score when the student clears the minimum marks by a wider margin."""
    if not min_marks:
        return 0.8  # no marks requirement -> decent default score
    if student_marks >= 100:
        return 1.0
    margin = (student_marks - min_marks) / max(1, (100 - min_marks))
    return _clip(0.5 + margin)


def category_specificity_score(eligible_category):
    """Schemes specifically targeted at the student's category score higher
    (less competitive) than fully open 'All' schemes."""
    return 1.0 if (eligible_category or "All").strip().lower() != "all" else 0.6


def deadline_urgency_score(deadline_str, today=None):
    """Schemes with a nearer deadline get a small boost so they aren't missed."""
    if not deadline_str:
        return 0.5
    today = today or date.today()
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    except ValueError:
        return 0.5
    days_left = (deadline - today).days
    if days_left < 0:
        return 0.0  # already expired
    if days_left <= 30:
        return 1.0
    if days_left <= 90:
        return 0.7
    return 0.4


def compute_match_score(student, scheme, weights=None):
    weights = weights or DEFAULT_WEIGHTS
    income_score = income_margin_score(student["income"], scheme["income_limit"])
    marks_score = marks_margin_score(student["twelfth_pct"], scheme["min_marks"])
    cat_score = category_specificity_score(scheme["eligible_category"])
    urgency_score = deadline_urgency_score(scheme["deadline"])

    score = (
        weights["w1"] * income_score
        + weights["w2"] * marks_score
        + weights["w3"] * cat_score
        + weights["w4"] * urgency_score
    )
    return round(score, 4)


def rank_schemes(student, eligible_schemes, weights=None):
    scored = [
        {"scheme": dict(scheme), "match_score": compute_match_score(student, scheme, weights)}
        for scheme in eligible_schemes
    ]
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    for i, item in enumerate(scored, start=1):
        item["rank"] = i
    return scored
