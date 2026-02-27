import os
import logging
from typing import List, Dict, Any, Tuple
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# Try to import sentence_transformers, handle if not installed
try:
    from sentence_transformers import SentenceTransformer, util
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    logger.warning("⚠️  sentence-transformers not found. Semantic search will be disabled.")
    HAS_SENTENCE_TRANSFORMERS = False

class SemanticSearchService:
    """
    Service for semantic search capabilities using vector embeddings.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.enabled = HAS_SENTENCE_TRANSFORMERS
        self.model = None
        self.medicine_names = []      # List[name] for index alignment
        self.embeddings_matrix = None # Matrix of all embeddings
        
        # Cache paths
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.cache_dir = os.path.join(backend_dir, 'data', 'cache')
        self.embeddings_file = os.path.join(self.cache_dir, 'embeddings_cache.pt')
        self.names_file = os.path.join(self.cache_dir, 'names_cache.json')
        
        if self.enabled:
            logger.info(f"🧠 Loading semantic model: {model_name}...")
            try:
                self.model = SentenceTransformer(model_name)
                logger.info("✅ Semantic model loaded.")
                self._load_from_cache()
            except Exception as e:
                logger.error(f"❌ Failed to load semantic model: {e}")
                self.enabled = False

    def _load_from_cache(self):
        import torch
        import json
        if os.path.exists(self.embeddings_file) and os.path.exists(self.names_file):
            logger.info("📦 Found cached embeddings. Loading from disk...")
            try:
                self.embeddings_matrix = torch.load(self.embeddings_file)
                with open(self.names_file, 'r') as f:
                    self.medicine_names = json.load(f)
                logger.info(f"✅ Successfully loaded {len(self.medicine_names)} embeddings from cache.")
            except Exception as e:
                logger.error(f"⚠️ Failed to load embeddings from cache: {e}")
                self.embeddings_matrix = None
                self.medicine_names = []

    def index_medicines(self, medicines: List[Dict[str, Any]]):
        """
        Create embeddings for a list of medicines.
        Skips indexing if already loaded from cache.
        """
        if not self.enabled or not medicines:
            return

        if self.embeddings_matrix is not None and len(self.medicine_names) > 0:
            logger.info(f"⏭️ Skipping semantic indexing; {len(self.medicine_names)} embeddings already loaded from cache.")
            return

        logger.info(f"🧠 Indexing {len(medicines)} medicines for semantic search...")
        
        self.medicine_names = []
        texts_to_embed = []
        
        for med in medicines:
            name = med.get("name", "")
            description = med.get("description", "")
            indication = med.get("indications", med.get("indication", ""))
            category = med.get("category", "")
            
            # Create a rich text representation for embedding
            # "Paracetamol 500mg. For fever and pain relief. Analgesic. Tablet. Active: Paracetamol."
            dosage_form = med.get("dosage_form") or ""
            active_ingredients = med.get("active_ingredients") or ""
            
            text = f"{name} {active_ingredients}. {description}. {indication}. {category}. {dosage_form}"
            
            self.medicine_names.append(name)
            texts_to_embed.append(text)
            
        if texts_to_embed:
            try:
                # Generate embeddings
                embeddings = self.model.encode(texts_to_embed, convert_to_tensor=True)
                self.embeddings_matrix = embeddings
                logger.info(f"✅ Indexed {len(medicines)} medicines.")
                
                # Try saving to cache to prevent this next time
                import torch
                import json
                os.makedirs(self.cache_dir, exist_ok=True)
                torch.save(self.embeddings_matrix, self.embeddings_file)
                with open(self.names_file, 'w') as f:
                    json.dump(self.medicine_names, f)
            except Exception as e:
                logger.error(f"❌ Failed to index medicines: {e}")

    def search(self, query: str, top_k: int = 3, threshold: float = 0.65) -> List[Tuple[str, float]]:
        """
        Search for medicines similar to the query.
        Returns list of (medicine_name, score).
        """
        if not self.enabled or self.embeddings_matrix is None:
            return []

        try:
            # Encode query
            query_embedding = self.model.encode(query, convert_to_tensor=True)
            
            # Compute cosine similarity
            # util.cos_sim returns a tensor of shape (1, num_medicines)
            cosine_scores = util.cos_sim(query_embedding, self.embeddings_matrix)[0]
            
            # Get top k results
            # torch.topk returns (values, indices)
            top_results = torch_topk_safe(cosine_scores, k=min(top_k, len(self.medicine_names)))
            
            results = []
            for score, idx in zip(top_results[0], top_results[1]):
                score_float = float(score)
                if score_float >= threshold:
                    results.append((self.medicine_names[int(idx)], score_float))
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Semantic search error: {e}")
            return []

# Helper to handle tensor vs numpy if needed, though sentence-transformers usually returns torch tensors
def torch_topk_safe(scores, k):
    import torch
    return torch.topk(scores, k=k)

# Global instance
semantic_search_service = SemanticSearchService()
