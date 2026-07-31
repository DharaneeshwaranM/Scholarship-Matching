"""
nlp_parser.py
Lightweight, dependency-free NLP-style parser that extracts structured
eligibility fields from unstructured scheme description text.

Deliberately avoids heavy libraries (spaCy/transformers) so the whole
backend stays under ~50MB and runs comfortably on free-tier hosting
(Render/Railway/PythonAnywhere free plans, 512MB RAM instances etc.).
Uses regex + keyword gazetteers, which is a legitimate, classical
information-extraction approach for this kind of semi-structured text.
"""
import re

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh",
]

CATEGORY_KEYWORDS = ["SC", "ST", "OBC", "EWS", "General", "Minority", "PwD"]

INCOME_PATTERN = re.compile(r"Rs\.?\s?([\d,]+)|₹\s?([\d,]+)", re.IGNORECASE)
MARKS_PATTERN = re.compile(r"(\d{2,3})\s?%")


def parse_eligibility_text(raw_text: str) -> dict:
    """
    Extracts income_limit, min_marks, eligible_category and state_applicable
    from a free-form eligibility paragraph.
    """
    text = raw_text or ""

    # --- income ---
    income_limit = None
    m = INCOME_PATTERN.search(text)
    if m:
        raw_num = m.group(1) or m.group(2)
        try:
            income_limit = int(raw_num.replace(",", ""))
        except ValueError:
            income_limit = None

    # --- marks ---
    min_marks = 0
    m2 = MARKS_PATTERN.search(text)
    if m2:
        min_marks = int(m2.group(1))

    # --- category ---
    found_categories = [c for c in CATEGORY_KEYWORDS if re.search(rf"\b{c}\b", text, re.IGNORECASE)]
    eligible_category = ",".join(found_categories) if found_categories else "All"

    # --- state ---
    found_states = [s for s in INDIAN_STATES if s.lower() in text.lower()]
    state_applicable = found_states[0] if found_states else "All India"

    return {
        "income_limit": income_limit,
        "min_marks": min_marks,
        "eligible_category": eligible_category,
        "state_applicable": state_applicable,
        "parse_confidence": _confidence(income_limit, min_marks, found_categories, found_states),
    }


def _confidence(income_limit, min_marks, categories, states):
    """A crude confidence signal: how many fields were actually detected."""
    hits = sum([income_limit is not None, min_marks > 0, bool(categories), bool(states)])
    return round(hits / 4, 2)


if __name__ == "__main__":
    sample = ("Applicants whose family income does not exceed Rs. 2,50,000 per "
               "annum and who have scored a minimum of 60% in their qualifying "
               "examination, and are domiciled in Tamil Nadu, are eligible to apply "
               "under the OBC category.")
    print(parse_eligibility_text(sample))
