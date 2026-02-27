"""
API ROUTES
==========
FastAPI route definitions.
"""

from src.routes.prescriptions import router as prescriptions_router
from src.routes.orders import router as orders_router
from src.routes.inventory import router as inventory_router

__all__ = [
    "prescriptions_router",
    "orders_router",
    "inventory_router"
]
