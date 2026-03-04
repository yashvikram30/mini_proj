import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_data
from analytics import calculate_stats, get_anomalies, plot_correlation_heatmap, plot_monthly_heatmap
from model import train_model, get_explainability_text
import os

# --- PAGE SETUP ---
st.set_page_config(
    page_title="AQI & Meteorology Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INJECT CUSTOM CSS ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("assets/style.css")

# --- LOAD DATA ---
@st.cache_data
def get_cached_data():
    df = load_data("aqi_era5_daily_2015_2019_clean.csv")
    return df

raw_df = get_cached_data()

if raw_df.empty:
    st.warning("⚠️ Data file not found or could not be loaded. Please ensure 'aqi_era5_daily_2015_2019_clean.csv' is in the current directory.")
    st.stop()

# Ensure session state initialization
if "selected_city" not in st.session_state:
    st.session_state.selected_city = "All"

# --- SIDEBAR NAVIGATION & FILTERS ---
st.sidebar.title("🌍 AQI Navigator")

# Navigation
sections = [
    "Executive Overview", 
    "Pollutant Explorer", 
    "Statistical Deep-Dive", 
    "Anomaly & Heatmaps", 
    "Predictive AI"
]
selected_section = st.sidebar.radio("Go to:", sections)

st.sidebar.divider()
st.sidebar.header("Filter Data")

# City Selector
cities = ["All"] + list(raw_df['City'].dropna().unique())
selected_city = st.sidebar.selectbox("Select City", cities, key="city_selector")

# Determine city data
if st.session_state.city_selector != "All":
    city_df = raw_df[raw_df['City'] == st.session_state.city_selector]
else:
    city_df = raw_df

# Date Range Slider
min_date = city_df['Date'].min().date() if pd.notnull(city_df['Date'].min()) else None
max_date = city_df['Date'].max().date() if pd.notnull(city_df['Date'].max()) else None

if min_date and max_date:
    date_range = st.sidebar.slider(
        "Select Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date)
    )
    
    # Apply date filter
    start_date, end_date = date_range
    mask = (city_df['Date'].dt.date >= start_date) & (city_df['Date'].dt.date <= end_date)
    filtered_df = city_df.loc[mask]
else:
    filtered_df = city_df

st.sidebar.caption(f"Showing {len(filtered_df)} records")

# --- MAIN CONTENT AREA ---

st.title("Air Quality & Meteorology Intelligence")

if selected_section == "Executive Overview":
    st.header("Executive Overview")
    st.markdown("Top-level KPIs and time series trends.")
    
    stats = calculate_stats(filtered_df)
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mean AQI", f"{stats['Mean AQI']:.1f}")
        col2.metric("Median AQI", f"{stats['Median AQI']:.1f}")
        col3.metric("Std Dev AQI", f"{stats['Std Dev AQI']:.1f}")
        col4.metric("Severe Days (>300)", stats['Severe Days'])
        
        st.subheader("AQI Timeline")
        if selected_city == "All":
            timeline_df = filtered_df.groupby('Date')['AQI'].mean().reset_index()
            fig = px.line(timeline_df, x='Date', y='AQI', title="Average AQI Over Time (All Cities)")
        else:
            fig = px.line(filtered_df, x='Date', y='AQI', title=f"AQI Over Time in {selected_city}")
            
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for the current selection.")

elif selected_section == "Pollutant Explorer":
    st.header("Pollutant Explorer")
    st.markdown("Explore individual meteorological and pollutant factors.")
    
    available_cols = filtered_df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    if 'AQI' in available_cols: available_cols.remove('AQI')
    
    if available_cols:
        selected_var = st.selectbox("Select Feature to Explore", available_cols)
        
        if selected_city == "All":
            var_df = filtered_df.groupby('Date')[selected_var].mean().reset_index()
            fig = px.line(var_df, x='Date', y=selected_var, title=f"Average {selected_var} Over Time")
        else:
            fig = px.line(filtered_df, x='Date', y=selected_var, title=f"{selected_var} in {selected_city}")
            
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No numeric columns available to explore.")

elif selected_section == "Statistical Deep-Dive":
    st.header("Statistical Deep-Dive")
    st.markdown("Distribution and spread of the Air Quality Index.")
    
    if not filtered_df.empty and 'AQI' in filtered_df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("AQI Distribution")
            fig_hist = px.histogram(filtered_df, x='AQI', nbins=50, title="Histogram of AQI")
            fig_hist.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"))
            st.plotly_chart(fig_hist, use_container_width=True)
            
        with col2:
            st.subheader("AQI Boxplot")
            if selected_city == "All":
                fig_box = px.box(filtered_df, x='City', y='AQI', title="AQI Spread per City")
            else:
                fig_box = px.box(filtered_df, y='AQI', title=f"AQI Spread in {selected_city}")
            fig_box.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"))
            st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("No AQI data available.")

elif selected_section == "Anomaly & Heatmaps":
    st.header("Anomaly Detection & Heatmaps")
    
    st.subheader(">95th Percentile Anomalies")
    anomalies = get_anomalies(filtered_df)
    if not anomalies.empty:
        st.dataframe(anomalies.sort_values(by='AQI', ascending=False).head(100), use_container_width=True)
        st.caption(f"Showing up to 100 top anomalies out of {len(anomalies)} total.")
    else:
        st.info("No anomalies found in current view.")
        
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Correlation Matrix")
        fig_corr = plot_correlation_heatmap(filtered_df)
        if fig_corr:
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Could not render correlation heatmap.")
            
    with col2:
        st.subheader("Seasonality (Monthly Avg)")
        fig_monthly = plot_monthly_heatmap(filtered_df)
        if fig_monthly:
            st.plotly_chart(fig_monthly, use_container_width=True)
        else:
            st.info("Could not render monthly heatmap.")

elif selected_section == "Predictive AI":
    st.header("Predictive AI Engine")
    st.markdown("Machine Learning analysis predicting AQI based on meteorological features.")
    
    try:
        model, importance_df, metrics_dict = train_model(raw_df) # Train on raw_df
        
        st.success(f"Model trained successfully! (R² Score: {metrics_dict['R2 Score']:.2f}, MSE: {metrics_dict['MSE']:.2f})")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Feature Importance")
            fig = px.bar(
                importance_df, 
                x='Importance', 
                y='Feature', 
                orientation='h', 
                title="What drives AQI?"
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"))
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown(get_explainability_text())
            
    except Exception as e:
        st.error(f"Could not train predictive model: {e}")
        st.info("Please ensure weather features ('Temperature (K)', 'Dewpoint Temp (K)' or 'd2m', 'Pressure (Pa)', 'Boundary Layer Height (m)', 'wind_speed') are present in the dataset.")
