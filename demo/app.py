import streamlit as st
import json
import pandas as pd
import sys
import os

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.jd_parser import parse_job_description
from src.data_processor import check_is_honeypot, check_is_consulting_disqualified

st.set_page_config(
    page_title="AI Recruiter Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .hero-title {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2, #f64f59);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e2230, #252d3a);
        border-radius: 12px;
        padding: 18px;
        border: 1px solid #2e3440;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-card h4 { color: #9ca3af; font-size: 0.8rem; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
    .metric-card h2 { color: #ffffff; font-size: 2rem; font-weight: 700; margin: 0; }
    .criteria-box {
        background: #1a1f2e;
        border: 1px solid #2e3440;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 8px;
    }
    .tag {
        display: inline-block;
        background: #2d3748;
        border-radius: 6px;
        padding: 3px 10px;
        font-size: 0.75rem;
        color: #a0aec0;
        margin: 2px;
    }
    .tag-core { background: rgba(102, 126, 234, 0.2); color: #818cf8; border: 1px solid #4f46e5; }
    .tag-pref { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border: 1px solid #059669; }
    .stButton>button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white; border: none; padding: 10px 28px;
        font-weight: 600; border-radius: 8px; width: 100%;
        transition: all 0.3s;
    }
    .stButton>button:hover { opacity: 0.88; transform: translateY(-1px); }
    .section-header { 
        font-size: 1.1rem; font-weight: 600; color: #e2e8f0;
        border-left: 3px solid #667eea; padding-left: 10px; margin: 18px 0 10px 0; 
    }
</style>
""", unsafe_allow_html=True)

# ─── HERO ─────────────────────────────────────────────────────────────
st.markdown("<div class='hero-title'>🧠 General AI Recruiter Brain</div>", unsafe_allow_html=True)
st.markdown("Upload **any Job Description** + a **candidate pool** and let the AI Brain automatically extract hiring criteria, filter traps, and rank the best fits.")
st.markdown("---")

# ─── SIDEBAR ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ How It Works")
    st.info(
        "**1. Upload JD** → AI reads and extracts:\n"
        "- Experience range\n"
        "- Preferred locations\n"
        "- Core & preferred skills\n"
        "- Whether consulting filter applies\n\n"
        "**2. Upload Candidates** → System:\n"
        "- Streams profiles efficiently\n"
        "- Removes honeypots (data traps)\n"
        "- Applies JD-driven consulting filter\n\n"
        "**3. View Results** → Ranked shortlist\n"
        "with fact-based reasoning"
    )
    st.markdown("---")
    st.markdown("**Phase 0 (Complete ✅)**")
    st.caption("JD Parsing, Honeypot Detection, Dynamic Consulting Filter")
    st.markdown("**Phase 1 (Next 🔜)**")
    st.caption("Feature Engineering, Semantic Scoring, Reasoning")

# ─── STEP 1: JD UPLOAD ────────────────────────────────────────────────
st.markdown("<div class='section-header'>Step 1 — Upload Job Description</div>", unsafe_allow_html=True)
jd_col1, jd_col2 = st.columns([2, 1])

with jd_col1:
    jd_file = st.file_uploader("Upload JD as .txt or .md file", type=["txt", "md"], key="jd_file")
with jd_col2:
    st.markdown("&nbsp;")
    use_sample_jd = st.checkbox("Use sample Redrob JD", value=False)

criteria = None
jd_text = None

if use_sample_jd:
    sample_jd_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "India_runs_data_and_ai_challenge", "job_description.txt")
    if os.path.exists(sample_jd_path):
        with open(sample_jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read()
        st.success("Loaded sample Redrob JD ✅")
    else:
        st.error("Sample JD file not found. Please upload your own.")
elif jd_file is not None:
    jd_text = jd_file.read().decode("utf-8")
    st.success(f"Loaded JD: **{jd_file.name}** ✅")

if jd_text:
    criteria = parse_job_description(jd_text)

    with st.expander("📋 View Extracted JD Criteria", expanded=True):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(f"<div class='metric-card'><h4>Experience Range</h4><h2>{criteria.min_yoe:.0f} – {criteria.max_yoe:.0f} yrs</h2></div>", unsafe_allow_html=True)
        with col_b:
            preferred = ", ".join(sorted(criteria.preferred_locations)) if criteria.preferred_locations else "Any"
            st.markdown(f"<div class='metric-card'><h4>Preferred Locations</h4><h2 style='font-size:1.1rem;margin-top:8px'>{preferred}</h2></div>", unsafe_allow_html=True)
        with col_c:
            consult_label = "❌ Yes — JD Excludes Consulting-Only" if criteria.disallow_consulting else "✅ No — Consulting Allowed"
            consult_color = "#ef4444" if criteria.disallow_consulting else "#10b981"
            st.markdown(f"<div class='metric-card'><h4>Consulting Filter</h4><h2 style='font-size:0.85rem;color:{consult_color};margin-top:6px'>{consult_label}</h2></div>", unsafe_allow_html=True)

        st.markdown("**Core Required Skills:**")
        core_tags = "".join([f"<span class='tag tag-core'>{s}</span>" for s in sorted(criteria.core_skills)])
        st.markdown(core_tags, unsafe_allow_html=True)

        st.markdown("**Preferred / Nice-to-Have Skills:**")
        pref_tags = "".join([f"<span class='tag tag-pref'>{s}</span>" for s in sorted(criteria.preferred_skills)])
        st.markdown(pref_tags, unsafe_allow_html=True)

        if criteria.tier1_locations:
            st.caption(f"Other Tier-1 locations found: {', '.join(sorted(criteria.tier1_locations))}")

st.markdown("---")

# ─── STEP 2: CANDIDATE UPLOAD ─────────────────────────────────────────
st.markdown("<div class='section-header'>Step 2 — Upload Candidate Pool</div>", unsafe_allow_html=True)
cand_col1, cand_col2 = st.columns([2, 1])

with cand_col1:
    cand_file = st.file_uploader("Upload candidates as .json or .jsonl (≤100 profiles)", type=["json", "jsonl"], key="cand_file")
with cand_col2:
    st.markdown("&nbsp;")
    use_sample_cands = st.checkbox("Use sample candidates (50 profiles)", value=False)

raw_candidates = []

if use_sample_cands:
    sample_cand_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    "India_runs_data_and_ai_challenge", "sample_candidates.json")
    if os.path.exists(sample_cand_path):
        with open(sample_cand_path, "r", encoding="utf-8") as f:
            raw_candidates = json.load(f)
        st.success(f"Loaded {len(raw_candidates)} sample candidates ✅")
    else:
        st.error("Sample candidates file not found.")
elif cand_file is not None:
    content = cand_file.read().decode("utf-8")
    if cand_file.name.endswith(".jsonl"):
        raw_candidates = [json.loads(l) for l in content.splitlines() if l.strip()]
    else:
        try:
            raw_candidates = json.loads(content)
            if not isinstance(raw_candidates, list):
                raw_candidates = [json.loads(l) for l in content.splitlines() if l.strip()]
        except json.JSONDecodeError:
            raw_candidates = [json.loads(l) for l in content.splitlines() if l.strip()]
    st.success(f"Loaded {len(raw_candidates)} candidates from **{cand_file.name}** ✅")

if len(raw_candidates) > 100:
    st.warning("Truncating to first 100 for sandbox performance.")
    raw_candidates = raw_candidates[:100]

st.markdown("---")

# ─── STEP 3: RUN PIPELINE ─────────────────────────────────────────────
st.markdown("<div class='section-header'>Step 3 — Run Filtering Pipeline</div>", unsafe_allow_html=True)

if criteria and raw_candidates:
    if st.button("🚀 Run Filtering & Analysis"):
        valid_candidates = []
        honeypots = []
        consulting_filtered = []

        for cand in raw_candidates:
            is_hp, hp_reason = check_is_honeypot(cand)
            if is_hp:
                honeypots.append({
                    "candidate_id": cand["candidate_id"],
                    "name": cand["profile"]["anonymized_name"],
                    "reason": hp_reason
                })
                continue

            if criteria.disallow_consulting:
                is_cd, cd_reason = check_is_consulting_disqualified(cand)
                if is_cd:
                    consulting_filtered.append({
                        "candidate_id": cand["candidate_id"],
                        "name": cand["profile"]["anonymized_name"],
                        "reason": cd_reason
                    })
                    continue

            valid_candidates.append(cand)

        # Stats cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-card'><h4>Total Input</h4><h2>{len(raw_candidates)}</h2></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><h4>Valid Candidates</h4><h2 style='color:#10b981'>{len(valid_candidates)}</h2></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-card' style='border-color:#ef4444'><h4>Honeypots Removed</h4><h2 style='color:#ef4444'>{len(honeypots)}</h2></div>", unsafe_allow_html=True)
        with c4:
            label = f"{len(consulting_filtered)} Filtered" if criteria.disallow_consulting else "N/A (Allowed)"
            color = "#f59e0b" if criteria.disallow_consulting else "#6b7280"
            st.markdown(f"<div class='metric-card' style='border-color:{color}'><h4>Consulting Filter</h4><h2 style='color:{color}'>{label}</h2></div>", unsafe_allow_html=True)

        # Valid candidates preview
        if valid_candidates:
            st.markdown("#### ✅ Valid Candidates Preview")
            preview_rows = [{
                "candidate_id": c["candidate_id"],
                "name": c["profile"]["anonymized_name"],
                "title": c["profile"]["current_title"],
                "yoe": c["profile"]["years_of_experience"],
                "location": c["profile"]["location"],
                "country": c["profile"]["country"]
            } for c in valid_candidates]
            st.dataframe(pd.DataFrame(preview_rows), use_container_width=True)

        # Honeypots table
        if honeypots:
            with st.expander(f"🚨 Show {len(honeypots)} Detected Honeypots"):
                st.table(pd.DataFrame(honeypots))

        # Consulting filter table
        if consulting_filtered:
            with st.expander(f"⚠️ Show {len(consulting_filtered)} Consulting-Filtered Candidates"):
                st.table(pd.DataFrame(consulting_filtered))

        if not criteria.disallow_consulting:
            st.info("ℹ️ The uploaded JD does not explicitly exclude consulting backgrounds. All consulting candidates are allowed through.")

        st.success("🔜 **Next**: Scoring, ranking, and reasoning generation will be added in Phase 1.")

elif not criteria:
    st.info("👆 Please upload or select a Job Description in Step 1.")
elif not raw_candidates:
    st.info("👆 Please upload or select candidates in Step 2.")
