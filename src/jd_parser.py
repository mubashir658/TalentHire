import re
from src.config import PREFERRED_LOCATIONS, TIER1_LOCATIONS, CORE_REQUIRED_SKILLS, NICE_TO_HAVE_SKILLS

# Phrases that unambiguously indicate a JD is discouraging consulting-only backgrounds.
# These must be clearly negative — not just mentions of consulting in neutral/positive context.
CONSULTING_EXCLUSION_PHRASES = [
    "only worked at consulting",
    "consulting-only",
    "no consulting",
    "not from consulting",
    "tcs, infosys, wipro",
    "infosys, wipro",
    "not want people who have only worked at",
    "exclusively from services",
    "spent their career at consulting",
]

# Known IT consulting/services company names to detect in JD
CONSULTING_COMPANY_MENTIONS = [
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "tech mahindra", "mphasis", "genpact", "mindtree", "ltimindtree"
]

class DynamicCriteria:
    def __init__(self):
        self.min_yoe = 0.0
        self.max_yoe = 50.0
        self.preferred_locations = set()
        self.tier1_locations = set()
        self.core_skills = set()
        self.preferred_skills = set()
        self.is_india_role = True
        # Set to True only if the JD explicitly signals discomfort with consulting-only careers
        self.disallow_consulting = False

def parse_job_description(jd_text):
    """
    Parses arbitrary job description text and extracts criteria dynamically.
    """
    criteria = DynamicCriteria()
    if not jd_text:
        return criteria

    jd_lower = jd_text.lower()

    # 1. Extract Years of Experience (YOE)
    # Pattern examples: "5-9 years", "5–9 years" (en-dash), "5 to 9 years", "3+ years", "over 5 years"
    yoe_range_match = re.search(r'(\d+)\s*[-–to]+\s*(\d+)\s*(?:years|yrs)', jd_text)
    yoe_plus_match = re.search(r'(\d+)\s*\+\s*(?:years|yrs)', jd_text)
    yoe_over_match = re.search(r'(?:over|greater than|more than)\s*(\d+)\s*(?:years|yrs)', jd_text, re.IGNORECASE)

    if yoe_range_match:
        criteria.min_yoe = float(yoe_range_match.group(1))
        criteria.max_yoe = float(yoe_range_match.group(2))
    elif yoe_plus_match:
        criteria.min_yoe = float(yoe_plus_match.group(1))
        criteria.max_yoe = max(50.0, criteria.min_yoe + 5.0)  # Default upper bound
    elif yoe_over_match:
        criteria.min_yoe = float(yoe_over_match.group(1))
        criteria.max_yoe = max(50.0, criteria.min_yoe + 5.0)

    # 2. Extract Locations
    # Check for preferred tech hub cities
    for loc in PREFERRED_LOCATIONS:
        if loc.lower() in jd_lower:
            criteria.preferred_locations.add(loc)
    
    for loc in TIER1_LOCATIONS:
        if loc.lower() in jd_lower:
            criteria.tier1_locations.add(loc)
            
    # Check for country-specific flags
    # E.g. If JD says "based in India" or mentions Indian cities, is_india_role is True.
    # If it says "visa sponsorship: no" and mentions "US", "Sydney", "London", we adjust.
    if "outside india" in jd_lower or "us based" in jd_lower or "london" in jd_lower or "sydney" in jd_lower:
        # Check if India is also mentioned
        if "india" not in jd_lower:
            criteria.is_india_role = False

    # 3. Extract Skills (Core vs Nice-to-have)
    # Split text into sections to identify lists of skills
    sections = re.split(r'\n\s*\n', jd_text)
    
    core_section_text = ""
    pref_section_text = ""
    
    # Simple heuristics to find sections
    for sec in sections:
        sec_lower = sec.lower()
        if any(phrase in sec_lower for phrase in ["absolutely need", "must have", "required", "requirements", "core skills"]):
            core_section_text += " " + sec_lower
        elif any(phrase in sec_lower for phrase in ["like you to have", "nice to have", "plus", "preferred", "desirable"]):
            pref_section_text += " " + sec_lower
            
    # If no specific sections were found, search the whole text
    if not core_section_text:
        core_section_text = jd_lower
    if not pref_section_text:
        pref_section_text = jd_lower

    # Match skills from a known vocabulary first
    for skill in CORE_REQUIRED_SKILLS:
        if skill in core_section_text:
            criteria.core_skills.add(skill)
            
    for skill in NICE_TO_HAVE_SKILLS:
        if skill in pref_section_text:
            # If it's already in core (due to overlapping sections), keep in core
            if skill not in criteria.core_skills:
                criteria.preferred_skills.add(skill)

    # Fallback: if we didn't extract any core skills, use default ones
    if not criteria.core_skills:
        criteria.core_skills = CORE_REQUIRED_SKILLS.copy()
    if not criteria.preferred_skills:
        criteria.preferred_skills = NICE_TO_HAVE_SKILLS.copy()

    # 4. Detect if JD explicitly discourages consulting-only backgrounds
    #
    # Strategy:
    #   - Scan for explicit exclusion phrases such as "consulting-only", "not a fit"
    #   - Also check if consulting company names appear in a negative context
    #     (i.e., within 100 characters of negative signals like "do not", "avoid", "won't", "not fit")
    #   - Default is False (i.e., consulting is allowed) unless there are clear signals.
    disallow_consulting = False

    # Check explicit phrases
    for phrase in CONSULTING_EXCLUSION_PHRASES:
        if phrase in jd_lower:
            disallow_consulting = True
            break

    # Check if consulting company names appear near negative sentiment words in the JD
    if not disallow_consulting:
        negative_words = ["do not want", "don't want", "not a fit", "not fit", "avoid", "won't consider", "explicitly"]
        for company in CONSULTING_COMPANY_MENTIONS:
            company_pos = jd_lower.find(company)
            if company_pos != -1:
                # Look in a 150-char window around the company mention for a negative word
                window = jd_lower[max(0, company_pos - 150): company_pos + 150]
                if any(neg in window for neg in negative_words):
                    disallow_consulting = True
                    break

    criteria.disallow_consulting = disallow_consulting

    return criteria
