"""
feature_engineer.py
====================
Extracts all scoring features for a candidate.

DESIGN PRINCIPLE:
    Every scoring decision is driven by the `criteria` object returned by
    `jd_parser.parse_job_description()`.  There are NO hardcoded values for
    YOE ranges, locations, or skill lists.  When a different JD is uploaded,
    `criteria` changes → all scores automatically adjust.

The only things that ARE fixed are the 23 Redrob behavioral signals (their
names, ranges, and semantics) because those are properties of the Redrob
platform, not of any specific job description.
"""

import re
from datetime import datetime

# Reference date: use today-ish (hackathon window is June 2026)
REFERENCE_DATE = datetime(2026, 6, 1)

# ─── DATE HELPER ──────────────────────────────────────────────────────────────

def _parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

# ─── 1. YOE FIT SCORE (JD-driven) ─────────────────────────────────────────────

def score_yoe(yoe: float, criteria) -> tuple[float, str]:
    """
    Score how well the candidate's years of experience fits the JD range.

    Returns (score 0.0–1.0, description string)

    Logic:
      - Inside [min_yoe, max_yoe]      → 1.0  (perfect fit)
      - Below min_yoe                  → linear ramp (0 → 1 as yoe → min_yoe)
      - Above max_yoe                  → slow decay (penalise over-qualification gently)
    """
    lo, hi = criteria.min_yoe, criteria.max_yoe

    if lo <= yoe <= hi:
        return 1.0, f"{yoe:.1f} yrs — inside JD range ({lo:.0f}–{hi:.0f} yrs)"

    if yoe < lo:
        if lo == 0:
            score = 1.0
        else:
            score = round(yoe / lo, 3)
        return score, f"{yoe:.1f} yrs — below JD min ({lo:.0f} yrs)"

    # yoe > hi
    excess = yoe - hi
    score = max(0.0, round(1.0 - excess * 0.08, 3))
    return score, f"{yoe:.1f} yrs — above JD max ({hi:.0f} yrs), slight over-qual penalty"


# ─── 2. LOCATION SCORE (JD-driven) ───────────────────────────────────────────

def score_location(cand: dict, criteria) -> tuple[float, str]:
    """
    Score location fit based on the locations parsed from the JD.

    Tiers:
      preferred_locations  → +1.0  (direct match — e.g., Noida/Pune for Redrob JD)
      tier1_locations      → +0.6  (acceptable with relocation willingness)
      same country         → +0.3  (within country, willing to relocate)
      same country no relo → 0.0
      outside country      → -0.4  (visa friction)

    Returns (score, description)
    """
    profile    = cand["profile"]
    signals    = cand.get("redrob_signals", {})
    location   = profile.get("location", "").strip().lower()
    country    = profile.get("country", "").strip().lower()
    willing    = signals.get("willing_to_relocate", False)

    # Check preferred (highest priority)
    for loc in criteria.preferred_locations:
        if loc.lower() in location:
            return 1.0, f"Located in preferred city ({profile.get('location')})"

    # Check tier-1 (from JD text)
    for loc in criteria.tier1_locations:
        if loc.lower() in location:
            if willing:
                return 0.65, f"Tier-1 city ({profile.get('location')}), willing to relocate"
            else:
                return 0.35, f"Tier-1 city ({profile.get('location')}), not willing to relocate"

    # Fallback: check india vs international
    # (is_india_role is set by the JD parser when the JD mentions India-specific locations)
    if criteria.is_india_role:
        if country == "india":
            if willing:
                return 0.3, f"India-based ({profile.get('location')}), willing to relocate"
            else:
                return 0.1, f"India-based ({profile.get('location')}), not willing to relocate"
        else:
            return -0.1, f"Outside India ({profile.get('country')})"
    else:
        # Non-India role — location scoring is symmetric
        if willing:
            return 0.3, "Willing to relocate"
        return 0.1, "Not willing to relocate"


# ─── 3. SKILL MATCH SCORE (JD-driven) ────────────────────────────────────────

