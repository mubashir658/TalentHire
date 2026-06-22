#!/usr/bin/env python3
import argparse
import sys
import os

# Ensure the root of the project is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.jd_parser import parse_job_description

def main():
    parser = argparse.ArgumentParser(description="General AI Brain for Intelligent Candidate Discovery & Ranking")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl file")
    parser.add_argument("--jd", required=True, help="Path to job description text file")
    parser.add_argument("--out", required=True, help="Path to write the output CSV")
    args = parser.parse_args()

    print("==================================================")
    print("🤖 GENERAL AI RECRUITER BRAIN: PHASE 0 INITIALIZATION")
    print("==================================================")
    
    # 1. Verify files exist
    if not os.path.exists(args.candidates):
        print(f"Error: Candidate file not found at: {args.candidates}")
        sys.exit(1)
    if not os.path.exists(args.jd):
        print(f"Error: Job description file not found at: {args.jd}")
        sys.exit(1)
        
    print(f"Candidates Pool File: {args.candidates}")
    print(f"Job Description File: {args.jd}")
    print(f"Output Submission File: {args.out}")
    print("--------------------------------------------------")

    # 2. Parse Job Description dynamically
    print("Reading and parsing job description...")
    with open(args.jd, "r", encoding="utf-8") as f_jd:
        jd_text = f_jd.read()
        
    criteria = parse_job_description(jd_text)
    
    print("\n[ Extracted Job Criteria ]")
    print(f"Experience Bounds: {criteria.min_yoe} to {criteria.max_yoe} years")
    print(f"Preferred Locations: {sorted(list(criteria.preferred_locations))}")
    print(f"Tier-1 Indian Locations Match: {sorted(list(criteria.tier1_locations))}")
    print(f"Is India-based role: {criteria.is_india_role}")
    print(f"Extracted Core Skills: {sorted(list(criteria.core_skills))}")
    print(f"Extracted Preferred Skills: {sorted(list(criteria.preferred_skills))}")
    print("--------------------------------------------------")
    
    print("\n[ Pipeline Execution Status ]")
    print("Data parsing, filtering, scoring, and ranking phases are currently pending.")
    print("Phase 0 skeleton completed successfully.")
    print("==================================================")

if __name__ == "__main__":
    main()
