from src.db_config import get_db_context
from src.models import Medicine
import json

def list_in_stock_medicines():
    with get_db_context() as db:
        meds = db.query(Medicine).filter(Medicine.stock > 0).limit(10).all()
        result = []
        for m in meds:
            result.append({
                "name": m.name,
                "stock": m.stock,
                "price": m.price
            })
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    list_in_stock_medicines()
