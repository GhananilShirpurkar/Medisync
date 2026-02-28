import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.db_config import engine

def add_pending_cart_column():
    print("Adding pending_cart column to conversation_sessions...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE conversation_sessions ADD COLUMN pending_cart JSON"))
            conn.commit()
            print("✅ Added pending_cart column successfully.")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✅ Column pending_cart already exists.")
            else:
                print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    add_pending_cart_column()
