import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

@st.cache_resource
def train_model(df):
    """
    Train a RandomForestRegressor on features: Temperature (K), Dewpoint Temp (K), 
    Pressure (Pa), Boundary Layer Height (m), and wind_speed.
    Returns the trained model and feature importances.
    """
    required_features = [
        'Temperature (K)', 
        'd2m', # Assuming d2m is dewpoint temp from ERA5
        'Pressure (Pa)', 
        'Boundary Layer Height (m)', 
        'wind_speed'
    ]
    
    # Check if 'Dewpoint Temp (K)' is already renamed, otherwise use 'd2m'
    if 'Dewpoint Temp (K)' in df.columns:
        required_features[1] = 'Dewpoint Temp (K)'
    elif 'd2m' in df.columns:
        # Create renamed column on the fly for consistency
        df['Dewpoint Temp (K)'] = df['d2m']
        required_features[1] = 'Dewpoint Temp (K)'
        
    target = 'AQI'
    
    # Filter for necessary columns and drop missing target or features for training
    columns_to_keep = required_features + [target]
    
    # Ensure all required features are in the dataframe
    missing_cols = [col for col in required_features + [target] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns for training: {missing_cols}")
        
    ml_df = df[columns_to_keep].dropna()
    
    if ml_df.empty:
        raise ValueError("No complete data available for training.")
        
    X = ml_df[required_features]
    y = ml_df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    
    # Calculate performance metrics
    predictions = rf_model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    
    # Extract feature importance
    importance = rf_model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'Feature': required_features,
        'Importance': importance
    }).sort_values(by='Importance', ascending=False)
    
    metrics = {
        'MSE': mse,
        'R2 Score': r2
    }
    
    return rf_model, feature_importance_df, metrics

def get_explainability_text():
    """Returns business explainability text regarding meteorological conditions and AQI."""
    return """
### 🌪️ Why Do These Factors Influence Air Quality?

* **Boundary Layer Height (PBLH)**: This acts as a "lid" on the lower atmosphere. When the boundary layer is low (e.g., during winter or at night), pollutants like PM2.5 and PM10 are trapped close to the surface, causing AQI to spike. Conversely, a high boundary layer provides more volume for pollutants to disperse.

* **Wind Speed**: Higher wind speeds generally help disperse pollutants, cleaning the air. Stagnant air (low wind speed) leads to accumulation of emissions.

* **Temperature and Dewpoint**: Temperature inversions (when warmer air traps cooler air near the surface) often lead to severe smog events. Dewpoint relates to humidity, which can affect aerosol formation and particulate matter suspension.

* **Surface Pressure**: High-pressure systems often bring clear, calm weather with descending air currents, creating stagnant conditions that trap pollution. Low-pressure systems usually bring wind and rain, which help "wash" pollutants from the air.
"""
