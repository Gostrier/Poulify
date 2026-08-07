from core.database import engine
from sqlalchemy import text

with engine.connect() as connection:
    try:
        print("Tables in database:")
        result = connection.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        for table in tables:
            print(f"\nSchema for '{table}':")
            result = connection.execute(text(f"DESCRIBE {table}"))
            for row in result:
                print(row)
    except Exception as e:
        print(f"Error: {e}")
