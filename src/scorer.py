"""
scorer.py
==========
Computes a single normalised composite score for a candidate given
the features extracted by feature_engineer.py.

SCORING PHILOSOPHY (grounded in submission_spec.txt and revise.md):
────────────────────────────────────────────────────────────────────
  Final score = weighted combination of 5 signal groups, then clamped [0, 1].

  The weights mirror the NDCG@10 (0.50) dominance in the evaluation metric:
  we care MOST about correctly identifying the top candidates, which means
  skill relevance and YOE fit must dominate; behavioral signals act as a
  tiebreaker / availability multiplier.

  Group                   Weight    Rationale
  ──────────────────────  ──────    ──────────────────────────────────────
  Core skill match        0.40      Primary hiring signal; JD-driven
  YOE fit                 0.20      Soft range; JD-driven
  Preferred skill match   0.10      Nice-to-have; JD-driven
  Behavioral / signals    0.20      Availability & engagement multiplier
  Location                0.10      Logistical fit; JD-driven

  Red-flag penalties from feature_engineer are applied AFTER weighting as
  absolute subtractions so they can never be hidden inside a low-weight group.

SCORE RANGE:
  Raw scores are in [0, 1] (approximately) before penalty.
  After penalty, score is clamped to [0.001, 1.0] so every candidate
  gets a positive score (avoids log(0) issues in NDCG computation).

  The final score is monotonically non-increasing with rank, satisfying
  the submission spec requirement.
"""


def calculate_composite_score(cand: dict, features: dict) -> tuple[float, dict]:
    """
    Compute the composite ranking score for one candidate.

    Args:
        cand     : Candidate dict (used only for tie-break context if needed)
        features : Feature dict returned by feature_engineer.extract_features()

    Returns:
        (score: float in [0.001, 1.0], components: dict)
    """

    # ── Group weights ──────────────────────────────────────────────────────
    W_CORE_SKILL   = 0.45
    W_YOE          = 0.15
    W_PREF_SKILL   = 0.10
    W_LOCATION     = 0.10
    # Behavioral is a MULTIPLIER (0.7 – 1.3 range), not additive weight.
    # This is grounded in redrob_signals_doc.txt:
    # "These signals are often more predictive... use them as a multiplier
    #  or modifier on top of skill-match scoring."

    # ── Sub-scores (all in [0, 1]) ─────────────────────────────────────────
    core_ratio     = features["core_skill_ratio"]
    pref_ratio     = features["pref_skill_ratio"]

    # If ZERO core skills match AND ZERO preferred skills, candidate has no
    # relevance — apply a hard ceiling so they cannot rank above candidates
    # with any skill overlap regardless of other signals.
    has_any_skill_overlap = (core_ratio > 0) or (pref_ratio > 0)

    core_component = core_ratio                    * W_CORE_SKILL
    yoe_component  = features["yoe_score"]         * W_YOE
    pref_component = pref_ratio                    * W_PREF_SKILL

    loc_raw       = features["loc_score"]           # in [-0.1, 1.0]
    loc_component = max(0.0, loc_raw)              * W_LOCATION
    loc_penalty   = min(0.0, loc_raw)              * W_LOCATION

    # ── Base relevance score (sum of JD-signal groups) ─────────────────────
    base_relevance = (
        core_component +
        yoe_component  +
        pref_component +
        loc_component
    )

    # ── Behavioral multiplier ──────────────────────────────────────────────
    # behavioral_score ∈ [-1, +1]
    # Map to multiplier range [0.70, 1.30]:
    #   -1.0  → 0.70  (inactive/unresponsive → penalise 30%)
    #    0.0  → 1.00  (neutral)
    #   +1.0  → 1.30  (highly engaged → boost 30%)
    beh_raw   = features["behavioral_score"]       # [-1, +1]
    beh_multi = 1.0 + (beh_raw * 0.30)            # [0.70, 1.30]
    beh_multi = max(0.70, min(1.30, beh_multi))

    relevance_after_beh = base_relevance * beh_multi

    # Hard ceiling for zero-skill candidates: cap at 0.25 so they always
    # rank below any candidate with at least one matched skill.
    if not has_any_skill_overlap:
        relevance_after_beh = min(relevance_after_beh, 0.25)

    # ── Additive modifiers ─────────────────────────────────────────────────
    notice_contribution  = features["notice_score"]     # [-0.10, +0.15]
    redflag_contribution = features["redflag_penalty"]  # ≤ 0.0

    # ── Final composition ──────────────────────────────────────────────────
    raw_score = (
        relevance_after_beh
        + loc_penalty
        + notice_contribution
        + redflag_contribution
    )

    # ── Clamp to [0.001, 1.0] ─────────────────────────────────────────────
    final_score = round(max(0.001, min(1.0, raw_score)), 6)

    components = {
        "core_component":       round(core_component,        4),
        "yoe_component":        round(yoe_component,         4),
        "pref_component":       round(pref_component,        4),
        "loc_component":        round(loc_component + loc_penalty, 4),
        "beh_multiplier":       round(beh_multi,             4),
        "relevance_after_beh":  round(relevance_after_beh,   4),
        "notice_contribution":  round(notice_contribution,   4),
        "redflag_contribution": round(redflag_contribution,  4),
        "raw_score":            round(raw_score,             6),
    }

    return final_score, components
