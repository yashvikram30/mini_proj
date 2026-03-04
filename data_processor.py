import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import os

class DataProcessor:
    def __init__(self, data_path="aqi_era5_daily_2015_2019_clean.csv"):
        self.data_path = data_path
        self.df = None
        self.rf_model = None
        self.load_and_clean_data()
        self.train_model()
        
    def load_and_clean_data(self):
        """Loads data, handles missing values, and calculates required features."""
        if not os.path.exists(self.data_path):
            print(f"Warning: Data file {self.data_path} not found.")
            return
            
        try:
            df = pd.read_csv(self.data_path)
            
            # Standardize column naming to lowercase ('AQI' -> 'aqi')
            df.columns = [col.lower() for col in df.columns]
            
            # Parse date to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                
            # Group by city and fill missing values using linear interpolation
            if 'city' in df.columns and 'date' in df.columns:
                df = df.sort_values(by=['city', 'date'])
                df = df.groupby('city', group_keys=False).apply(lambda group: group.interpolate(method='linear'))
                df = df.groupby('city', group_keys=False).apply(lambda group: group.ffill().bfill())
                
            # Feature Engineering: 
            # Calculate wind_speed = sqrt(u10² + v10²)
            if 'u10' in df.columns and 'v10' in df.columns:
                df['wind_speed'] = np.sqrt(df['u10']**2 + df['v10']**2)
                
            self.df = df
            print("Data loaded and cleaned successfully.")
        except Exception as e:
            print(f"Error loading data: {e}")
            
    def get_summary_stats(self, city: str = "all"):
        """Returns top-level statistics, optionally filtered by city."""
        if self.df is None or self.df.empty or 'aqi' not in self.df.columns:
            return {"error": "Data not available"}
            
        # Filter by city if specified
        target_df = self.df
        if city.lower() != "all" and 'city' in self.df.columns:
            target_df = self.df[self.df['city'].str.lower() == city.lower()]
            
        if target_df.empty:
            return {"error": f"No data found for city: {city}"}
            
        stats = {
            "avg_aqi": round(float(target_df['aqi'].mean()), 2),
            "median_aqi": round(float(target_df['aqi'].median()), 2),
            "max_aqi": round(float(target_df['aqi'].max()), 2),
            "severe_days": int((target_df['aqi'] > 300).sum()),
            "total_records": int(len(target_df))
        }
        return stats
        
    def get_cities(self):
        """Returns a list of unique cities in the dataset."""
        if self.df is None or self.df.empty or 'city' not in self.df.columns:
            return []
        
        # Get unique cities, drop NaN, and sort
        cities = self.df['city'].dropna().unique().tolist()
        return sorted(cities)

    def get_timeseries(self, city: str):
        """Returns daily AQI and meteorological data for a specific city, or globally if 'All'."""
        if self.df is None or self.df.empty:
            return {"error": "Data not available"}
            
        if city.lower() != "all" and 'city' in self.df.columns:
            city_df = self.df[self.df['city'].str.lower() == city.lower()]
        else:
            city_df = self.df
            
        if city_df.empty:
            return {"error": f"No data found for city: {city}"}
            
        # Group by date to get daily averages (in case 'All' is selected)
        if 'date' in city_df.columns:
            # We select numeric columns for aggregation
            numeric_cols = city_df.select_dtypes(include=[np.number]).columns.tolist()
            if 'date' not in numeric_cols:
                numeric_cols.append('date')
            
            # Aggregate to daily
            daily_df = city_df[numeric_cols].groupby('date').mean().reset_index()
            daily_df['date'] = daily_df['date'].dt.strftime('%Y-%m-%d')
            
            # Formulate response
            response = {
                "dates": daily_df['date'].tolist(),
                "aqi": daily_df['aqi'].round(2).tolist() if 'aqi' in daily_df.columns else [],
            }
            
            # Include met data if present
            if 't2m' in daily_df.columns:
                response["t2m"] = daily_df['t2m'].round(2).tolist()
            if 'wind_speed' in daily_df.columns:
                response["wind_speed"] = daily_df['wind_speed'].round(2).tolist()
                
            return response
            
        return {"error": "Date column missing"}

    def get_monthly_seasonality(self, city: str = "all"):
        """Returns average AQI per month for seasonality analysis."""
        if self.df is None or self.df.empty or 'aqi' not in self.df.columns or 'date' not in self.df.columns:
            return {"error": "Data not available"}
            
        target_df = self.df
        if city.lower() != "all" and 'city' in self.df.columns:
            target_df = self.df[self.df['city'].str.lower() == city.lower()]
            
        if target_df.empty:
            return {"error": f"No data found for city: {city}"}
            
        # Extract month and calculate mean AQI
        monthly_avg = target_df.groupby(target_df['date'].dt.month)['aqi'].mean().round(2)
        
        # Format for Chart.js
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        result = {
            "labels": [months[m-1] for m in monthly_avg.index],
            "values": monthly_avg.tolist()
        }
        return result

    def get_aqi_distribution(self, city: str = "all"):
        """Returns distribution of AQI categories."""
        if self.df is None or self.df.empty or 'aqi' not in self.df.columns:
            return {"error": "Data not available"}
            
        target_df = self.df
        if city.lower() != "all" and 'city' in self.df.columns:
            target_df = self.df[self.df['city'].str.lower() == city.lower()]
            
        if target_df.empty:
            return {"error": f"No data found for city: {city}"}
            
        bins = [0, 50, 100, 200, float('inf')]
        labels = ['Good', 'Moderate', 'Unhealthy', 'Severe']
        
        # Use pd.cut to categorize
        categories = pd.cut(target_df['aqi'], bins=bins, labels=labels, right=True)
        counts = categories.value_counts().reindex(labels).fillna(0).astype(int)
        
        return {
            "labels": counts.index.tolist(),
            "values": counts.tolist()
        }

    def get_correlation(self, city: str = "all"):
        """Returns correlations between met variables and AQI."""
        if self.df is None or self.df.empty or 'aqi' not in self.df.columns:
            return {"error": "Data not available"}
            
        target_df = self.df
        if city.lower() != "all" and 'city' in self.df.columns:
            target_df = self.df[self.df['city'].str.lower() == city.lower()]
            
        if target_df.empty:
            return {"error": f"No data found for city: {city}"}
            
        cols_of_interest = ['aqi', 't2m', 'd2m', 'wind_speed', 'sp', 'blh']
        available_cols = [c for c in cols_of_interest if c in target_df.columns]
        
        if len(available_cols) < 2:
            return {"error": "Not enough variables for correlation"}
            
        corr_matrix = target_df[available_cols].corr()
        
        # Get correlations with AQI, dropping the AQI-AQI correlation
        aqi_corr = corr_matrix['aqi'].drop('aqi').round(3)
        
        return {
            "labels": aqi_corr.index.tolist(),
            "values": aqi_corr.tolist()
        }

    def train_model(self):
        """Trains RandomForestRegressors for predicting AQI per city and globally."""
        if self.df is None or self.df.empty:
            return
            
        required_cols = ['t2m', 'd2m', 'sp', 'blh', 'wind_speed', 'aqi']
        missing = [c for c in required_cols if c not in self.df.columns]
        
        if missing:
            print(f"Skipping model training. Missing columns: {missing}")
            return
            
        ml_df = self.df[required_cols + (['city'] if 'city' in self.df.columns else [])].dropna()
        if ml_df.empty:
            print("Skipping model training. No complete data after dropping NaNs.")
            return

        self.rf_models = {}

        def _train(data):
            X = data[['t2m', 'd2m', 'sp', 'blh', 'wind_speed']]
            y = data['aqi']
            model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=1)
            model.fit(X, y)
            return model

        # Train global ('all') model
        self.rf_models['all'] = _train(ml_df)

        # Train city-specific models
        if 'city' in ml_df.columns:
            for city in ml_df['city'].unique():
                city_data = ml_df[ml_df['city'] == city]
                if not city_data.empty:
                    self.rf_models[city.lower()] = _train(city_data)

        print(f"Models trained successfully for: {list(self.rf_models.keys())}")
        
    def predict_aqi(self, t2m: float, d2m: float, sp: float, blh: float, wind_speed: float, city: str = 'all') -> float:
        """Predicts AQI based on meteorological inputs and optional city specific model."""
        if not hasattr(self, 'rf_models') or not self.rf_models:
            raise ValueError("Models are not trained.")
            
        target_city = city.lower()
        if target_city not in self.rf_models:
            # Fallback to 'all' if specific city model isn't available
            target_city = 'all'

        model = self.rf_models[target_city]

        X_new = pd.DataFrame([{
            't2m': t2m,
            'd2m': d2m,
            'sp': sp,
            'blh': blh,
            'wind_speed': wind_speed
        }])
        
        prediction = model.predict(X_new)[0]
        return round(float(prediction), 2)

# Global instance
processor = DataProcessor()