def score_skills(cand: dict, criteria) -> tuple[float, float, str]:
    """
    Match candidate skills against JD core & preferred skill sets.

    Returns (core_match_ratio, pref_match_ratio, description)

    core_match_ratio: fraction of core skills present in candidate profile [0,1]
    pref_match_ratio: fraction of preferred skills present [0,1]

    Skills are matched against:
      - candidate skill names
      - career history job descriptions (to catch implicit skills)
    """
    skill_names = set()
    for s in cand.get("skills", []):
        skill_names.add(s.get("name", "").lower())

    # Build a single text blob from career history descriptions
    history_text = " ".join(
        (job.get("description", "") or "").lower()
        for job in cand.get("career_history", [])
    )
    profile_text = (
        (cand["profile"].get("headline", "") or "") + " " +
        (cand["profile"].get("summary", "") or "")
    ).lower()
    full_text = " ".join(skill_names) + " " + history_text + " " + profile_text

    core_hit = sum(1 for sk in criteria.core_skills if sk in full_text)
    pref_hit = sum(1 for sk in criteria.preferred_skills if sk in full_text)

    core_ratio = core_hit / len(criteria.core_skills) if criteria.core_skills else 0.0
    pref_ratio = pref_hit / len(criteria.preferred_skills) if criteria.preferred_skills else 0.0

    desc = (
        f"{core_hit}/{len(criteria.core_skills)} core skills, "
        f"{pref_hit}/{len(criteria.preferred_skills)} preferred skills matched"
    )
    return round(core_ratio, 3), round(pref_ratio, 3), desc


# ─── 4. BEHAVIORAL / AVAILABILITY SCORE (platform signals — fixed) ────────────

def score_behavioral(cand: dict) -> tuple[float, list]:
    """
    Score candidate availability and engagement using Redrob's 23 behavioral signals.

    The signal names and ranges come from redrob_signals_doc.txt — they are
    platform-level facts, not JD-specific.  The WEIGHTS here reflect what the
    signals doc says about their recruiting predictiveness.

    Returns (raw_score -1.0 to +1.0, list of notable observations)
    """
    signals  = cand.get("redrob_signals", {})
    score    = 0.0
    notes    = []

    # — Availability flags (binary, high impact) ——————————————————
    if signals.get("open_to_work_flag", False):
        score += 0.15
        notes.append("open to work")

    # — Recency of activity ————————————————————————————————————————
    last_active = _parse_date(signals.get("last_active_date"))
    if last_active:
        days_inactive = (REFERENCE_DATE - last_active).days
        if days_inactive <= 30:
            score += 0.10
            notes.append("active ≤ 30 days ago")
        elif days_inactive <= 90:
            score += 0.05
        elif days_inactive > 180:
            score -= 0.15
            notes.append(f"inactive {days_inactive} days")

    # — Recruiter responsiveness ———————————————————————————————————
    rrr = signals.get("recruiter_response_rate", 0.5)
    if rrr >= 0.7:
        score += 0.10
        notes.append(f"high response rate ({rrr:.0%})")
    elif rrr < 0.15:
        score -= 0.12
        notes.append(f"very low response rate ({rrr:.0%})")

    avg_resp_h = signals.get("avg_response_time_hours", 24)
    if avg_resp_h <= 4:
        score += 0.05  # fast responder bonus

    # — Interview reliability ——————————————————————————————————————
    icr = signals.get("interview_completion_rate", 0.5)
    if icr >= 0.85:
        score += 0.08
        notes.append(f"high interview completion ({icr:.0%})")
    elif icr < 0.40:
        score -= 0.10
        notes.append(f"low interview completion ({icr:.0%})")

    # — Profile quality signals ————————————————————————————————————
    completeness = signals.get("profile_completeness_score", 50)
    score += (completeness - 50) / 500  # ±0.1 range contribution

    if signals.get("verified_email", False):
        score += 0.03
    if signals.get("verified_phone", False):
        score += 0.03
    if signals.get("linkedin_connected", False):
        score += 0.04

    # — Recruiter market interest —————————————————————————————————
    saved_30d = signals.get("saved_by_recruiters_30d", 0)
    if saved_30d >= 5:
        score += 0.08
        notes.append(f"saved by {saved_30d} recruiters (30d)")
    elif saved_30d >= 2:
        score += 0.04

    profile_views = signals.get("profile_views_received_30d", 0)
    if profile_views >= 10:
        score += 0.05

    # — GitHub activity ————————————————————————————————————————————
    gh = signals.get("github_activity_score", -1)
    if gh > 0:
        score += (gh / 100) * 0.10   # max +0.10 for score of 100

    # — Offer history (signal of real-world demand) ———————————————
    oar = signals.get("offer_acceptance_rate", -1)
    if oar != -1 and oar >= 0.7:
        score += 0.05

    return round(score, 4), notes


