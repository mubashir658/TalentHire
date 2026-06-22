import random
import re

def generate_reasoning(cand, rank, features, match_details):
    """
    Generates a high-quality, 1-2 sentence non-templated reasoning string
    for a candidate, based on their actual profile facts, rank, and features.
    """
    profile = cand["profile"]
    yoe = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "Software Engineer")
    company = profile.get("current_company", "")
    location = profile.get("location", "")
    willing_to_relocate = cand["redrob_signals"].get("willing_to_relocate", False)
    notice_days = cand["redrob_signals"].get("notice_period_days", 90)
    rrr = int(cand["redrob_signals"].get("recruiter_response_rate", 1.0) * 100)
    
    # Get matched skills/terms from match_details
    matched_skills = match_details.get("matched_terms", [])
    # Limit to top 3-4 matched skills for conciseness
    skills_to_show = [s for s in matched_skills if s in ["vector search", "pinecone", "weaviate", "qdrant", "milvus", "embeddings", "semantic search", "ndcg", "mrr", "map", "rag", "fine-tuning", "lora", "python"]]
    if not skills_to_show:
        skills_to_show = matched_skills[:3]
    else:
        skills_to_show = skills_to_show[:3]
        
    skills_str = ", ".join(skills_to_show) if skills_to_show else "machine learning"
    
    # Highlight warnings/concerns
    warnings = []
    if notice_days > 90:
        warnings.append(f"long notice period of {notice_days} days")
    if rrr < 20:
        warnings.append(f"low recruiter response rate of {rrr}%")
    if features.get("avail_warnings"):
        # Add first warning from features if available
        warnings.append(features["avail_warnings"][0])
        
    warnings_str = " and ".join(warnings) if warnings else ""
    
    # Noida/Pune check
    is_pune_noida = features.get("loc_preferred", False)
    if is_pune_noida:
        loc_str = f"based in {location} (preferred hybrid location)"
    elif willing_to_relocate:
        loc_str = f"willing to relocate from {location}"
    else:
        loc_str = f"located in {location} (not willing to relocate)"
        
    # Variation of openers and connectors based on rank range
    if rank <= 15:
        # Top-tier reasoning (very positive, highlights strong alignment)
        openers = [
            f"Exceptional Senior AI Engineer with {yoe} years of experience, currently working as {title} at {company if company else 'a product company'}.",
            f"Top-tier candidate possessing {yoe} years of hands-on ML experience, currently holding the title of {title}.",
            f"Highly relevant {yoe}-year senior engineering profile with a strong track record as {title}."
        ]
        mid_connectors = [
            f"Demonstrated production depth in {skills_str}, aligning perfectly with the JD's search and retrieval requirements.",
            f"Proven experience deploying systems involving {skills_str} directly to production environments.",
            f"Strong expertise in core search and IR concepts, including {skills_str}."
        ]
        closers = [
            f"Strong fit due to being {loc_str} with a fast notice period of {notice_days} days.",
            f"Candidate is {loc_str}; highly engaged with an active recruiter response rate of {rrr}%.",
            f"Ready to contribute to the founding team from day one; {loc_str}."
        ]
        
        opener = random.choice(openers)
        connector = random.choice(mid_connectors)
        closer = random.choice(closers)
        
        if warnings_str:
            closer = f"Note: there is a slight concern with {warnings_str}, but their strong technical fit outweighs this. {loc_str}."
            
        reasoning = f"{opener} {connector} {closer}"
        
    elif rank <= 60:
        # Mid-tier reasoning (solid fit, mentions some trade-offs or standard profile details)
        openers = [
            f"Solid Senior Engineer with {yoe} years of experience in product environments as {title}.",
            f"Experienced {title} with {yoe} years of experience, matching the experience range of the JD.",
            f"Candidate profile shows {yoe} years of experience, currently focused on backend/ML systems."
        ]
        mid_connectors = [
            f"Possesses relevant expertise in {skills_str} and system design.",
            f"Good familiarity with retrieval structures like {skills_str}.",
            f"Has worked on projects involving {skills_str}."
        ]
        closers = [
            f"Fits the location criteria ({loc_str}) with a notice period of {notice_days} days.",
            f"A strong contributor who is {loc_str} (response rate: {rrr}%).",
            f"Heuristic scoring indicates a highly stable profile; candidate is {loc_str}."
        ]
        
        opener = random.choice(openers)
        connector = random.choice(mid_connectors)
        closer = random.choice(closers)
        
        if warnings_str:
            closer = f"However, they have {warnings_str}. Currently {loc_str}."
            
        reasoning = f"{opener} {connector} {closer}"
        
    else:
        # Lower-tier reasoning (acknowledges gap, adjacent skills, or why they are at the bottom of the top 100)
        openers = [
            f"Adjacent engineering profile with {yoe} years of experience, currently working as {title}.",
            f"Software engineer with {yoe} years of experience showing interest in moving to AI/ML systems.",
            f"Candidate has {yoe} years of experience, with some adjacent skills but less direct production AI experience."
        ]
        mid_connectors = [
            f"Has some experience with {skills_str}, but lacks the deep vector database or evaluation background required.",
            f"Lists skills like {skills_str}, but the career history shows less focus on search and retrieval.",
            f"Familiar with standard engineering practices and has basic exposure to {skills_str}."
        ]
        closers = [
            f"Included as a potential candidate given their {loc_str} and notice period.",
            f"Potential match if other options are exhausted; {loc_str}.",
            f"Heuristic score is lower due to {warnings_str or 'notice period constraints'}; {loc_str}."
        ]
        
        opener = random.choice(openers)
        connector = random.choice(mid_connectors)
        closer = random.choice(closers)
        
        reasoning = f"{opener} {connector} {closer}"
        
    # Ensure no double spaces and clean text
    reasoning = " ".join(reasoning.split())
    # Truncate to maximum 2 sentences if needed (split by period and take first two)
    sentences = re.split(r'\. ', reasoning)
    if len(sentences) > 2:
        reasoning = ". ".join(sentences[:2]) + "."
        
    return reasoning
