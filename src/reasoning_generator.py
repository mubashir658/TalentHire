"""
reasoning_generator.py
========================
Generates a 1–2 sentence, fact-grounded reasoning string for each ranked
candidate.

RULES (from submission_spec.txt Stage 4 evaluation checks):
────────────────────────────────────────────────────────────
  ✅ Specific facts    — reference actual YOE, title, matched skills, signals
  ✅ JD connection     — mention specific JD requirements, not generic praise
  ✅ Honest concerns   — acknowledge gaps / red flags where they exist
  ✅ No hallucination  — every claim must be in the candidate's profile
  ✅ Variation         — no two candidates get the same string
  ✅ Rank consistency  — tone matches rank (glowing at #1, cautious at #95)

  ❌ NO random.choice templating
  ❌ NO generic praise without evidence
  ❌ NO skills mentioned that don't appear in the candidate's profile

APPROACH:
    Build the reasoning from discrete, observed facts then compose a sentence.
    Tone is determined by the composite score bucket, not randomly.
"""

from datetime import datetime

REFERENCE_DATE = datetime(2026, 6, 1)


def _days_since(date_str: str) -> int | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            d = datetime.strptime(date_str, fmt)
            return (REFERENCE_DATE - d).days
        except ValueError:
            continue
    return None


def generate_reasoning(cand: dict, rank: int, features: dict,
                       components: dict, criteria) -> str:
    """
    Generate a non-templated, fact-based 1–2 sentence reasoning.

    Args:
        cand       : Full candidate dict
        rank       : Assigned rank (1-based)
        features   : Feature dict from feature_engineer.extract_features()
        components : Score component dict from scorer.calculate_composite_score()
        criteria   : DynamicCriteria from jd_parser (for JD-specific references)

    Returns:
        str : 1–2 sentence reasoning, max ~280 chars
    """
    profile  = cand["profile"]
    signals  = cand.get("redrob_signals", {})

    yoe      = profile.get("years_of_experience", 0)
    title    = profile.get("current_title", "engineer") or "engineer"
    company  = profile.get("current_company", "") or ""
    location = profile.get("location", "") or ""
    country  = profile.get("country", "") or ""

    notice   = signals.get("notice_period_days", 90)
    rrr      = signals.get("recruiter_response_rate", 0.5)
    active   = signals.get("last_active_date", "")
    open_wk  = signals.get("open_to_work_flag", False)
    gh_score = signals.get("github_activity_score", -1)

    # ── Skill evidence: what core/preferred skills were actually found ─────
    # Re-derive from the candidate profile text so we mention REAL skills
    skill_names = {s.get("name", "").lower() for s in cand.get("skills", [])}
    history_text = " ".join(
        (j.get("description", "") or "").lower()
        for j in cand.get("career_history", [])
    )
    profile_text = (
        (profile.get("headline", "") or "") + " " +
        (profile.get("summary", "") or "")
    ).lower()
    full_text = " ".join(skill_names) + " " + history_text + " " + profile_text

    matched_core = [sk for sk in criteria.core_skills   if sk in full_text]
    matched_pref = [sk for sk in criteria.preferred_skills if sk in full_text]

    # ── Build fact fragments ───────────────────────────────────────────────

    # YOE fact
    lo, hi = criteria.min_yoe, criteria.max_yoe
    if lo <= yoe <= hi:
        yoe_fact = f"{yoe:.0f} yrs exp (within JD range {lo:.0f}–{hi:.0f})"
    elif yoe < lo:
        yoe_fact = f"{yoe:.0f} yrs exp (below JD min of {lo:.0f})"
    else:
        yoe_fact = f"{yoe:.0f} yrs exp (above JD max of {hi:.0f})"

    # Title/company fact
    if company:
        role_fact = f"{title} at {company}"
    else:
        role_fact = title

    # Skill fact
    if matched_core:
        skill_fact = f"matches {len(matched_core)}/{len(criteria.core_skills)} core JD skills ({', '.join(matched_core[:3])}{'...' if len(matched_core) > 3 else ''})"
    elif matched_pref:
        skill_fact = f"no core skills matched but shows {', '.join(matched_pref[:2])} (preferred)"
    else:
        skill_fact = "no direct skill overlap with JD requirements"

    # Location fact
    loc_score = features["loc_score"]
    if loc_score >= 0.9:
        loc_fact = f"based in {location} (preferred JD location)"
    elif loc_score >= 0.5:
        loc_fact = f"in {location}, willing to relocate"
    elif country.lower() != "india" and criteria.is_india_role:
        loc_fact = f"outside India ({country})"
    else:
        loc_fact = f"in {location}, not willing to relocate"

    # Availability fact
    days_inactive = _days_since(active)
    if open_wk:
        avail_fact = "actively open to work"
    elif days_inactive and days_inactive <= 30:
        avail_fact = f"active recently ({days_inactive}d ago)"
    elif days_inactive and days_inactive > 180:
        avail_fact = f"inactive {days_inactive} days"
    else:
        avail_fact = f"response rate {rrr:.0%}"

    # Notice fact
    if notice <= 30:
        notice_fact = f"notice ≤30d"
    elif notice > 90:
        notice_fact = f"long notice ({notice}d)"
    else:
        notice_fact = f"notice {notice}d"

    # Red flags
    redflags = features.get("redflags", [])
    redflag_fact = redflags[0] if redflags else ""

    # GitHub fact (only mention if meaningful)
    if gh_score >= 60:
        gh_fact = f"strong GitHub activity ({gh_score}/100)"
    elif gh_score > 0:
        gh_fact = ""
    else:
        gh_fact = ""

    # ── Compose reasoning based on rank tier ──────────────────────────────

    if rank <= 10:
        # Top-10: lead with skill+role strength, close with availability
        sentence1 = (
            f"{role_fact}, {yoe_fact}; "
            f"{skill_fact}."
        )
        concerns = []
        if redflag_fact:
            concerns.append(redflag_fact)
        if notice > 90:
            concerns.append(notice_fact)
        if days_inactive and days_inactive > 90:
            concerns.append(avail_fact)

        if concerns:
            sentence2 = (
                f"Concern: {concerns[0]}; "
                f"overall top fit given {loc_fact} and {avail_fact}."
            )
        else:
            extras = [loc_fact, avail_fact]
            if gh_fact:
                extras.append(gh_fact)
            sentence2 = f"Strong fit: {'; '.join(extras)}."

    elif rank <= 30:
        # Ranks 11–30: solid fit, acknowledge one trade-off
        sentence1 = (
            f"{role_fact} with {yoe_fact}; "
            f"{skill_fact}."
        )
        trade_off = redflag_fact or (notice_fact if notice > 60 else "") or avail_fact
        sentence2 = (
            f"{loc_fact.capitalize()}, {notice_fact}; "
            f"{'concern: ' + trade_off + '.' if trade_off and trade_off != avail_fact else avail_fact + '.'}"
        )

    elif rank <= 60:
        # Ranks 31–60: moderate fit, honest about gaps
        sentence1 = (
            f"{yoe_fact} as {title}; "
            f"{skill_fact}."
        )
        gap_note = redflag_fact if redflag_fact else f"partial skill overlap with JD"
        sentence2 = (
            f"Gap: {gap_note}. "
            f"{loc_fact.capitalize()}, {notice_fact}, {avail_fact}."
        )

    else:
        # Ranks 61–100: adjacent or weak fit, be honest
        sentence1 = (
            f"{yoe_fact} as {title}; "
            f"{skill_fact}."
        )
        why_low = redflag_fact if redflag_fact else "limited direct JD skill match"
        sentence2 = (
            f"Ranked lower due to {why_low}; "
            f"{loc_fact}, {notice_fact}."
        )

    # ── Clean and enforce length ───────────────────────────────────────────
    reasoning = f"{sentence1} {sentence2}"
    # Collapse multiple spaces
    reasoning = " ".join(reasoning.split())
    # Ensure max ~300 chars (the spec says "1-2 sentences")
    if len(reasoning) > 300:
        reasoning = reasoning[:297] + "..."

    return reasoning