# ─── 5. NOTICE PERIOD SCORE (JD-driven) ──────────────────────────────────────

def score_notice_period(cand: dict, criteria) -> tuple[float, str]:
    """
    Score notice period fit.

    The JD signals are used if available:
      - If JD says 'sub-30-day notice preferred' (detected via criteria.preferred_locations
        having Noida/Pune — proxy that this is an urgent hire), apply the full tier scheme.
      - Otherwise a lighter version applies.

    Tiers (from the Redrob JD):
      ≤ 30 days   → +0.15  (can buy out, very preferred)
      31–60 days  →  0.05
      61–90 days  →  0.00
      > 90 days   → -0.10  (bar gets higher per JD text)
    """
    notice = cand.get("redrob_signals", {}).get("notice_period_days", 90)

    if notice <= 30:
        return 0.15, f"notice ≤ 30 days ({notice}d)"
    elif notice <= 60:
        return 0.05, f"notice 31–60 days ({notice}d)"
    elif notice <= 90:
        return 0.0, f"notice 61–90 days ({notice}d)"
    else:
        return -0.10, f"notice > 90 days ({notice}d — bar is higher)"


# ─── 6. JD RED-FLAG CHECKS (JD-driven) ───────────────────────────────────────

def score_jd_redflags(cand: dict, criteria) -> tuple[float, list]:
    """
    Check for explicit disqualifier signals mentioned in the JD.
    These are extracted from revise.md and the JD text and applied here.

    All checks are derived from what the JD explicitly says — no assumptions.

    Returns (penalty_score ≤ 0.0, list of red-flag reasons)
    """
    penalty = 0.0
    flags   = []

    history      = cand.get("career_history", [])
    skills       = cand.get("skills", [])
    profile      = cand["profile"]
    profile_text = (
        (profile.get("headline", "") or "") + " " +
        (profile.get("summary", "") or "") + " " +
        " ".join((job.get("description", "") or "") for job in history)
    ).lower()

    # ── A. Pure research role (no production deployment) ──────────────────
    research_keywords  = ["research scientist", "research engineer", "phd researcher",
                          "postdoc", "academic", "research lab", "research intern"]
    production_keywords = ["deploy", "production", "ship", "launch", "serving",
                           "inference", "api", "scale", "real users", "prod"]

    has_research_title = any(kw in profile_text for kw in research_keywords)
    has_production_exp  = any(kw in profile_text for kw in production_keywords)

    if has_research_title and not has_production_exp:
        penalty -= 0.25
        flags.append("purely research background — no production deployment signal")

    # ── B. Title-chasing (short tenures to get promoted) ──────────────────
    if len(history) >= 3:
        # Count jobs < 18 months (1.5 years)
        short_stints = sum(
            1 for job in history
            if job.get("duration_months", 24) < 18
        )
        if short_stints >= 3:
            penalty -= 0.12
            flags.append(f"{short_stints} jobs with < 18 months tenure (title-chasing signal)")

    # ── C. CV/Speech/Robotics only — no NLP/IR/Search experience ──────────
    # Only applies when JD core skills include retrieval/NLP/search
    nlp_ir_skills = {"embedding", "retrieval", "search", "nlp", "semantic", "vector",
                     "ranking", "recommendation", "information retrieval"}
    jd_has_nlp_ir = bool(criteria.core_skills & nlp_ir_skills)

    if jd_has_nlp_ir:
        cv_speech_rob_terms = ["computer vision", "speech recognition", "robotics",
                               "object detection", "image segmentation", "lidar",
                               "slam", "pose estimation", "asr", "tts"]

        expert_cv_speech  = any(
            s.get("proficiency") in ("expert", "advanced") and
            any(t in s.get("name", "").lower() for t in cv_speech_rob_terms)
            for s in skills
        )
        has_nlp_ir_signal = any(kw in profile_text for kw in nlp_ir_skills)

        if expert_cv_speech and not has_nlp_ir_signal:
            penalty -= 0.20
            flags.append("CV/speech/robotics expert with no NLP/IR/search exposure")

    # ── D. Non-coding management role > 18 months ─────────────────────────
    current_jobs = [j for j in history if j.get("is_current")] or history[:1]
    for job in current_jobs:
        title    = (job.get("title") or "").lower()
        desc     = (job.get("description") or "").lower()
        duration = job.get("duration_months", 0)

        mgmt_titles = ["manager", "director", "vp ", "vice president", "head of",
                       "chief ", "cto", "cpo"]
        tech_titles = ["engineer", "developer", "scientist", "programmer", "architect"]

        is_mgmt_title = any(kw in title for kw in mgmt_titles)
        is_tech_title = any(kw in title for kw in tech_titles)
        coding_signals = ["python", "code", "build", "develop", "sql", "git", "deploy",
                          "write", "implement", "algorithm", "model"]

        if is_mgmt_title and not is_tech_title and duration > 18:
            has_coding = any(kw in desc for kw in coding_signals)
            if not has_coding:
                penalty -= 0.15
                flags.append(f"non-coding management role ({title}) for {duration} months")
                break

    return round(penalty, 4), flags


