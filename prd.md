# Product Requirements Document (PRD) - Redrob AI Recruiter

## 1. Product Overview

**Vision**: A modular, general-purpose **AI Brain for Talent Acquisition** that any company can use to transform massive candidate pools into high-quality shortlists.
**Product Name**: **General AI Brain for Intelligent Candidate Discovery**  
**Version**: 1.0 (Hackathon Submission)  
**Objective**: Build a general-purpose, extensible **AI-powered recruiting brain** that can intelligently understand any Job Description and rank candidates from large pools (100K+). For the hackathon, it is applied to the Redrob "Senior AI Engineer — Founding Team" role.

This system is designed as a **general AI recruiter** capable of working across different companies and roles. It deeply understands nuanced JDs, goes beyond keywords using semantic + structured signals, integrates behavioral data, and avoids traps.

## 2. Objectives & Success Criteria
### Business Goals
- Deliver highly relevant top-100 shortlist that maximizes hiring success probability
- Demonstrate understanding of nuanced JD requirements
- Survive all 5 stages of hackathon evaluation

### Technical Goals
- Process 100K candidates in ≤5 minutes (CPU only, no network)
- Produce explainable, honest reasoning
- Zero format violations
- Honeypot rate in top-100 < 10%

### Metrics
- **Ranking Quality**: High NDCG@10, NDCG@50, MAP
- **Reasoning Quality**: Specific, JD-aligned, non-hallucinated, varied
- **System Quality**: Reproducible, fast, clean code

## 3. Inputs
- `candidates.jsonl.gz` — 100,000 candidate profiles (JSON Lines)
- `job_description.txt` — Single target JD
- Pre-computed artifacts (embeddings, processed features) — allowed

## 4. Outputs
- `team_xxx.csv` — Exactly 100 rows with columns:  
  `candidate_id, rank, score, reasoning`
- Streamlit/Gradio demo for sandbox
- Full GitHub repository with reproduction instructions

## 5. Key Features & Requirements

### 5.1 Core Capabilities
- **Honeypot & Trap Detection** (Must-have)
  - YOE vs skill duration mismatch
  - Expert skills with zero experience
  - Title vs summary vs career inconsistency
  - Pure consulting / services background flags

- **Semantic Matching**
  - JD-Candidate embedding similarity (sentence-transformers)
  - Skill semantic understanding

- **Structured Scoring**
  - Relevant Experience (AI/ML, Retrieval, Ranking, Vector DBs)
  - Behavioral Signals (last_active, response_rate, open_to_work, saved_by_recruiters, etc.)
  - Production vs Research/Consulting fit
  - Location & Notice Period fit

- **Final Ranking**
  - Hybrid score (semantic + structured + signals - penalties)
  - Deterministic tie-breaking
  - Monotonically non-increasing scores

### 5.2 Reasoning Generation
- 1-2 sentences per candidate
- Specific facts from profile
- Honest concerns when present
- Clear connection to JD requirements
- Varied across candidates

## 6. Non-Functional Requirements
- **Performance**: Ranking step ≤5 min on CPU
- **Reproducibility**: Single command to generate CSV
- **Dependencies**: Local only (no API calls in final run)
- **Output**: Strictly CSV format as per submission_spec
- **Explainability**: Clear feature contributions where possible

## 7. Architecture Overview

The architecture is intentionally **JD-agnostic** and modular so it can be used for any job role/company.
1. Data Loader + Processor
2. Feature Engineer + Trap Detector
3. Embedding Generator (pre-computed)
4. Scorer (Weighted + XGBoost)
5. Ranker + Reasoning Generator
6. CSV Exporter + Validator

## 8. Assumptions & Constraints
- No access to ground truth labels
- Must work with provided synthetic dataset
- All code must be self-contained for Docker/sandbox reproduction
- AI tools allowed for development, not for final inference

## 9. Out of Scope
- PDF resume parsing (data is already structured)
- Hosted LLM calls in ranking script
- Training large models from scratch

## 10. Risks
- Overfitting to sample data
- Time limit violations
- Poor reasoning quality → Stage 4 failure
- High honeypot rate → Stage 3 disqualification

**Approval**: This PRD defines the complete scope for a competitive submission.
Upgrade to SuperGrok
