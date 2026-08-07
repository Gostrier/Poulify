from core.database import engine
from sqlalchemy import text

def update_schema():
    with engine.connect() as connection:
        try:
            print("Adding 'start_date' column...")
            connection.execute(text("ALTER TABLE flocks ADD COLUMN start_date DATE AFTER user_id"))
            
            print("Adding 'is_active' column...")
            connection.execute(text("ALTER TABLE flocks ADD COLUMN is_active BOOLEAN DEFAULT TRUE AFTER start_date"))
            
            connection.commit()
            print("Successfully updated flocks table schema.")
        except Exception as e:
            print(f"Error updating schema: {e}")

if __name__ == "__main__":
    update_schema()
