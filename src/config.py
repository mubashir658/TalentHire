# Configuration for candidate ranking system

STARTUP_FOUNDING_YEARS = {
    'Krutrim': 2023,
    'Sarvam AI': 2023,
    'Rephrase.ai': 2019,
    'Glance': 2019,
    'Observe.AI': 2017,
    'Saarthi.ai': 2017,
    'Aganitha': 2017,
    'Niramai': 2016,
    'Wysa': 2015,
    'Haptik': 2013,
    'Mad Street Den': 2013
}

PREFERRED_LOCATIONS = {'Pune', 'Noida'}
TIER1_LOCATIONS = {
    'Bangalore', 'Bengaluru', 'Hyderabad', 'Chennai', 'Mumbai', 
    'Delhi', 'Delhi NCR', 'NCR', 'Kolkata', 'Gurgaon', 'Ahmedabad'
}

# IT Consulting Companies list for the consulting-only filter
IT_CONSULTING_COMPANIES = {
    'tcs', 'tata consultancy services', 'infosys', 'wipro', 'accenture',
    'cognizant', 'capgemini', 'hcl', 'hcltech', 'tech mahindra', 'mphasis',
    'genpact'
}

# Key skill categorization based on JD
CORE_REQUIRED_SKILLS = {
    'embeddings', 'vector search', 'vector database', 'vector databases',
    'pinecone', 'milvus', 'qdrant', 'weaviate', 'faiss', 'opensearch', 
    'elasticsearch', 'semantic search', 'ndcg', 'mrr', 'map', 
    'information retrieval', 'ranking'
}

NICE_TO_HAVE_SKILLS = {
    'rag', 'retrieval-augmented generation', 'fine-tuning', 'fine-tuning llms',
    'lora', 'qlora', 'peft', 'learning to rank', 'mlops', 'python', 
    'xgboost', 'lightgbm', 'neural ranking'
}

# CV/Speech/Robotics skills that require NLP/IR presence
CV_SPEECH_ROBOTICS_SKILLS = {
    'computer vision', 'cv', 'cnn', 'yolo', 'image classification', 
    'object detection', 'speech recognition', 'tts', 'text-to-speech', 
    'robotics', 'gans', 'diffusion models'
}

# Keywords to look for NLP/IR/Search/RAG/Embedding presence
NLP_IR_SEARCH_KEYWORDS = {
    'nlp', 'natural language processing', 'embeddings', 'retrieval', 
    'search', 'rag', 'information retrieval', 'indexing', 'semantic search', 
    'bert', 'transformer', 'transformers', 'sentence-transformers', 'vector'
}

# Keywords to find in career histories that indicate actual ranking/recommendation experience
CAREER_HISTORY_KEYWORDS = [
    "recommendation system", "ranking system", "search engine", 
    "re-ranking", "a/b test", "deployed to production", 
    "production deployment", "retrieval", "vector search"
]
