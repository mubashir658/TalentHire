import re
from datetime import datetime
from src.config import (
    PREFERRED_LOCATIONS, TIER1_LOCATIONS, CORE_REQUIRED_SKILLS, 
    NICE_TO_HAVE_SKILLS, CV_SPEECH_ROBOTICS_SKILLS, NLP_IR_SEARCH_KEYWORDS
)

# Reference date for activity calculations (hackathon date is around June 2026)
REFERENCE_DATE = datetime(2026, 6, 1)

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m")
        except ValueError:
            return None

def calculate_yoe_score(yoe):
    """
    Experience Score: Peak fit at 5-9 years.
    Returns a score between 0.0 and 1.0.
    """
    if 5.0 <= yoe <= 9.0:
        return 1.0
    elif yoe < 5.0:
        # Linear ramp from 0.0 to 1.0
        return yoe / 5.0
    else:
        # Slow decay for overqualified candidates
        return max(0.0, 1.0 - (yoe - 9.0) * 0.1)

def calculate_location_features(cand):
    """
    Location relocation logic.
    Returns:
      - is_preferred: bool
      - penalty: float
      - reloc_info: str (for reasoning)
    """
    location = cand["profile"].get("location", "").strip()
    country = cand["profile"].get("country", "").strip()
    willing_to_relocate = cand["redrob_signals"].get("willing_to_relocate", False)
    
    # Check if outside India
    if country.lower() != "india":
        return False, -40.0, "Outside India (visa penalty)"
        
    # Check if in Pune or Noida (preferred locations)
    # Check for direct inclusion or word matching
    is_pune_noida = False
    for loc in PREFERRED_LOCATIONS:
        if loc.lower() in location.lower():
            is_pune_noida = True
            break
            
    if is_pune_noida:
        return True, 15.0, "Pune/Noida-based (preferred hybrid)"
        
    # Check if in other Tier-1 Indian cities
    is_tier1 = False
    for loc in TIER1_LOCATIONS:
        if loc.lower() in location.lower():
            is_tier1 = True
            break
            
    if is_tier1:
        if willing_to_relocate:
            return False, 0.0, f"Tier-1 city ({location}) and willing to relocate"
        else:
            return False, -30.0, f"Tier-1 city ({location}) but NOT willing to relocate"
            
    # Outside preferred and other Tier-1, inside India
    if willing_to_relocate:
        return False, 0.0, f"Located in {location} and willing to relocate"
    else:
        return False, -30.0, f"Located in {location} and NOT willing to relocate"

def calculate_availability_signals(cand):
    """
    Calculates behavioral penalties and bonuses.
    Returns:
      - penalty: float
      - reasons: list of warning strings
    """
    signals = cand["redrob_signals"]
    penalty = 0.0
    warnings = []
    
    # 1. Inactive > 180 days
    last_active_str = signals.get("last_active_date")
    last_active = parse_date(last_active_str)
    if last_active:
        days_inactive = (REFERENCE_DATE - last_active).days
        if days_inactive > 180:
            penalty += -20.0
            warnings.append("inactive > 180 days")
            
    # 2. Recruiter response rate < 10%
    rrr = signals.get("recruiter_response_rate", 1.0)
    if rrr < 0.10:
        penalty += -15.0
        warnings.append("low response rate (<10%)")
        
    # 3. Interview completion rate < 50%
    icr = signals.get("interview_completion_rate", 1.0)
    if icr < 0.50:
        penalty += -15.0
        warnings.append("low interview completion (<50%)")
        
    # 4. Open to work flag
    if signals.get("open_to_work_flag", False):
        penalty += 5.0 # small bonus
        
    return penalty, warnings

def check_managerial_status(cand):
    """
    Check if candidate has been purely managerial for >18 months with no coding keyword.
    Returns:
      - is_managerial_only: bool
      - penalty: float
    """
    history = cand.get("career_history", [])
    if not history:
        return False, 0.0
        
    # Check most recent / current job
    current_jobs = [job for job in history if job.get("is_current")]
    if not current_jobs:
        current_jobs = [history[0]]
        
    job = current_jobs[0]
    title = job.get("title", "").lower()
    description = job.get("description", "").lower()
    duration = job.get("duration_months", 0)
    
    # Managerial title keywords
    managerial_keywords = ["manager", "director", "vp", "vice president", "architect", "lead", "head", "chief"]
    technical_keywords = ["developer", "engineer", "programmer", "scientist"]
    
    is_mgmt_title = any(kw in title for kw in managerial_keywords) and not any(kw in title for kw in technical_keywords)
    
    if is_mgmt_title and duration > 18:
        # Check for coding keywords in the description
        coding_keywords = ["python", "code", "develop", "write", "build", "programming", "sql", "git", "deploy", "implement"]
        has_coding = any(kw in description for kw in coding_keywords)
        if not has_coding:
            return True, -20.0
            
    return False, 0.0

