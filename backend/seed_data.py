import datetime
import random
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import DATABASE_URL
from core.models import User, Flock, DailyLog

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def seed_poultry_data():
    print("🌱 Starting data injection for POULify...")
    
    # Get all users
    users = db.query(User).all()
    if not users:
        print("❌ No users found. Please register first.")
        return

    for user in users:
        print(f"Creating flock for user: {user.email}")
        # Create a default flock
        flock = Flock(
            name="Main Flock",
            breed="Broiler",
            initial_count=1000,
            user_id=user.id
        )
        db.add(flock)
        db.commit()
        db.refresh(flock)
        
        start_date = datetime.date.today() - datetime.timedelta(days=30)
        current_weight = 45.0  # Starting weight of a chick in grams
        
        for i in range(31):
            log_date = start_date + datetime.timedelta(days=i)
            
            # Simulate natural growth and consumption
            feed = 20 + (i * 1.5) + random.uniform(-2, 2)
            water = feed * 2.1
            current_weight += 40 + random.uniform(5, 15)
            
            # Introduce a "Health Anomaly" around day 22 for AI testing
            mortality = 0
            if 20 <= i <= 23:
                mortality = random.randint(1, 3)
                current_weight -= 10 # Growth slowdown
                
            new_log = DailyLog(
                flock_id=flock.id,
                log_date=log_date.strftime("%Y-%m-%d"),
                feed_consumed_kg=round(feed, 2),
                water_consumed_liters=round(water, 2),
                avg_bird_weight_g=round(current_weight, 2),
                eggs_collected=0, 
                mortality_count=mortality
            )
            
            db.add(new_log)
        
        db.commit()
        print(f"✅ Successfully injected 30 days of data for flock {flock.id} (user {user.id})!")

if __name__ == "__main__":
    seed_poultry_data()
