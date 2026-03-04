import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def load_data(file_path="aqi_era5_daily_2015_2019_clean.csv"):
    try:
        # Load data
        df = pd.read_csv(file_path)
        
        # Parse date to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Group by city and fill missing values using linear interpolation
        if 'city' in df.columns:
            # Sort values to ensure proper interpolation
            df = df.sort_values(by=['city', 'date'])
            df = df.groupby('city', group_keys=False).apply(lambda group: group.interpolate(method='linear'))
            
            # Forward and backward fill for remaining NaNs at edges
            df = df.groupby('city', group_keys=False).apply(lambda group: group.ffill().bfill())
        
        # Feature Engineering: 
        # Calculate wind_speed = sqrt(u10² + v10²)
        if 'u10' in df.columns and 'v10' in df.columns:
            df['wind_speed'] = np.sqrt(df['u10']**2 + df['v10']**2)
            
        # Rename t2m to Temperature (K), sp to Pressure (Pa), and blh to Boundary Layer Height (m)
        rename_mapping = {
            't2m': 'Temperature (K)',
            'sp': 'Pressure (Pa)',
            'blh': 'Boundary Layer Height (m)',
            'aqi': 'AQI', # standardizing cases if needed
            'city': 'City',
            'date': 'Date'
        }
        
        # Only rename columns that exist
        actual_mapping = {k: v for k, v in rename_mapping.items() if k in df.columns}
        df = df.rename(columns=actual_mapping)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()
