import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def calculate_stats(df):
    """Calculate Mean, Median, Std Dev, and 'Severe Days' (AQI > 300)."""
    if df.empty or 'AQI' not in df.columns:
        return {}
    
    stats = {
        'Mean AQI': df['AQI'].mean(),
        'Median AQI': df['AQI'].median(),
        'Std Dev AQI': df['AQI'].std(),
        'Severe Days': (df['AQI'] > 300).sum()
    }
    return stats

def get_anomalies(df):
    """Identify records in the >95th percentile of AQI."""
    if df.empty or 'AQI' not in df.columns:
        return pd.DataFrame()
    
    threshold = df['AQI'].quantile(0.95)
    anomalies = df[df['AQI'] > threshold]
    return anomalies

def plot_correlation_heatmap(df):
    """Generate a correlation heatmap using Plotly."""
    if df.empty:
        return None
        
    num_df = df.select_dtypes(include=['float64', 'int64'])
    if num_df.empty:
        return None
        
    corr = num_df.corr()
    
    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="Tealgrn",
        title="Feature Correlation Heatmap"
    )
    
    # Update layout for modern dark theme
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff")
    )
    
    return fig

def plot_monthly_heatmap(df):
    """Generate a Monthly Heatmap of AQI averages."""
    if df.empty or 'Date' not in df.columns or 'AQI' not in df.columns:
        return None
        
    df_copy = df.copy()
    df_copy['Year'] = df_copy['Date'].dt.year
    df_copy['Month'] = df_copy['Date'].dt.month
    
    monthly_avg = df_copy.groupby(['Year', 'Month'])['AQI'].mean().reset_index()
    pivot_table = monthly_avg.pivot(index='Year', columns='Month', values='AQI')
    
    fig = px.imshow(
        pivot_table,
        labels=dict(x="Month", y="Year", color="Average AQI"),
        x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        color_continuous_scale="OrRd",
        title="Monthly Average AQI Heatmap"
    )
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff")
    )
    
    return fig
