from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    farm_name = Column(String(100))
    country = Column(String(100))
    region = Column(String(100))
    city = Column(String(100))

    flocks = relationship("Flock", back_populates="owner")

class Flock(Base):
    __tablename__ = "flocks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    breed = Column(String(50))
    initial_count = Column(Integer, default=100)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(Date, default=datetime.date.today)
    is_active = Column(Boolean, default=True)
    
    owner = relationship("User", back_populates="flocks")
    logs = relationship("DailyLog", back_populates="flock")
    expenses = relationship("Expense", back_populates="flock")
    revenues = relationship("Revenue", back_populates="flock")
    vaccinations = relationship("Vaccination", back_populates="flock")

class DailyLog(Base):
    __tablename__ = "daily_logs"
    id = Column(Integer, primary_key=True, index=True)
    flock_id = Column(Integer, ForeignKey("flocks.id"))
    log_date = Column(Date)
    feed_consumed_kg = Column(Float)
    water_consumed_liters = Column(Float)
    avg_bird_weight_g = Column(Float)
    mortality_count = Column(Integer)
    eggs_collected = Column(Integer, default=0)

    flock = relationship("Flock", back_populates="logs")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    flock_id = Column(Integer, ForeignKey("flocks.id"))
    category = Column(String(50)) # Feed, Medication, Chicks, Labor, Other
    amount = Column(Float)
    description = Column(String(255))
    date = Column(Date, default=datetime.date.today)

    flock = relationship("Flock", back_populates="expenses")

class Revenue(Base):
    __tablename__ = "revenues"
    id = Column(Integer, primary_key=True, index=True)
    flock_id = Column(Integer, ForeignKey("flocks.id"))
    category = Column(String(50)) # Eggs, Birds, Manure, Other
    amount = Column(Float)
    description = Column(String(255))
    date = Column(Date, default=datetime.date.today)

    flock = relationship("Flock", back_populates="revenues")

class Vaccination(Base):
    __tablename__ = "vaccinations"
    id = Column(Integer, primary_key=True, index=True)
    flock_id = Column(Integer, ForeignKey("flocks.id"))
    vaccine_name = Column(String(100))
    scheduled_date = Column(Date)
    administered_date = Column(Date, nullable=True)
    is_completed = Column(Boolean, default=False)

    flock = relationship("Flock", back_populates="vaccinations")

class FeedStock(Base):
    __tablename__ = "feed_stock"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    feed_type = Column(String(50))
    current_stock_kg = Column(Float)
    low_stock_threshold = Column(Float, default=50.0)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
