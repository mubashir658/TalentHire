# Revision Guide: Intelligent Candidate Discovery & Ranking (Track 01)

This document contains everything learned, analyzed, and planned for the **Redrob AI Hackathon (The Data & AI Challenge)**. Copy this file into your active development folder to continue work without starting from scratch.

---

## 1. Problem Statement in Simple Words
The mission is to build an **offline candidate discovery and ranking system** that acts as an "AI Recruiter" for a **"Senior AI Engineer — Founding Team"** role:
* **Input**: A JSONL file containing **100,000 candidate profiles** (`candidates.jsonl`).
* **Output**: A CSV file containing exactly the **top 100** best-fit candidates, ranked 1 to 100, with unique ranks, scores (non-increasing with rank), and a custom, non-templated reasoning for each candidate.
* **Format**:
  ```csv
  candidate_id,rank,score,reasoning
  CAND_0042871,1,0.987,"Senior AI Engineer with 7 years building RAG systems..."
  ```
* **Strict Performance Limits**: The code must run **entirely offline** (no external API calls/network), on **CPU only** (no GPU), using **≤16GB RAM**, and complete the execution in **under 5 minutes** for the 100k pool. (A pure Python heuristic/BM25 parser can process 100k records in ~10 seconds).

---

## 2. Identified Honeypots (118 Total Traps)
The dataset contains subtly impossible synthetic profiles designed to trap systems that rely purely on keyword matching. If these are ranked in your top 100, you will be disqualified. Our analysis identified **118 honeypot candidates** in the 100k pool:

1. **Job Duration Mismatch (21 candidates)**: 
   * **Anomalous Pattern**: A candidate's single job duration (months / 12) is larger than their overall stated `years_of_experience` (with 0.1 year tolerance). 
   * *Example*: `CAND_0007353` has a single job of 13.8 years but only claims 9.9 years of total experience.
2. **Expert Skill with 0 Duration (21 candidates)**: 
   * **Anomalous Pattern**: Candidates with skills marked as `"proficiency": "expert"` but having `"duration_months": 0`.
   * *Example*: `CAND_0016000` lists TypeScript, Go, and Docker as "expert" but with 0 months of use.
3. **AI Startup Founding Date Violations (77 candidates)**: 
   * **Anomalous Pattern**: Candidates claiming to work at modern AI startups before the startups were founded.
   * **Startup Founding Year Dictionary**:
     * `Krutrim`: 2023
     * `Sarvam AI`: 2023
     * `Rephrase.ai`: 2019
     * `Glance`: 2019
     * `Observe.AI`: 2017
     * `Saarthi.ai`: 2017
     * `Aganitha`: 2017
     * `Niramai`: 2016
     * `Wysa`: 2015
     * `Haptik`: 2013
     * `Mad Street Den`: 2013
   * *Example*: `CAND_0003599` claims to have worked at Krutrim (founded Dec 2023) since April 2022.

> [!WARNING]
> **Action**: Implement a pre-filter function in your ranking script to immediately give any of these 118 candidate IDs a score of `0.0` or exclude them entirely.

---

## 3. Disqualifiers & Critical Deductions
To match the job description, the ranking engine must apply the following logical filters:

* **Consulting-Only Careers (Disqualifier)**:
  * Candidates whose entire career is spent at consulting firms (TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini, HCL, Tech Mahindra, Mphasis, Genpact) are disqualified.
  * Candidates currently at a consulting firm are allowed **only** if they have prior product-company experience.
* **Location/Relocation Filter**:
  * Noida/Pune (Preferred Hybrid Locations): Maximum score bonus (+15).
  * Other Tier-1 Indian Cities (Bangalore, Hyderabad, Chennai, Mumbai, Delhi, NCR, Kolkata, Gurgaon, Ahmedabad): Allowed **only** if `willing_to_relocate` is `true`. If `willing_to_relocate` is `false`, apply a heavy penalty (-30).
  * Outside India: Apply a severe visa-sponsorship penalty (-40) unless they are highly exceptional.
