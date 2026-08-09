import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import pickle
import os
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

def process_poultry_data(logs, expenses=None, revenues=None, vaccinations=None):
    """
    Transforms raw DB logs into AI insights for the dashboard.
    """
    if not logs:
        return {
            "status": "No Data", 
            "fcr": 0, 
            "alerts": [], 
            "avg_weight": 0, 
            "total_mortality": 0,
            "lay_percent": 0,
            "survival_rate": 100,
            "current_birds": 0,
            "profit": 0,
            "roi": 0
        }

    # 1. Convert SQLAlchemy objects to Pandas DataFrame
    data_list = []
    for l in logs:
        data_list.append({
            "date": l.log_date,
            "feed": l.feed_consumed_kg or 0,
            "weight": l.avg_bird_weight_g or 0,
            "mortality": l.mortality_count or 0,
            "water": l.water_consumed_liters or 0,
            "eggs": l.eggs_collected or 0
        })
    
    df = pd.DataFrame(data_list)
    df = df.sort_values('date')

    alerts = []
    
    # 2. Mortality & Survival Calculations
    total_mortality = int(df['mortality'].sum())
    
    unique_flocks = {}
    for l in logs:
        if hasattr(l, 'flock') and l.flock:
            if l.flock_id not in unique_flocks:
                unique_flocks[l.flock_id] = getattr(l.flock, 'initial_count', 100)
    
    initial_birds = sum(unique_flocks.values()) if unique_flocks else 100
    current_birds = max(0, initial_birds - total_mortality)
    survival_rate = round((current_birds / initial_birds) * 100, 1) if initial_birds > 0 else 0

    # 3. Egg Production
    latest_eggs = df['eggs'].iloc[-1] if not df.empty else 0
    lay_percent = round((latest_eggs / current_birds) * 100, 1) if current_birds > 0 else 0

    # 4. FCR
    total_feed = df['feed'].sum()
    current_weight = df['weight'].iloc[-1] if not df.empty else 0
    initial_weight = df['weight'].iloc[0] if len(df) > 1 else 40 
    weight_gain = current_weight - initial_weight
    current_fcr = round(total_feed / (weight_gain / 1000), 2) if weight_gain > 0 else 0

    # 5. Financials
    total_expenses = sum([e.amount for e in expenses]) if expenses else 0
    total_revenue = sum([r.amount for r in revenues]) if revenues else 0
    profit = total_revenue - total_expenses
    roi = round((profit / total_expenses) * 100, 1) if total_expenses > 0 else 0

    # 6. Vaccination Alerts
    if vaccinations:
        today = date.today()
        for v in vaccinations:
            if not v.is_completed and v.scheduled_date <= today:
                alerts.append(f"💉 Vaccination Due: {v.vaccine_name} for {v.flock.name}")

    # 7. AI Anomaly Detection
    if len(df) > 5:
        features = df[['feed', 'mortality', 'water', 'eggs']].fillna(0)
        model = IsolationForest(contamination=0.05, random_state=42)
        df['anomaly_score'] = model.fit_predict(features)
        if df['anomaly_score'].iloc[-1] == -1:
            alerts.append("⚠️ Unusual behavior detected: Feed/Water intake doesn't match production patterns.")

    # 8. Growth Prediction
    predicted_weight = None
    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai_models", "weight_model.pkl")
    if os.path.exists(model_path):
        try:
            with open(model_path, 'rb') as f:
                weight_model = pickle.load(f)
                age_days = len(df) # Rough estimate
                predicted_weight = weight_model.predict([[age_days + 7, total_feed / age_days * (age_days + 7)]])[0]
        except Exception as e:
            logger.warning("Weight model could not be loaded/predicted: %s", e)

    return {
        "fcr": current_fcr,
        "fcr_status": "Excellent" if (1.4 <= current_fcr <= 1.7) else "Monitor",
        "alerts": alerts,
        "avg_weight": round(df['weight'].mean(), 2) if not df.empty else 0,
        "total_mortality": total_mortality,
        "current_birds": current_birds,
        "survival_rate": survival_rate,
        "lay_percent": lay_percent,
        "profit": profit,
        "roi": roi,
        "total_expenses": total_expenses,
        "total_revenue": total_revenue,
        "predicted_weight_7d": round(predicted_weight, 2) if predicted_weight else None
    }
