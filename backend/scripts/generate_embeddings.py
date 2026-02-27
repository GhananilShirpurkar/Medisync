import os
import sqlite3
import json
import logging
import torch
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = 'all-MiniLM-L6-v2'
BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BACKEND_DIR, 'hackfusion.db')
CACHE_DIR = os.path.join(BACKEND_DIR, 'data', 'cache')
EMBEDDINGS_FILE = os.path.join(CACHE_DIR, 'embeddings_cache.pt')
NAMES_FILE = os.path.join(CACHE_DIR, 'names_cache.json')

def generate_embeddings():
    """Reads all medicines from DB using raw sqlite and caches their embeddings."""
    logger.info(f"Loading {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    logger.info(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name, description, indications, category, dosage_form, active_ingredients FROM medicines")
        medicines = cursor.fetchall()
        
        logger.info(f"Found {len(medicines)} medicines. Generating embeddings...")
        
        medicine_names = []
        texts_to_embed = []
        
        for med in medicines:
            name = med['name'] or ""
            description = med['description'] or ""
            indication = med['indications'] or ""
            category = med['category'] or ""
            dosage_form = med['dosage_form'] or ""
            active_ingredients = med['active_ingredients'] or ""
            
            text = f"{name} {active_ingredients}. {description}. {indication}. {category}. {dosage_form}"
            medicine_names.append(name)
            texts_to_embed.append(text)
            
        if texts_to_embed:
            # Generate and save
            embeddings = model.encode(texts_to_embed, convert_to_tensor=True)
            
            os.makedirs(CACHE_DIR, exist_ok=True)
            
            torch.save(embeddings, EMBEDDINGS_FILE)
            with open(NAMES_FILE, 'w') as f:
                json.dump(medicine_names, f)
                
            logger.info(f"✅ Successfully cached {len(medicines)} embeddings to {CACHE_DIR}")
        else:
            logger.warning("No medicines found to embed.")
            
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    generate_embeddings()
