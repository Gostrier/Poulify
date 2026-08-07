from core.database import engine
from sqlalchemy import text

with engine.connect() as connection:
    try:
        result = connection.execute(text("SELECT id, email FROM users"))
        for row in result:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
