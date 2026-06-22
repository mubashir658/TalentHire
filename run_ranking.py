"""
run_ranking.py
===============
CLI entry-point for the Redrob Hackathon candidate ranking pipeline.

Usage:
    python run_ranking.py \
        --candidates ./India_runs_data_and_ai_challenge/candidates.jsonl \
        --jd ./India_runs_data_and_ai_challenge/job_description.txt \
        --out ./outputs/team_xxx.csv

Constraints (from submission_spec.txt):
    - Must produce exactly 100 rows (ranks 1–100)
    - Each candidate_id appears exactly once
    - score is monotonically non-increasing with rank
    - Runs on CPU only, ≤16GB RAM, ≤5 minutes wall-clock
    - No external API calls
"""

import argparse
import csv
import os
import sys
import time

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.jd_parser        import parse_job_description
from src.data_processor   import stream_candidates
from src.feature_engineer import extract_features
from src.scorer           import calculate_composite_score
from src.reasoning_generator import generate_reasoning


def main():
    parser = argparse.ArgumentParser(
        description="Rank candidates against a job description and produce a submission CSV."
    )
    parser.add_argument(
        "--candidates", required=True,
        help="Path to candidates.jsonl (or sample_candidates.json)"
    )
    parser.add_argument(
        "--jd", required=True,
        help="Path to job_description.txt (plain text)"
    )
    parser.add_argument(
        "--out", default="outputs/submission.csv",
        help="Output CSV path (default: outputs/submission.csv)"
    )
    parser.add_argument(
        "--top-n", type=int, default=100,
        help="How many top candidates to include in the output (default: 100)"
    )
    args = parser.parse_args()

    # ── Validate inputs ────────────────────────────────────────────────────
    if not os.path.exists(args.candidates):
        print(f"[ERROR] Candidate file not found: {args.candidates}")
        sys.exit(1)
    if not os.path.exists(args.jd):
        print(f"[ERROR] JD file not found: {args.jd}")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.out) if os.path.dirname(args.out) else ".", exist_ok=True)

    start_time = time.time()
    print("=" * 60)
    print(" AI Recruiter Brain — Candidate Ranking Pipeline")
    print("=" * 60)
    print(f"  Candidates : {args.candidates}")
    print(f"  JD         : {args.jd}")
    print(f"  Output     : {args.out}")
    print(f"  Top-N      : {args.top_n}")
    print()

    # ── Step 1: Parse JD dynamically ──────────────────────────────────────
    print("[1/4] Parsing job description...")
    with open(args.jd, "r", encoding="utf-8") as f:
        jd_text = f.read()

    criteria = parse_job_description(jd_text)
    print(f"      YOE range      : {criteria.min_yoe:.0f}–{criteria.max_yoe:.0f} years")
    print(f"      Preferred locs : {sorted(criteria.preferred_locations)}")
    print(f"      Tier-1 locs    : {sorted(criteria.tier1_locations)}")
    print(f"      Core skills    : {len(criteria.core_skills)} detected")
    print(f"      Pref skills    : {len(criteria.preferred_skills)} detected")
    print(f"      Consulting gate: {'YES — active' if criteria.disallow_consulting else 'NO — inactive'}")
    print()

    # ── Step 2: Stream, filter, score ─────────────────────────────────────
    print("[2/4] Streaming and scoring candidates...")
    scored = []
    n_total = 0
    n_honeypot = 0
    n_consulting = 0

    for cand in stream_candidates(args.candidates, criteria):
        n_total += 1
        features              = extract_features(cand, criteria)
        score, components     = calculate_composite_score(cand, features)
        scored.append({
            "cand":       cand,
            "features":   features,
            "components": components,
            "score":      score,
        })

    # Approximate filter counts (stream_candidates already removes them)
    # We count total lines to estimate
    print(f"      Candidates read and scored: {len(scored)}")
    print()

    # ── Step 3: Sort and assign ranks ─────────────────────────────────────
    print("[3/4] Sorting and assigning ranks...")
    # Primary: score descending
    # Tie-break: candidate_id ascending (deterministic, as required by spec)
    scored.sort(key=lambda x: (-x["score"], x["cand"]["candidate_id"]))

    top_n = scored[: args.top_n]
    print(f"      Top-{args.top_n} candidates selected")
    print()

    # ── Step 4: Generate reasonings and write CSV ──────────────────────────
    print("[4/4] Generating reasoning and writing CSV...")
    rows = []
    for rank_idx, item in enumerate(top_n, start=1):
        reasoning = generate_reasoning(
            cand       = item["cand"],
            rank       = rank_idx,
            features   = item["features"],
            components = item["components"],
            criteria   = criteria,
        )
        rows.append({
            "candidate_id": item["cand"]["candidate_id"],
            "rank":         rank_idx,
            "score":        item["score"],
            "reasoning":    reasoning,
        })

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        writer.writerows(rows)

    elapsed = time.time() - start_time
    print(f"      Written {len(rows)} rows → {args.out}")
    print()
    print("=" * 60)
    print(f" Done in {elapsed:.1f}s")
    print(f" Top-3 candidates:")
    for row in rows[:3]:
        print(f"   #{row['rank']:>3}  {row['candidate_id']}  score={row['score']:.4f}")
        print(f"         {row['reasoning'][:100]}...")
    print("=" * 60)


if __name__ == "__main__":
    main()
