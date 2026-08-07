import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import pickle
import os

def train_basic_model():
    # Synthetic data for training if no real data exists
    # age (days), feed_consumed (kg cumulative) -> weight (g)
    data = {
        'age': [1, 7, 14, 21, 28, 35, 42],
        'feed': [0.02, 0.15, 0.5, 1.2, 2.2, 3.5, 5.0],
        'weight': [40, 180, 450, 900, 1500, 2100, 2800]
    }
    
    df = pd.DataFrame(data)
    X = df[['age', 'feed']]
    y = df['weight']
    
    model = LinearRegression()
    model.fit(X, y)
    
    model_path = os.path.join(os.path.dirname(__file__), "ai_models", "weight_model.pkl")
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Model trained and saved to {model_path}")

if __name__ == "__main__":
    train_basic_model()
