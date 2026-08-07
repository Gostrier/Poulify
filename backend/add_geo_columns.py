from core.database import engine
from sqlalchemy import text

def add_columns():
    cols_to_add = [
        ("country", "VARCHAR(100)"),
        ("region", "VARCHAR(100)"),
        ("city", "VARCHAR(100)")
    ]
    
    with engine.connect() as conn:
        for col_name, col_type in cols_to_add:
            try:
                # Check if column exists
                result = conn.execute(text(f"SHOW COLUMNS FROM users LIKE '{col_name}'"))
                if not result.fetchone():
                    print(f"Adding column {col_name}...")
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"Column {col_name} added.")
                else:
                    print(f"Column {col_name} already exists.")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")

if __name__ == "__main__":
    add_columns()