* **Availability/Engagement Signals**:
  * If the candidate has been inactive for >180 days (6 months) based on `last_active_date`: Apply a heavy penalty (-20).
  * Recruiter response rate < 10% (`recruiter_response_rate` < 0.10): Apply penalty (-15).
  * Interview completion rate < 50%: Apply penalty (-15) as they are a no-show risk.
* **No Code in 18 Months**:
  * If the current role title is purely managerial (e.g. Engineering Manager, Architect, VP, Director) and has been active for >18 months with no coding keywords (e.g. Python, code, develop, write) in the description: Apply penalty (-20).
* **CV/Speech/Robotics Only**:
  * If a candidate has expert CV/Speech/Robotics skills (CNN, YOLO, Image Classification, Speech Recognition, TTS) but has **0** NLP/IR/Search/RAG/Embedding keywords: Apply a heavy penalty.

---

## 4. Key Scoring Criteria (Core Heuristics)
Construct a composite score using the following components:
1. **Experience Score**: Peak score for total experience between **5 and 9 years** (as specified in JD).
2. **Skill Score**: 
   * **Core Required (High Weight)**: Embeddings, Vector Search (Pinecone, Milvus, Qdrant, Weaviate, FAISS), Elasticsearch, Semantic Search, NDCG, MRR, MAP, Information Retrieval.
   * **Nice to Have (Medium Weight)**: RAG, Fine-tuning (LoRA, QLoRA, PEFT), Learning to Rank, MLOps, Python.
3. **Keyword Matching on Descriptions**: Scan `career_history` descriptions for phrases like "recommendation system", "ranking system", "search engine", "re-ranking", "A/B test", and "deployed to production".
4. **Notice Period**: Bonus for notice period ≤30 days; penalize notice periods >90 days.
5. **Engagement Signals**: Small positive weights for `open_to_work_flag`, high `recruiter_response_rate`, and recent `last_active_date`.

---

## 5. 15-Day Team Plan (3 Members)

### Phase 1: Foundation & Data Cleaning (Days 1–4)
* **Member 1 (AI)**: Code the honeypot detection rules and startup founding date filters.
* **Member 2 (Systems)**: Write a fast parser for `candidates.jsonl` and set up git repository structure.
* **Member 3 (Eval)**: Set up local test metrics (NDCG@10, NDCG@50, MAP) on a sample dataset (e.g. 1k candidates) to evaluate rankings.

### Phase 2: Feature Engineering & Scoring Engine (Days 5–8)
* **Member 1 (AI)**: Write the skill matching rules and CV/Speech/Robotics filters.
* **Member 2 (Systems)**: Write the location/relocation checks and notice period scorer.
* **Member 3 (Eval)**: Implement the behavioral signals scoring (last active, response rates, connection count).

### Phase 3: Text Search & Integration (Days 9–11)
* **Member 1 (AI)**: Add basic BM25 or keyword matching over career descriptions.
* **Member 2 (Systems)**: Combine all components into a unified pipeline and ensure runtime < 1 minute.
* **Member 3 (Eval)**: Build the reasoning generator to construct factual, non-templated reasonings for the top 100 CSV rows.

### Phase 4: Tuning, Validation & Sandbox (Days 12–15)
* **Member 1 (AI)**: Tune scoring weights to optimize NDCG/MAP on the validation set.
* **Member 2 (Systems)**: Run `validate_submission.py` and Dockerize the pipeline.
* **Member 3 (Eval)**: Build and host a simple Streamlit UI on Streamlit Cloud for the sandbox demo.

---

## 6. Sandbox / Demo Requirement
A frontend is **not** required, but a hosted demo link is mandatory. We recommend using **Streamlit** (written in pure Python) and hosting it on **Streamlit Cloud** (free tier). The app should:
1. Accept a file upload of ≤100 sample candidates.
2. Run your Python scoring pipeline.
3. Show the ranked list and allow downloading the output CSV.