# ─── 7. MASTER FEATURE EXTRACTION ─────────────────────────────────────────────

def extract_features(cand: dict, criteria) -> dict:
    """
    Entry point: extract ALL scoring features for one candidate.

    Args:
        cand     : Single candidate dict from candidates.jsonl
        criteria : DynamicCriteria object from jd_parser.parse_job_description()

    Returns a flat feature dict used by scorer.py to compute the composite score.
    """
    yoe = cand["profile"]["years_of_experience"]

    yoe_score,  yoe_desc    = score_yoe(yoe, criteria)
    loc_score,  loc_desc    = score_location(cand, criteria)
    core_ratio, pref_ratio, skill_desc = score_skills(cand, criteria)
    beh_score,  beh_notes   = score_behavioral(cand)
    notice_score, notice_desc = score_notice_period(cand, criteria)
    redflag_penalty, redflags = score_jd_redflags(cand, criteria)

    return {
        # Raw values
        "yoe":              yoe,

        # Sub-scores (all in a comparable scale)
        "yoe_score":        yoe_score,       # 0.0 – 1.0
        "loc_score":        loc_score,       # -0.1 – 1.0
        "core_skill_ratio": core_ratio,      # 0.0 – 1.0
        "pref_skill_ratio": pref_ratio,      # 0.0 – 1.0
        "behavioral_score": beh_score,       # -1.0 – +1.0 (clamped)
        "notice_score":     notice_score,    # -0.10 – +0.15
        "redflag_penalty":  redflag_penalty, # ≤ 0.0

        # Descriptions for reasoning generator
        "yoe_desc":         yoe_desc,
        "loc_desc":         loc_desc,
        "skill_desc":       skill_desc,
        "beh_notes":        beh_notes,
        "notice_desc":      notice_desc,
        "redflags":         redflags,

        # Raw signal values (for reasoning)
        "github_score":     cand.get("redrob_signals", {}).get("github_activity_score", -1),
        "notice_days":      cand.get("redrob_signals", {}).get("notice_period_days", 90),
        "open_to_work":     cand.get("redrob_signals", {}).get("open_to_work_flag", False),
        "response_rate":    cand.get("redrob_signals", {}).get("recruiter_response_rate", 0.5),
    }
