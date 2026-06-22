import re
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Let's define target terms and their importance weights for custom keyword boosting
TARGET_TERMS = {
    # Core search/retrieval terms (Highest weight)
    'vector search': 5.0,
    'semantic search': 5.0,
    'embeddings': 4.0,
    'information retrieval': 4.0,
    'pinecone': 4.0,
    'weaviate': 4.0,
    'qdrant': 4.0,
    'milvus': 4.0,
    'faiss': 4.0,
    'elasticsearch': 3.5,
    'opensearch': 3.5,
    'ndcg': 4.0,
    'mrr': 4.0,
    'map': 3.5,
    
    # Secondary technical terms (Medium weight)
    'rag': 3.0,
    'retrieval-augmented generation': 3.0,
    'learning to rank': 3.0,
    'fine-tuning': 2.5,
    'lora': 2.5,
    'qlora': 2.5,
    'peft': 2.0,
    'xgboost': 2.0,
    'lightgbm': 2.0,
    'python': 2.0,
    
    # General product/engineering context (Lower weight)
    'deployed to production': 2.0,
    'production deployment': 2.0,
    'ab test': 1.5,
    'a/b test': 1.5,
    'recommendation system': 2.0,
    'ranking system': 2.0,
    'search engine': 2.0,
}

# Compile regular expressions for fast keyword matching
BOOST_PATTERNS = {term: re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE) for term in TARGET_TERMS}

class CandidateTextRanker:
    def __init__(self):
        # Build query text by replicating important terms by their weights
        query_parts = []
        for term, weight in TARGET_TERMS.items():
            # Add the term multiple times proportional to its weight to construct a weighted query vector
            count = int(weight * 2)
            query_parts.extend([term] * count)
        
        self.query_text = " ".join(query_parts)
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), 
            stop_words='english',
            token_pattern=r'(?u)\b[\w-]+\b' # Include words with hyphens (e.g. fine-tuning, a/b)
        )
        self.fitted = False

    def build_candidate_document(self, cand):
        """
        Builds a single text document representing the candidate's profile, career history, and skills.
        """
        profile = cand["profile"]
        headline = profile.get("headline", "")
        summary = profile.get("summary", "")
        
        # Skills text
        skills = []
        for s in cand.get("skills", []):
            skills.append(f"{s.get('name', '')} {s.get('proficiency', '')}")
        skills_text = ", ".join(skills)
        
        # Career History text
        careers = []
        for job in cand.get("career_history", []):
            company = job.get("company", "")
            title = job.get("title", "")
            desc = job.get("description", "")
            careers.append(f"{title} at {company}. {desc}")
        career_text = " ".join(careers)
        
        # Combine
        doc = f"{headline}. {summary}. Skills: {skills_text}. History: {career_text}"
        return doc

    def fit_and_score(self, candidates):
        """
        Fits TF-IDF vectorizer on all candidate documents and calculates cosine similarity to the query.
        Also calculates custom keyword boosts.
        Returns:
            - list of float: similarity scores (length equals candidates count)
            - list of dict: matches info (for reasoning generation)
        """
        documents = [self.build_candidate_document(c) for c in candidates]
        
        # Fit TF-IDF on candidate documents + the query
        corpus = documents + [self.query_text]
        tfidf_matrix = self.vectorizer.fit_transform(corpus)
        
        # The query vector is the last element
        query_vector = tfidf_matrix[-1]
        candidates_matrix = tfidf_matrix[:-1]
        
        # Compute cosine similarity: (A . B) / (||A|| ||B||)
        # tfidf_matrix vectors are normalized by TfidfVectorizer, so cosine similarity is simple dot product
        similarities = (candidates_matrix * query_vector.T).toarray().flatten()
        
        # Compute custom boosts based on exact matching of key terms in skills/history
        final_scores = []
        match_details = []
        
        for i, cand in enumerate(candidates):
            doc_lower = documents[i].lower()
            
            # Find which terms are present
            matched_terms = []
            boost = 0.0
            
            for term, pattern in BOOST_PATTERNS.items():
                if pattern.search(doc_lower):
                    matched_terms.append(term)
                    # Add a small boost for each matched term based on its weight
                    boost += TARGET_TERMS[term] * 0.01
            
            # Final text matching score is the TF-IDF similarity + keyword boost
            # Cap the score between 0.0 and 1.0 (approximately)
            text_score = float(similarities[i] + boost)
            final_scores.append(text_score)
            
            match_details.append({
                "tfidf_similarity": float(similarities[i]),
                "boost": boost,
                "matched_terms": matched_terms
            })
            
        return final_scores, match_details
