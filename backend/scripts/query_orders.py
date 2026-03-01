from src.db_config import get_db_context
from src.models import Order
import json

def query_recent_orders():
    with get_db_context() as db:
        orders = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()
        result = []
        for o in orders:
            result.append({
                "order_id": o.order_id,
                "user_id": o.user_id,
                "status": o.status,
                "total_amount": o.total_amount,
                "created_at": o.created_at.isoformat() if o.created_at else None
            })
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    query_recent_orders()
