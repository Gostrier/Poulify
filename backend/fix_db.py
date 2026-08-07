from core.database import engine
from core.models import Base
from sqlalchemy import text

with engine.connect() as connection:
    print("Dropping tables...")
    try:
        # We need to disable foreign key checks if we want to drop them easily
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        connection.execute(text("DROP TABLE IF EXISTS daily_logs;"))
        connection.execute(text("DROP TABLE IF EXISTS flocks;"))
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        connection.commit()
        print("Tables dropped.")
    except Exception as e:
        print(f"Error dropping tables: {e}")

print("Creating tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
except Exception as e:
    print(f"Error creating tables: {e}")