def check_cv_speech_robotics_only(cand):
    """
    Check if candidate has expert CV/speech/robotics skills but 0 NLP/IR keywords.
    Returns:
      - is_specialized_only: bool
      - penalty: float
    """
    skills = cand.get("skills", [])
    profile_text = (cand["profile"].get("headline", "") + " " + cand["profile"].get("summary", "")).lower()
    
    # Check expert CV/Speech/Robotics skills
    has_expert_cv_speech_rob = False
    for skill in skills:
        skill_name = skill.get("name", "").lower()
        if skill.get("proficiency") in ["expert", "advanced"] and any(s in skill_name for s in CV_SPEECH_ROBOTICS_SKILLS):
            has_expert_cv_speech_rob = True
            break
            
    if not has_expert_cv_speech_rob:
        return False, 0.0
        
    # Check if there are any NLP/IR/Search/RAG/Embedding keywords in profile or skills
    has_nlp_ir = False
    # Check in skills
    for skill in skills:
        skill_name = skill.get("name", "").lower()
        if any(kw in skill_name for kw in NLP_IR_SEARCH_KEYWORDS):
            has_nlp_ir = True
            break
            
    # Check in profile summary/headline
    if not has_nlp_ir:
        if any(kw in profile_text for kw in NLP_IR_SEARCH_KEYWORDS):
            has_nlp_ir = True
            
    if has_expert_cv_speech_rob and not has_nlp_ir:
        return True, -35.0
        
    return False, 0.0

def calculate_notice_period_score(cand):
    """
    Notice Period: Bonus for notice period <=30 days, penalty for >90 days.
    Returns:
      - score: float
      - notice_info: str
    """
    notice_days = cand["redrob_signals"].get("notice_period_days", 90)
    if notice_days <= 30:
        return 10.0, "notice <= 30 days"
    elif notice_days > 90:
        return -15.0, "notice > 90 days"
    else:
        return 0.0, "standard notice"

def extract_features(cand):
    """
    Wrapper function to extract all structured scoring features for a candidate.
    """
    yoe = cand["profile"]["years_of_experience"]
    yoe_score = calculate_yoe_score(yoe)
    
    loc_preferred, loc_score, loc_info = calculate_location_features(cand)
    avail_score, avail_warnings = calculate_availability_signals(cand)
    is_mgmt, mgmt_score = check_managerial_status(cand)
    is_cv_speech_only, cv_speech_score = check_cv_speech_robotics_only(cand)
    notice_score, notice_info = calculate_notice_period_score(cand)
    
    # Calculate basic skill count features
    skills = cand.get("skills", [])
    core_count = 0
    nice_count = 0
    for skill in skills:
        skill_name = skill.get("name", "").lower()
        if any(s in skill_name for s in CORE_REQUIRED_SKILLS):
            core_count += 1
        elif any(s in skill_name for s in NICE_TO_HAVE_SKILLS):
            nice_count += 1
            
    # Calculate GitHub activity score
    github_score = cand["redrob_signals"].get("github_activity_score", -1)
    
    return {
        "yoe": yoe,
        "yoe_score": yoe_score,
        "loc_preferred": loc_preferred,
        "loc_score": loc_score,
        "loc_info": loc_info,
        "avail_score": avail_score,
        "avail_warnings": avail_warnings,
        "is_mgmt": is_mgmt,
        "mgmt_score": mgmt_score,
        "is_cv_speech_only": is_cv_speech_only,
        "cv_speech_score": cv_speech_score,
        "notice_score": notice_score,
        "notice_info": notice_info,
        "core_skills_count": core_count,
        "nice_skills_count": nice_count,
        "github_score": github_score
    }
