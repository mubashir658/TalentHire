# Redrob Hackathon - Intelligent Candidate Discovery Plan

**Combined Best Approach** (Friend's Plan + Research Insights + Hackathon Constraints)

**Goal**: Build a **General AI Brain for Modern Hiring** — a robust, extensible intelligent ranking system that can work for **any Job Description** and any company, while delivering excellent performance on the Redrob Senior AI Engineer role for the hackathon.  
**Core Philosophy**: **Hybrid Multi-Stage System** = Fast Filter + Semantic Embeddings + Structured Features + Behavioral Signals + Strong Honeypot/Trap Detection. The architecture is designed to be JD-agnostic.

**Key Principles**:
- Strictly respect compute limits (≤5 min CPU, no network in final ranking).
- Pre-compute heavy operations.
- Prioritize honeypot/trap avoidance.
- Generate specific, honest reasoning.
- Use local models only for final run.

## Phase 0: Setup & Exploration (Day 1)

- Read all provided files: `job_description.md`, `submission_spec.md`, `redrob_signals_doc.md`, `candidate_schema.json`, `all_anomalies.json`, `suspicious_candidates.json`.
- Design the system to accept **any JD** as input (modular architecture).
- Unzip and explore `candidates.jsonl.gz` using sample data.
- Set up GitHub repo with the recommended folder structure.
- Install dependencies and create virtual environment.
- Member 3: Create `run_ranking.py` skeleton with argument parsing.

## Phase 1: Data Processing & Feature Engineering (Days 2-4)

**Owner**: Member 1 (Data Engineer)

- Load full candidates efficiently.
- Parse all fields: profile, career_history, skills (with duration/proficiency), education, redrob_signals.
- Build **Honeypot & Trap Detector**:
  - Use `all_anomalies.json` + custom rules (YOE vs skill duration mismatches).
  - Flag impossible profiles, expert skills with 0 duration, consulting-only careers, low behavioral activity.
- Extract rich features:
  - Relevant YOE (AI/ML, Retrieval, Production).
  - Skill match score (exact + fuzzy to JD keywords like embeddings, vector DBs, evaluation frameworks).
  - Company type (product vs services/consulting).
  - Behavioral composite score (last_active, response_rate, open_to_work, saved_by_recruiters, etc.).
  - Location/relocation fit, notice period penalty.
- Output: Clean pandas DataFrame + saved feature cache.

## Phase 2: Semantic Understanding (Days 5-7)

**Owner**: Member 2 (ML Engineer)

- Load JD as text.
- Use local embedding model (`sentence-transformers/all-MiniLM-L6-v2` or BGE-small — fast on CPU).
- Pre-compute and save:
  - JD embedding.
  - Candidate profile + summary + skills + career embeddings.
- Compute cosine similarity scores.
- Optional: BM25 keyword filter for initial shortlist (top 5K-10K).

## Phase 3: Scoring Engine (Days 8-10)

**Owner**: Member 2 + Member 1

- Combine multiple signals into final score:
  - Semantic similarity (40%)
  - Structured skill + YOE match (25%)
  - Behavioral signals bonus (15%)
  - Anomaly / Honeypot penalty (strong negative)
  - Other JD-specific factors (company type, Python strength, evaluation exp)
- Use **Weighted Sum** as baseline + **XGBoost** (or LightGBM) for better ranking.
- Train XGBoost on synthetic labels or use as feature combiner.
- Pre-compute everything possible.

## Phase 4: Top-100 Ranking & Reasoning (Days 11-13)

**Owner**: Member 3

- Take top 300-500 candidates from Phase 3.
- Apply final re-ranking if needed.
- Generate **high-quality reasoning** (1-2 sentences per candidate):
  - Reference specific facts from profile.
  - Connect to JD requirements.
  - Mention concerns honestly (e.g., notice period, gaps).
  - Avoid hallucination — use templates + extracted data.
- Ensure scores are non-increasing, ranks 1-100 unique, deterministic tie-breaking.
- Generate `team_xxx.csv`.

## Phase 5: Validation & Testing (Days 14-15)

- Run `validate_submission.py`.
- Test full pipeline under constraints (time + memory).
- Verify honeypot rate in top 100 is low (<5% ideally).
- Member 3: Prepare `submission_metadata.yaml`.

## Phase 6: Demo & Documentation (Days 16-18)

**Owner**: Member 3

- Build **Streamlit app** (`demo/app.py`):
  - Upload small candidate sample or use pre-loaded.
  - Show ranking + reasoning + honeypot flags.
- Write comprehensive `README.md` with:
  - Setup instructions.
  - Exact reproduction command.
  - Architecture explanation.
  - Methodology summary.

## Phase 7: Final Submission (Day 19)

- Final valid CSV.
- GitHub repo (public or accessible).
- Sandbox link (Streamlit/HF Space/Colab).
- Submit via portal.

---

**Tech Stack (All Local & Efficient)**

- Core: Python 3.10+, pandas, numpy, scikit-learn
- Embeddings: sentence-transformers
- Ranking: XGBoost / LightGBM
- Demo: Streamlit
- Validation: Provided script

**Risk Mitigation**
- No hosted LLM calls in final `run_ranking.py`.
- Pre-compute embeddings and features.
- Strong emphasis on explainable, rule-based components.

**Success Metrics**
- Low honeypot rate in top 100.
- High-quality, varied reasoning.
- Full pipeline < 5 minutes on CPU.
- Strong Stage 4 manual review performance.

This plan creates a **general-purpose AI recruiting brain** that combines the best of research (semantic embeddings, hybrid scoring) with hackathon-specific requirements (compute limits, honeypot detection, behavioral signals). The system is modular and can be extended to any JD/company.

**Next Action**: Start with Phase 0 and Phase 1. Let me know when you're ready for code templates.
Upgrade to SuperGrok
