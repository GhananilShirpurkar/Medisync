import sys
import os

backend_dir = os.path.dirname(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from src.services.semantic_search_service import semantic_search_service

query = "i have stomach ache"
results = semantic_search_service.search(query, top_k=5, threshold=0.1)
print(f"Results for '{query}':")
for r in results:
    print(f"{r[0]}: {r[1]:.3f}")
