import json
from datetime import datetime
from src.config import STARTUP_FOUNDING_YEARS, IT_CONSULTING_COMPANIES

def _parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m")
        except ValueError:
            return None

def _is_consulting_company(company_name):
    """Returns True if the given company name is a known IT consulting/services firm."""
    if not company_name:
        return False
    name_lower = company_name.lower().strip()
    for cc in IT_CONSULTING_COMPANIES:
        if cc in name_lower:
            return True
    return False

# ─────────────────────────────────────────────────────────────────────────────
# HONEYPOT DETECTION (General-purpose: independent of any JD)
# ─────────────────────────────────────────────────────────────────────────────

def check_is_honeypot(cand):
    """
    Detects synthetic/impossible candidate profiles (honeypots).
    These checks are JD-agnostic — they flag data integrity violations.

    Returns:
        (True, reason_str) if the candidate is a honeypot
        (False, None)      if the candidate is legitimate
    """
    yoe = cand["profile"]["years_of_experience"]

    # Rule 1: Any single job duration (in years) exceeds total stated YOE + 0.1 buffer
    for job in cand.get("career_history", []):
        job_dur_years = job.get("duration_months", 0) / 12.0
        if job_dur_years > yoe + 0.1:
            return True, (
                f"Job duration mismatch: '{job.get('company')}' role lasted "
                f"{job_dur_years:.1f} yrs but total YOE is only {yoe} yrs"
            )

    # Rule 2: Skill listed as 'expert' proficiency with 0 months of usage
    for skill in cand.get("skills", []):
        if skill.get("proficiency") == "expert" and skill.get("duration_months", 0) == 0:
            return True, f"Expert skill with 0 duration: '{skill.get('name')}'"

    # Rule 3: Employment at a modern AI startup before that startup was founded
    for job in cand.get("career_history", []):
        company = job.get("company", "")
        founding_year = STARTUP_FOUNDING_YEARS.get(company)
        if founding_year is not None:
            start_date = _parse_date(job.get("start_date"))
            if start_date and start_date.year < founding_year:
                return True, (
                    f"Startup founding violation: claims to have worked at "
                    f"'{company}' (founded {founding_year}) from {start_date.year}"
                )

    return False, None

# ─────────────────────────────────────────────────────────────────────────────
# CONSULTING FILTER (JD-DRIVEN: only applied if the JD signals it)
# ─────────────────────────────────────────────────────────────────────────────

def check_is_consulting_disqualified(cand):
    """
    Determines if a candidate should be excluded based on consulting-only career.

    This is NOT called by default — it is called only when the JD explicitly
    signals that consulting-only backgrounds are a disqualifier
    (i.e., criteria.disallow_consulting == True).

    Rules:
        - If the candidate's ENTIRE career is at IT consulting firms → disqualify
        - If the candidate is CURRENTLY at a consulting firm but has
          NO prior non-consulting (product company) experience → disqualify
        - Otherwise → allow (e.g., currently at consulting with past product exp.)

    Returns:
        (True, reason_str) if disqualified
        (False, None)      if allowed
    """
    history = cand.get("career_history", [])
    if not history:
        return False, None

    # Check if entire career is in consulting
    all_consulting = all(_is_consulting_company(job.get("company")) for job in history)
    if all_consulting:
        return True, "Entire career spent at IT consulting/services firms"

    # Identify current role(s)
    current_jobs = [job for job in history if job.get("is_current")]
    if not current_jobs:
        current_jobs = [history[0]]  # Fallback to most recent

    is_currently_consulting = any(_is_consulting_company(j.get("company")) for j in current_jobs)

    if is_currently_consulting:
        # Check if there is any past non-consulting (product) experience
        past_jobs = [job for job in history if job not in current_jobs]
        has_product_experience = any(
            not _is_consulting_company(job.get("company")) for job in past_jobs
        )
        if not has_product_experience:
            return True, "Currently at IT consulting firm with no prior product company experience"

    return False, None

# ─────────────────────────────────────────────────────────────────────────────
# STREAMING CANDIDATE PARSER
# ─────────────────────────────────────────────────────────────────────────────

def stream_candidates(file_path, criteria=None):
    """
    Streams candidates one-by-one from the JSONL file with early filtering.

    Args:
        file_path (str): Path to candidates.jsonl or sample_candidates.json
        criteria (DynamicCriteria | None): Parsed JD criteria object.
            If None, only honeypot filtering is applied.

    Yields:
        dict: Valid candidate record that passed all pre-filters.
    """
    # Detect if file is a JSON array (sample) or JSONL (full dataset)
    with open(file_path, "r", encoding="utf-8") as f:
        first_char = f.read(1)

    if first_char == "[":
        # JSON array format (e.g. sample_candidates.json)
        with open(file_path, "r", encoding="utf-8") as f:
            candidates = json.load(f)
        lines_iter = iter(candidates)
        is_jsonl = False
    else:
        lines_iter = None
        is_jsonl = True

    def process(cand):
        # Step 1: Hard filter — JD-agnostic honeypot check
        is_hp, _ = check_is_honeypot(cand)
        if is_hp:
            return None

        # Step 2: Conditional filter — consulting disqualification (JD-driven)
        if criteria is not None and criteria.disallow_consulting:
            is_cd, _ = check_is_consulting_disqualified(cand)
            if is_cd:
                return None

        return cand

    if is_jsonl:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                cand = json.loads(line)
                result = process(cand)
                if result is not None:
                    yield result
    else:
        for cand in candidates:
            result = process(cand)
            if result is not None:
                yield result
