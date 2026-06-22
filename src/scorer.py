def calculate_composite_score(cand, text_score, features):
    """
    Combines the text matching score with structured features, bonuses, and penalties.
    Returns:
      - score: float
      - score_components: dict (useful for reasoning generation)
    """
    # 1. Text Relevance Score (weight: 60)
    # text_score is typically between 0.0 and ~0.8
    # We multiply by 60 to make it the primary signal
    text_component = text_score * 60.0
    
    # 2. Experience Score (weight: 15)
    yoe_component = features["yoe_score"] * 15.0
    
    # 3. Location Bonus/Penalty
    # +15 for Noida/Pune, 0 for relocatable, -30 for non-relocatable, -40 for outside India
    loc_component = features["loc_score"]
    
    # 4. Availability/Engagement Signal Adjustments
    # Inactivity: -20, low response: -15, low interview completion: -15, open to work: +5
    avail_component = features["avail_score"]
    
    # 5. Managerial Penalty
    # Pure manager for >18 months with no coding: -20
    mgmt_component = features["mgmt_score"]
    
    # 6. CV/Speech/Robotics Only Penalty
    # Specialized without NLP/IR: -35
    cv_speech_component = features["cv_speech_score"]
    
    # 7. Notice Period Bonus/Penalty
    # <=30 days: +10, >90 days: -15
    notice_component = features["notice_score"]
    
    # 8. GitHub Activity Bonus
    # github_score ranges from -1 to 100. Let's add up to +5 points for high activity.
    github_bonus = 0.0
    if features["github_score"] > 0:
        github_bonus = (features["github_score"] / 100.0) * 5.0
        
    # Calculate raw sum
    raw_score = (
        text_component + 
        yoe_component + 
        loc_component + 
        avail_component + 
        mgmt_component + 
        cv_speech_component + 
        notice_component + 
        github_bonus
    )
    
    # Normalize score to be non-negative and scaled cleanly
    # Let's map raw_score to a typical 0.0 - 100.0 range
    final_score = max(0.001, round(raw_score, 3))
    
    components = {
        "text_component": text_component,
        "yoe_component": yoe_component,
        "loc_component": loc_component,
        "avail_component": avail_component,
        "mgmt_component": mgmt_component,
        "cv_speech_component": cv_speech_component,
        "notice_component": notice_component,
        "github_bonus": github_bonus
    }
    
    return final_score, components
