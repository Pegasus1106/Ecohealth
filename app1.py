import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import weather_api as weather
import openai_helper as ai
import data_utils as utils
import visualization as viz
import database as db
import newsletter
from utils.data_processor import DataProcessor
from utils.visualization import VisualizationGenerator
from utils.deepseek_helper import DeepSeekAnalyzer
from utils.advanced_analytics import AdvancedAnalytics
import json
import base64
from PIL import Image
import os
import folium
from streamlit_folium import folium_static
from model_page import model_page


# Page Configuration
st.set_page_config(
    page_title="Ecohealth Insights",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
    <style>
    /* Navigation bar styling */
    .navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background-color: #e8ffec;
        color: #000000;
        margin: -60px -60px 0px -60px;
        border-radius: 8px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        transition: background-color 0.3s ease;
    }

    .navbar:hover {
        background-color: #e8ffec;
    }

    .brand {
        font-size: 24px;
        color: #000000 !important;
        text-decoration: none !important;
        font-weight: bold;
    }

    .nav-links {
        display: flex;
        gap: 2rem;
    }

    .nav-link {
        color: #000000 !important;
        text-decoration: none !important;
        font-size: 16px;
        padding: 5px 10px;
        border-radius: 5px;
        transition: color 0.3s ease, background-color 0.3s ease;
    }

    .nav-link:hover {
        color: #166534 !important;
        background-color: #61ff73;
    }

    
""", unsafe_allow_html=True)



# Create SVG images - storing inline for reliability
weather_svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 400">
  <!-- Background -->
  <rect x="0" y="0" width="500" height="400" fill="#f5f7f9" rx="15" ry="15" />
  
  <!-- City Skyline -->
  <rect x="80" y="200" width="30" height="100" fill="#94a3b8" />
  <rect x="120" y="150" width="40" height="150" fill="#64748b" />
  <rect x="170" y="170" width="35" height="130" fill="#7f8ea3" />
  <rect x="215" y="120" width="50" height="180" fill="#475569" />
  <rect x="275" y="180" width="40" height="120" fill="#64748b" />
  <rect x="325" y="150" width="30" height="150" fill="#94a3b8" />
  <rect x="365" y="170" width="45" height="130" fill="#475569" />
  
  <!-- Data Circle -->
  <circle cx="230" cy="180" r="90" fill="#2563eb" fill-opacity="0.9" />
  <circle cx="230" cy="180" r="85" fill="#3b82f6" fill-opacity="0.8" />
  <circle cx="230" cy="180" r="80" fill="#60a5fa" fill-opacity="0.7" />
  
  <!-- Temperature -->
  <text x="230" y="155" font-family="Arial" font-size="46" fill="white" text-anchor="middle" font-weight="bold">25°C</text>
  <text x="230" y="185" font-family="Arial" font-size="16" fill="white" text-anchor="middle">Humidity</text>
  <text x="230" y="215" font-family="Arial" font-size="35" fill="white" text-anchor="middle">45%</text>
  <text x="230" y="250" font-family="Arial" font-size="22" fill="white" text-anchor="middle">GOOD</text>
  
  <!-- Control Icons -->
  <circle cx="135" cy="300" r="18" fill="#3b82f6" />
  <circle cx="185" cy="300" r="18" fill="#3b82f6" />
  <circle cx="235" cy="300" r="18" fill="#3b82f6" />
  <circle cx="285" cy="300" r="18" fill="#3b82f6" />
  <circle cx="335" cy="300" r="18" fill="#3b82f6" />
  
  <!-- Icon symbols -->
  <text x="135" y="306" font-family="Arial" font-size="16" fill="white" text-anchor="middle">☀️</text>
  <text x="185" y="306" font-family="Arial" font-size="16" fill="white" text-anchor="middle">🌡️</text>
  <text x="235" y="306" font-family="Arial" font-size="16" fill="white" text-anchor="middle">💧</text>
  <text x="285" y="306" font-family="Arial" font-size="16" fill="white" text-anchor="middle">🌈</text>
  <text x="335" y="306" font-family="Arial" font-size="16" fill="white" text-anchor="middle">🔍</text>
</svg>
"""

aqi_svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 400">
  <!-- Main Background -->
  <rect x="0" y="0" width="500" height="400" fill="#f5f7f9" rx="15" ry="15" />
  
  <!-- Title -->
  <text x="250" y="40" font-family="Arial" font-size="24" fill="#1e293b" text-anchor="middle" font-weight="bold">AQI</text>
  <text x="250" y="65" font-family="Arial" font-size="18" fill="#475569" text-anchor="middle">AIR QUALITY INDEX</text>
  
  <!-- AQI Scale -->
  <rect x="100" y="85" width="60" height="160" fill="#4ade80" rx="5" ry="5" />
  <rect x="170" y="85" width="60" height="160" fill="#22c55e" rx="5" ry="5" />
  <rect x="240" y="85" width="60" height="160" fill="#facc15" rx="5" ry="5" />
  <rect x="310" y="85" width="60" height="160" fill="#f97316" rx="5" ry="5" />
  <rect x="380" y="85" width="60" height="160" fill="#ef4444" rx="5" ry="5" />
  
  <!-- AQI Values -->
  <circle cx="130" cy="130" r="25" fill="#fff" stroke="#4ade80" stroke-width="4" />
  <text x="130" y="135" font-family="Arial" font-size="14" fill="#1e293b" text-anchor="middle" font-weight="bold">50</text>
  <text x="130" y="155" font-family="Arial" font-size="12" fill="#fff" text-anchor="middle">GOOD</text>
  
  <circle cx="200" cy="130" r="25" fill="#fff" stroke="#22c55e" stroke-width="4" />
  <text x="200" y="135" font-family="Arial" font-size="14" fill="#1e293b" text-anchor="middle" font-weight="bold">50</text>
  <text x="200" y="155" font-family="Arial" font-size="12" fill="#fff" text-anchor="middle">GOOD</text>
  
  <circle cx="270" cy="130" r="25" fill="#fff" stroke="#facc15" stroke-width="4" />
  <text x="270" y="135" font-family="Arial" font-size="14" fill="#1e293b" text-anchor="middle" font-weight="bold">100</text>
  <text x="270" y="155" font-family="Arial" font-size="12" fill="#fff" text-anchor="middle">MODERATE</text>
  
  <circle cx="340" cy="130" r="25" fill="#fff" stroke="#f97316" stroke-width="4" />
  <text x="340" y="135" font-family="Arial" font-size="14" fill="#1e293b" text-anchor="middle" font-weight="bold">150</text>
  <text x="340" y="155" font-family="Arial" font-size="12" fill="#fff" text-anchor="middle">UNHEALTHY</text>
  
  <circle cx="410" cy="130" r="25" fill="#fff" stroke="#ef4444" stroke-width="4" />
  <text x="410" y="135" font-family="Arial" font-size="14" fill="#1e293b" text-anchor="middle" font-weight="bold">150+</text>
  <text x="410" y="155" font-family="Arial" font-size="12" fill="#fff" text-anchor="middle">HAZARDOUS</text>
  
  <!-- Range Labels -->
  <text x="130" y="260" font-family="Arial" font-size="10" fill="#1e293b" text-anchor="middle">0-50</text>
  <text x="130" y="275" font-family="Arial" font-size="10" fill="#1e293b" text-anchor="middle">GOOD</text>
  
  <text x="200" y="260" font-family="Arial" font-size="10" fill="#1e293b" text-anchor="middle">51-100</text>
  <text x="200" y="275" font-family="Arial" font-size="10" fill="#1e293b" text-anchor="middle">MODERATE</text>
  
  <text x="270" y="260" font-family="Arial" font-size="10" fill="#1e293b" text-anchor="middle">101-150</text>
  <text x="270" y="275" font-family="Arial" font-size="10" fill="#1e293b" text-anchor="middle">UNHEALTHY</text>
  
  <text x="340" y="260" font-family="Arial" font-size="10" fill="#1e293b" text-anchor="middle">151-200</text>
  <text x="340" y="275" font-family="Arial" font-size="10" fill="#1e293b" text-anchor="middle">VERY UNHEALTHY</text>
  
  <text x="410" y="260" font-family="Arial" font-size="10" fill="#1e293b" text-anchor="middle">201+</text>
  <text x="410" y="275" font-family="Arial" font-size="10" fill="#1e293b" text-anchor="middle">HAZARDOUS</text>
  
  <!-- Icons -->
  <circle cx="130" cy="320" r="15" fill="#4ade80" />
  <text x="130" y="325" font-family="Arial" font-size="12" fill="#fff" text-anchor="middle">😀</text>
  
  <circle cx="200" cy="320" r="15" fill="#22c55e" />
  <text x="200" y="325" font-family="Arial" font-size="12" fill="#fff" text-anchor="middle">🙂</text>
  
  <circle cx="270" cy="320" r="15" fill="#facc15" />
  <text x="270" y="325" font-family="Arial" font-size="12" fill="#fff" text-anchor="middle">😷</text>
  
  <circle cx="340" cy="320" r="15" fill="#f97316" />
  <text x="340" y="325" font-family="Arial" font-size="12" fill="#fff" text-anchor="middle">🏭</text>
  
  <circle cx="410" cy="320" r="15" fill="#ef4444" />
  <text x="410" y="325" font-family="Arial" font-size="12" fill="#fff" text-anchor="middle">⚠️</text>
  
  <!-- Bottom Label -->
  <text x="270" y="370" font-family="Arial" font-size="14" fill="#1e293b" text-anchor="middle" font-weight="bold">Health Recommendations</text>
</svg>
"""

health_svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 400">
  <!-- Background -->
  <rect x="0" y="0" width="500" height="400" fill="#f5f7f9" rx="15" ry="15" />
  
  <!-- Weather Zones -->
  <rect x="50" y="50" width="180" height="100" fill="#e0f2fe" rx="10" ry="10" />
  <rect x="270" y="50" width="180" height="100" fill="#dbeafe" rx="10" ry="10" />
  
  <!-- Hot Weather Section -->
  <text x="140" y="80" font-family="Arial" font-size="16" fill="#0369a1" text-anchor="middle" font-weight="bold">HOT WEATHER</text>
  
  <!-- Icons for Hot Weather -->
  <circle cx="90" y="110" r="20" fill="#f97316" />
  <text x="90" y="116" font-family="Arial" font-size="14" fill="white" text-anchor="middle">☀️</text>
  
  <circle cx="140" y="110" r="20" fill="#f97316" />
  <text x="140" y="116" font-family="Arial" font-size="14" fill="#fff" text-anchor="middle">⚠️</text>
  
  <circle cx="190" y="110" r="20" fill="#f97316" />
  <text x="190" y="116" font-family="Arial" font-size="14" fill="#fff" text-anchor="middle">💦</text>
  
  <!-- Cold Weather Section -->
  <text x="360" y="80" font-family="Arial" font-size="16" fill="#0369a1" text-anchor="middle" font-weight="bold">COLD WEATHER</text>
  
  <!-- Icons for Cold Weather -->
  <circle cx="310" y="110" r="20" fill="#60a5fa" />
  <text x="310" y="116" font-family="Arial" font-size="14" fill="#fff" text-anchor="middle">❄️</text>
  
  <circle cx="360" y="110" r="20" fill="#60a5fa" />
  <text x="360" y="116" font-family="Arial" font-size="14" fill="#fff" text-anchor="middle">☃️</text>
  
  <circle cx="410" y="110" r="20" fill="#60a5fa" />
  <text x="410" y="116" font-family="Arial" font-size="14" fill="#fff" text-anchor="middle">🧣</text>
  
  <!-- Health Recommendations -->
  <rect x="50" y="170" width="180" height="60" fill="#dbeafe" rx="8" ry="8" />
  <text x="140" y="205" font-family="Arial" font-size="12" fill="#1e40af" text-anchor="middle">STAY HYDRATED</text>
  
  <rect x="270" y="170" width="180" height="60" fill="#dbeafe" rx="8" ry="8" />
  <text x="360" y="205" font-family="Arial" font-size="12" fill="#1e40af" text-anchor="middle">STAY WARM</text>
  
  <rect x="50" y="240" width="180" height="60" fill="#dbeafe" rx="8" ry="8" />
  <text x="140" y="275" font-family="Arial" font-size="12" fill="#1e40af" text-anchor="middle">WEAR SUNSCREEN</text>
  
  <rect x="270" y="240" width="180" height="60" fill="#dbeafe" rx="8" ry="8" />
  <text x="360" y="275" font-family="Arial" font-size="12" fill="#1e40af" text-anchor="middle">LAYER CLOTHING</text>
  
  <!-- Air Quality Recommendations -->
  <rect x="50" y="310" width="80" height="60" fill="#d1fae5" rx="8" ry="8" />
  <text x="90" y="345" font-family="Arial" font-size="10" fill="#065f46" text-anchor="middle">STAY INDOORS</text>
  
  <rect x="140" y="310" width="80" height="60" fill="#d1fae5" rx="8" ry="8" />
  <text x="180" y="345" font-family="Arial" font-size="10" fill="#065f46" text-anchor="middle">WEAR MASK</text>
  
  <rect x="230" y="310" width="80" height="60" fill="#d1fae5" rx="8" ry="8" />
  <text x="270" y="345" font-family="Arial" font-size="10" fill="#065f46" text-anchor="middle">AVOID OUTDOORS</text>
  
  <rect x="320" y="310" width="80" height="60" fill="#d1fae5" rx="8" ry="8" />
  <text x="360" y="345" font-family="Arial" font-size="10" fill="#065f46" text-anchor="middle">USE INHALER</text>
  
  <rect x="410" y="310" width="80" height="60" fill="#d1fae5" rx="8" ry="8" />
  <text x="450" y="345" font-family="Arial" font-size="10" fill="#065f46" text-anchor="middle">STAY UPDATED</text>
</svg>
"""
# Navigation bar
def navigation():
    st.markdown("""
        <div class="navbar">
            <a href="#" class="brand">🌿Ecohealth Insights</a>
            <div class="nav-links">
                <a href="/?page=home" class="nav-link" target="_self">Home</a>
                <a href="/?page=about" class="nav-link" target="_self">About</a>
                <a href="/?page=weather" class="nav-link" target="_self">Weather</a>
                <a href="/?page=visualizations" class="nav-link" target="_self">Visualizations</a>
                <a href="/?page=model" class="nav-link" target="_self">Model</a>
            </div>
        </div>
    """, unsafe_allow_html=True)



def home_page():
    import base64
    from datetime import datetime
    import streamlit as st

    # Function to render SVG
    def render_svg(svg_content, width=None):
        if width:
            svg_content = svg_content.replace('<svg ', f'<svg width="{width}" ')
        b64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        html = f'''
            <img src="data:image/svg+xml;base64,{b64}" style="max-width: 100%; height: auto;">
        '''
        return html

    # Card styling
    def add_card_styling():
        st.markdown("""
        <style>
        .card {
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }
        .card-header {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 15px;
            color: #1e3a8a;
        }
        .card-description {
            font-size: 1.0rem;
            color: #4b5563;
            margin-bottom: 15px;
        }
        </style>
        """, unsafe_allow_html=True)

    # Call card styling
    add_card_styling()

    # Header Section
    st.markdown("<h1 style='text-align: center; color: #166534;'>Welcome to Ecohealth Insights</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4b5563; margin-bottom: 50px;'>Get personalized health recommendations based on your local environmental conditions</h3>", unsafe_allow_html=True)

    # Static location (replace with dynamic input if needed)
    location = "Your Location"

    # Main Features Section - Cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-header">Real-time Weather</div>
            <div class="card-description">Get accurate temperature and weather conditions for your location</div>
        """, unsafe_allow_html=True)

        st.markdown(render_svg(weather_svg), unsafe_allow_html=True)

        if location:
            st.markdown(f"<div style='text-align: center; padding: 10px;'>Current conditions for <b>{location}</b></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-header">Air Quality Index</div>
            <div class="card-description">Monitor real-time air quality data and pollution levels</div>
        """, unsafe_allow_html=True)

        st.markdown(render_svg(aqi_svg), unsafe_allow_html=True)

        if location:
            st.markdown(f"<div style='text-align: center; padding: 10px;'>Air quality data for <b>{location}</b></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-header">Health Recommendations</div>
            <div class="card-description">Get AI-powered health insights based on environmental conditions</div>
        """, unsafe_allow_html=True)

        st.markdown(render_svg(health_svg), unsafe_allow_html=True)

        if location:
            st.markdown(f"<div style='text-align: center; padding: 10px;'>Health recommendations for <b>{location}</b></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Additional Information Section
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.markdown("""
        <div class="card">
            <div class="card-header">How It Works</div>
            <p>EcoHealth Insights combines real-time environmental data with advanced algorithms to provide you with personalized health recommendations.</p>
            <p>Our system analyzes:</p>
            <ul>
                <li>Current weather conditions</li>
                <li>Local air quality measurements</li>
                <li>Seasonal health trends</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with info_col2:
        st.markdown("""
        <div class="card">
            <div class="card-header">Why EcoHealth Insights?</div>
            <ul>
                <li><b>Personalized</b>: Recommendations tailored to your specific location</li>
                <li><b>Real-time</b>: Always up-to-date with the latest environmental data</li>
                <li><b>Science-backed</b>: Insights based on verified health research</li>
                <li><b>User-friendly</b>: Clear, actionable recommendations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("<div style='margin-top: 30px; text-align: center; color: #6b7280;'>© 2025 EcoHealth Insights | Data updated: " + 
                datetime.now().strftime("%Y-%m-%d %H:%M") + "</div>", unsafe_allow_html=True)

    

def about_page():
    

    st.title("🌍 About Ecohealth Insights")
    st.markdown("---")

    # Introduction
    st.markdown("""
    Welcome to Ecohealth Insights a comprehensive environmental health platform designed to help you make informed decisions 
    about your health based on environmental conditions. The platform combines real-time data with 
    advanced analytics to provide personalized health recommendations.
    """)

    # Main Features Section using columns
    st.header("🎯 Key Features")

    # Weather & Health Monitoring
    with st.expander("🌤️ Weather & Health Monitoring", expanded=False):
        st.markdown("""
        It provides real-time weather and air quality monitoring:
        - **Location-based Data**: Enter your city, state, and country
        - **Real-time Updates**: Powered by Tomorrow.io, Open-Meteo, and OpenWeatherMap APIs
        - **Comprehensive Metrics**: Temperature, humidity, air quality index (AQI), and more
        - **Instant Access**: Get immediate insights about your local environmental conditions
        """)

    # Personalized Health Recommendations
    with st.expander("💡 Personalized Health Recommendations", expanded=False):
        st.markdown("""
        Receive AI-powered health advice tailored to your environment:
        - **Smart Analysis**: Utilizes OpenAI's GPT-4 model
        - **Context-Aware**: Recommendations based on:
            - Current temperature
            - Air quality levels
            - Location-specific factors
        - **Practical Advice**: Get actionable health and safety tips
        - **Reliable Backup**: Rule-based recommendations when AI is unavailable
        """)

    # Data Visualization
    with st.expander("📊 Data Visualization", expanded=False):
        st.markdown("""
        Interactive visualizations to understand environmental patterns:
        - **Historical Weather Patterns**: Track temperature trends
        - **AQI History**: Color-coded air quality visualizations
        - **Weather Forecasts**: Interactive Plotly charts
        - **Trend Analysis**: Rolling averages and pattern identification
        """)

    # Weekly Newsletter Service
    with st.expander("📫 Weekly Newsletter Service", expanded=False):
        st.markdown("""
        Stay informed with comprehensive weekly updates:
        - **Weather Summaries**: Coverage of major Indian and global cities
        - **Health Advisories**: Personalized recommendations
        - **Weekly Forecasts**: Upcoming weather predictions
        - **Easy Subscription**: Simple email signup process
        """)

    # Environmental Health Education
    with st.expander("📚 Environmental Health Education", expanded=False):
        st.markdown("""
        Learn about environmental impacts on health:
        - **Educational Resources**: Understanding weather-health relationships
        - **Activity Guidelines**: Recommendations for outdoor activities
        - **Health Management**: Tips for different weather conditions
        - **Environmental Awareness**: Impact of climate on well-being
        """)

    # Platform Features
    st.header("💻 Platform Features")
    st.markdown("""
    - **Modern Interface**: Built with Streamlit for a responsive experience
    - **Cross-Platform**: Works seamlessly on desktop and mobile devices
    - **User-Friendly Navigation**: Easy access to all features
    - **Interactive Components**: Engaging user interface elements
    """)

    # Call to Action
    st.header("🚀 Get Started")
    st.markdown("""
        Ready to take control of your environmental health? Start by:
        1. Checking your local weather conditions
        2. Getting personalized health recommendations
        3. Subscribing to our weekly newsletter
        """)

    # Footer
    st.markdown("---")
    st.markdown("""
    💪 **Empowering you to make informed health decisions based on your environment**
    """)

def weather_page():
    # Session state initialization
    if 'location_submitted' not in st.session_state:
        st.session_state.location_submitted = False
    if 'current_data' not in st.session_state:
        st.session_state.current_data = None
    if 'historical_data' not in st.session_state:
        st.session_state.historical_data = None
    if 'health_advice' not in st.session_state:
        st.session_state.health_advice = None
    if 'error' not in st.session_state:
        st.session_state.error = None
    if 'coordinates' not in st.session_state:
        st.session_state.coordinates = None
    if 'location_info' not in st.session_state:
        st.session_state.location_info = {"city": "", "state": "", "country": ""}

    st.title("🌤️Weather & Health Advisor")
    st.markdown("""
        Get real-time weather, air quality data, and personalized health recommendations based on your location.
        Enter your location details below to begin.
    """)

    # Location input form
    with st.form(key='location_form'):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            country = st.text_input("Country")
        with col2:
            state = st.text_input("State/Province")
        with col3:
            city = st.text_input("City")
        
        submit_button = st.form_submit_button(label='Get Weather Data')
        
        if submit_button:
            try:
                st.session_state.error = None
                with st.spinner("Fetching data..."):
                    # Get coordinates from location
                    coordinates = utils.get_coordinates(city, state, country)
                    
                    if not coordinates:
                        st.session_state.error = "Unable to find coordinates for the specified location. Please check the spelling and try again."
                        st.session_state.location_submitted = False
                    else:
                        # Get current weather and AQI data
                        current_data = weather.get_current_weather_and_aqi(coordinates['lat'], coordinates['lng'])
                        
                        # Get last 24 hours data only
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=1)  # 24 hours
                        historical_data = weather.get_historical_data(
                            coordinates['lat'], 
                            coordinates['lng'], 
                            start_date, 
                            end_date
                        )
                        
                        # Get health recommendations based on temperature and AQI
                        health_advice = ai.get_health_recommendations(
                            location=f"{city}, {state}, {country}",
                            temperature_c=current_data.get('temperature'),
                            aqi=current_data.get('aqi')
                        )
                        
                        # Update session state
                        st.session_state.current_data = current_data
                        st.session_state.historical_data = historical_data
                        st.session_state.health_advice = health_advice
                        st.session_state.coordinates = coordinates
                        st.session_state.location_info = {"city": city, "state": state, "country": country}
                        st.session_state.location_submitted = True
                        
            except Exception as e:
                st.session_state.error = f"An error occurred: {str(e)}"
                st.session_state.location_submitted = False

    # Display error message if any
    if st.session_state.error:
        st.error(st.session_state.error)

    # Display results if location submitted
    if st.session_state.location_submitted and st.session_state.current_data:
        # Create two columns for map and weather data side by side
        map_col, weather_col = st.columns(2)
        
        # Column 1: Map display
        with map_col:
            st.markdown("## Location Map")
            try:
                if st.session_state.coordinates:
                    m = folium.Map(location=[st.session_state.coordinates['lat'], st.session_state.coordinates['lng']], zoom_start=10)
                    
                    location_info = st.session_state.location_info
                    location_name = f"{location_info['city']}, {location_info['state']}, {location_info['country']}"
                    popup_text = f"""
                    <b>{location_name}</b><br>
                    Latitude: {st.session_state.coordinates['lat']:.4f}<br>
                    Longitude: {st.session_state.coordinates['lng']:.4f}
                    """
                    folium.Marker(
                        location=[st.session_state.coordinates['lat'], st.session_state.coordinates['lng']],
                        popup=folium.Popup(popup_text, max_width=300),
                        tooltip=location_name,
                        icon=folium.Icon(color='blue', icon='cloud')
                    ).add_to(m)
                    
                    folium_static(m)
                else:
                    st.warning("Location coordinates not available.")
            except Exception as e:
                st.error(f"Error displaying location map: {str(e)}")
        
        # Column 2: Current Weather and AQI Data
        with weather_col:
            st.markdown("## Current Weather and AQI Data")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    label="Temperature", 
                    value=f"{st.session_state.current_data['temperature']:.1f}°C",
                    delta=f"{utils.celsius_to_fahrenheit(st.session_state.current_data['temperature']):.1f}°F"
                )
                
                feels_like = st.session_state.current_data.get('temperature_apparent', 'N/A')
                if feels_like != 'N/A':
                    feels_like = f"{feels_like:.1f}°C"
                
                st.metric(label="Feels Like", value=feels_like)
                
                humidity = st.session_state.current_data.get('humidity', 'N/A')
                if humidity != 'N/A':
                    humidity = f"{humidity:.1f}%"
                
                st.metric(label="Humidity", value=humidity)
                
                cloud_cover = st.session_state.current_data.get('cloud_cover', 'N/A')
                if cloud_cover != 'N/A':
                    cloud_cover = f"{cloud_cover:.0f}%"
                
                st.metric(label="Cloud Coverage", value=cloud_cover)
                
            with col2:
                aqi = st.session_state.current_data['aqi']
                aqi_color = utils.get_aqi_color(aqi)
                aqi_label = utils.get_aqi_label(aqi)
                
                st.metric(label=f"Air Quality Index ({aqi_label})", value=f"{aqi:.1f}")
                st.markdown(f"<div style='width:100%;height:20px;background-color:{aqi_color}'></div>", unsafe_allow_html=True)
                
                wind_speed = st.session_state.current_data.get('wind_speed', 'N/A')
                if wind_speed != 'N/A':
                    wind_speed = f"{wind_speed:.1f} m/s"
                
                st.metric(label="Wind Speed", value=wind_speed)
                
                pressure = st.session_state.current_data.get('pressure', 'N/A')
                if pressure != 'N/A':
                    pressure = f"{pressure:.1f} hPa"
                
                st.metric(label="Pressure", value=pressure)
                
                visibility = st.session_state.current_data.get('visibility', 'N/A')
                if visibility != 'N/A':
                    visibility = f"{visibility:.1f} km"
                
                st.metric(label="Visibility", value=visibility)
        

        # Get and display forecast data
        if st.session_state.location_submitted and not st.session_state.error:
            try:
                if st.session_state.coordinates:
                    forecast_data = weather.get_forecast_data(
                        st.session_state.coordinates['lat'], 
                        st.session_state.coordinates['lng']
                    )

                    st.markdown("## Weather & AQI Forecast (Next Few Days)")
                    forecast_fig = viz.plot_forecast(forecast_data)
                    st.plotly_chart(forecast_fig, use_container_width=True)

                    forecast_df = pd.DataFrame(forecast_data)
                    forecast_df['date'] = pd.to_datetime(forecast_df['date']).dt.strftime('%Y-%m-%d')
                    forecast_df = forecast_df.round(1)
                    forecast_df.columns = ['Date', 'Min Temp (°C)', 'Max Temp (°C)', 'Avg Temp (°C)', 
                                        'Min AQI', 'Max AQI', 'Avg AQI']
                    st.dataframe(forecast_df, use_container_width=True)
                else:
                    st.warning("Location coordinates not available for forecast data.")
            except Exception as e:
                st.error(f"Error getting forecast data: {str(e)}")
                
            # Last week data
            try:
                last_week_data = None
                if st.session_state.coordinates:
                    last_week_data = weather.get_last_week_data(
                        st.session_state.coordinates['lat'], 
                        st.session_state.coordinates['lng']
                    )
                
                    st.markdown("## Last Week's Historical Weather Data")
                    st.markdown("*Temperature, humidity, and air quality data for the past 7 days*")
                    
                    week_tabs = st.tabs(["Temperature", "Air Quality & Humidity", "Data Table"])
                    
                    with week_tabs[0]:
                        if last_week_data:
                            temp_fig, _ = viz.plot_last_week_data(last_week_data)
                            st.plotly_chart(temp_fig, use_container_width=True)
                        else:
                            st.warning("No temperature data available for the past week")
                    
                    with week_tabs[1]:
                        if last_week_data:
                            _, aqi_humidity_fig = viz.plot_last_week_data(last_week_data)
                            st.plotly_chart(aqi_humidity_fig, use_container_width=True)
                        else:
                            st.warning("No AQI and humidity data available for the past week")
                    
                    with week_tabs[2]:
                        if last_week_data:
                            st.markdown("### Weather Data Table (Last 7 Days)")
                            last_week_df = pd.DataFrame(last_week_data)
                            last_week_df['date'] = pd.to_datetime(last_week_df['date']).dt.strftime('%Y-%m-%d')
                            last_week_df = last_week_df.round(1)
                            last_week_df.columns = ['Date', 'Min Temp (°C)', 'Max Temp (°C)', 'Avg Temp (°C)', 
                                        'Avg Humidity (%)', 'Avg AQI']
                            st.dataframe(last_week_df, use_container_width=True)
                        else:
                            st.warning("No historical data available for the past week")
                else:
                    st.warning("Location coordinates not available for historical data.")
                
            except Exception as e:
                st.error(f"Error getting last week data: {str(e)}")


        # Health recommendations
        st.markdown("## Health Recommendations")
        st.markdown(st.session_state.health_advice)
        
        # Last 24 Hours Data visualizations
        if st.session_state.historical_data and len(st.session_state.historical_data) > 0:
            st.markdown("## Last 24 Hours Data")
            
            last24h_tab1, last24h_tab2 = st.tabs(["Temperature", "Air Quality"])
            
            with last24h_tab1:
                temp_24h_fig = viz.plot_temperature_last_24h(st.session_state.historical_data)
                st.plotly_chart(temp_24h_fig, use_container_width=True)
                
            with last24h_tab2:
                aqi_24h_fig = viz.plot_aqi_last_24h(st.session_state.historical_data)
                st.plotly_chart(aqi_24h_fig, use_container_width=True)
        else:
            st.info("Last 24 hours data is not available for this location.")

    # Newsletter subscription section
    st.markdown("---")
    st.markdown("## 📫 Subscribe to Weekly Weather Updates")
    st.markdown("""
        Get weekly updates delivered to your inbox featuring:
        - Temperature and AQI trends for your location
        - Weather highlights from major cities in India
        - Global weather updates and air quality information
        - Weekly temperature forecasts and health recommendations
    """)

    with st.form(key='newsletter_form'):
        col1, col2 = st.columns(2)
        with col1:
            subscriber_name = st.text_input("Your Name")
        with col2:
            subscriber_email = st.text_input("Email Address")
        
        st.markdown("### Your Location (for personalized updates)")
        col3, col4, col5 = st.columns(3)
        with col3:
            subscriber_country = st.text_input("Country", value=country if 'country' in locals() else "")
        with col4:
            subscriber_state = st.text_input("State/Province", value=state if 'state' in locals() else "")
        with col5:
            subscriber_city = st.text_input("City", value=city if 'city' in locals() else "")
        
        subscribe_button = st.form_submit_button(label='Subscribe to Newsletter')
        
        if subscribe_button:
            if not subscriber_name or not subscriber_email:
                st.error("Please provide both name and email address.")
            else:
                result = db.add_subscriber(
                    name=subscriber_name,
                    email=subscriber_email,
                    city=subscriber_city,
                    state=subscriber_state,
                    country=subscriber_country
                )
                
                if result["success"]:
                    st.success(result["message"])
                    
                    with st.spinner("Sending welcome email..."):
                        try:
                            db_session = None
                            try:
                                db_session = db.get_db()
                                subscriber = db_session.query(db.Subscriber).filter(db.Subscriber.email == subscriber_email).first()
                                if subscriber:
                                    email_sent = newsletter.send_welcome_email(subscriber)
                                    if email_sent:
                                        st.success("Welcome email sent to your inbox!")
                                    else:
                                        st.warning("Welcome email could not be sent. You'll still receive the weekly newsletter.")
                            except Exception as e:
                                st.warning(f"Could not retrieve subscriber: {str(e)}. You'll still receive the weekly newsletter.")
                            finally:
                                if db_session is not None:
                                    db_session.close()
                        except Exception as e:
                            st.warning(f"Welcome email could not be sent: {str(e)}. You'll still receive the weekly newsletter.")
                    
                    st.markdown("""
                        #### 🎉 Welcome to IcoHealth Weather Newsletter!
                        
                        You'll receive your first newsletter this Sunday at 8 AM. Each newsletter includes:
                        - Personalized weather forecast for your location
                        - Temperature and AQI trends across India
                        - Global weather highlights
                        - Health recommendations based on weather conditions
                        
                        You can unsubscribe at any time using the link in the newsletter.
                    """)
                else:
                    st.error(result["message"])

    # Start the newsletter scheduler (only once)
    if 'newsletter_scheduler_started' not in st.session_state:
        try:
            newsletter.start_scheduler()
            st.session_state.newsletter_scheduler_started = True
        except Exception as e:
            print(f"Error starting newsletter scheduler: {str(e)}")
            st.session_state.newsletter_scheduler_started = True

    # Admin section
    with st.expander("Admin Tools"):
        st.markdown("### Subscriber Management")
        
        if 'admin_view_subscribers' not in st.session_state:
            st.session_state.admin_view_subscribers = False
        if 'subscribers_list' not in st.session_state:
            st.session_state.subscribers_list = []
        if 'admin_message' not in st.session_state:
            st.session_state.admin_message = None
        
        admin_tabs = st.tabs(["View Subscribers", "Delete Subscriber", "Database Actions"])
        
        with admin_tabs[0]:
            if st.button("Get All Subscribers"):
                try:
                    db_session = db.get_db()
                    try:
                        subscribers = db_session.query(db.Subscriber).all()
                        
                        if subscribers:
                            subscribers_data = []
                            for sub in subscribers:
                                subscribed_at_ist = sub.get_subscribed_at_ist()
                                last_email_sent_ist = sub.get_last_email_sent_ist()
                                
                                subscribers_data.append({
                                    "ID": sub.id,
                                    "Name": sub.name,
                                    "Email": sub.email,
                                    "Subscribed On (IST)": subscribed_at_ist.strftime('%Y-%m-%d %H:%M:%S') if subscribed_at_ist else "N/A",
                                    "Status": "Active" if sub.is_active else "Inactive",
                                    "Location": f"{sub.location_city or 'N/A'}, {sub.location_state or 'N/A'}, {sub.location_country or 'N/A'}",
                                    "Last Email (IST)": last_email_sent_ist.strftime('%Y-%m-%d %H:%M:%S') if last_email_sent_ist else "Never"
                                })
                            
                            st.session_state.subscribers_list = subscribers_data
                            st.session_state.admin_view_subscribers = True
                            st.session_state.admin_message = f"Found {len(subscribers)} subscribers"
                        else:
                            st.session_state.admin_message = "No subscribers found in the database"
                            st.session_state.admin_view_subscribers = False
                            st.session_state.subscribers_list = []
                    finally:
                        db_session.close()
                except Exception as e:
                    st.session_state.admin_message = f"Error retrieving subscribers: {str(e)}"
                    st.session_state.admin_view_subscribers = False
            
            if st.session_state.admin_message:
                st.info(st.session_state.admin_message)
                
            if st.session_state.admin_view_subscribers and st.session_state.subscribers_list:
                st.dataframe(st.session_state.subscribers_list)
        
        with admin_tabs[1]:
            subscriber_email = st.text_input("Enter subscriber email to delete/unsubscribe")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Unsubscribe (Mark Inactive)"):
                    if subscriber_email:
                        result = db.unsubscribe(subscriber_email)
                        st.info(result["message"])
                    else:
                        st.warning("Please enter an email address")
            
            with col2:
                if st.button("Permanently Delete"):
                    if subscriber_email:
                        result = db.delete_subscriber(subscriber_email)
                        if result["success"]:
                            st.success(result["message"])
                        else:
                            st.error(result["message"])
                    else:
                        st.warning("Please enter an email address")
        
        with admin_tabs[2]:
            st.warning("⚠️ These actions affect the entire subscriber database. Use with caution.")
            
            if st.button("Count Subscribers"):
                result = db.count_subscribers()
                if result["success"]:
                    st.info(f"Total subscribers: {result['total']} (Active: {result['active']}, Inactive: {result['inactive']})")
                else:
                    st.error(result["message"])
            
            if st.button("Clear All Data (DANGER)"):
                st.error("⚠️ This will delete ALL subscriber data. This cannot be undone.")
                confirm = st.text_input("Type 'DELETE ALL' to confirm")
                if confirm == "DELETE ALL":
                    result = db.clear_all_subscribers()
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
    
    

def visualizations_page():
    st.title("📊 AI-Powered Data Visualization Platform")
    st.write("Upload your dataset and get intelligent visualization suggestions powered by AI!")
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="Upload a CSV file to generate visualizations"
    )

    if uploaded_file is not None:
        try:
            with st.spinner('Processing your data...'):
                # Read and process data
                data_processor = DataProcessor()
                df = data_processor.read_data(uploaded_file)

                # Create tabs for different sections
                main_tabs = st.tabs(["Data Preview", "AI Visualizations", "Advanced Analytics"])

                with main_tabs[0]:
                    st.subheader("Data Preview")
                    st.dataframe(df.head(10), use_container_width=True)

                with main_tabs[1]:
                    # Get data insights using DeepSeek
                    deepseek_analyzer = DeepSeekAnalyzer()
                    analysis_results = deepseek_analyzer.analyze_dataset(df)

                    st.subheader("AI-Suggested Visualizations")
                    viz_tabs = st.tabs([f"Visualization {i+1}" for i in range(5)])

                    for i, (tab, suggestion) in enumerate(zip(viz_tabs, analysis_results['suggestions'])):
                        with tab:
                            try:
                                st.markdown(f"### {suggestion['title']}")
                                viz_col, info_col = st.columns([3, 1])

                                with viz_col:
                                    viz_generator = VisualizationGenerator(df)
                                    fig = viz_generator.create_visualization(
                                        suggestion['type'],
                                        suggestion['columns'],
                                        suggestion['title']
                                    )
                                    fig.update_layout(
                                        autosize=True,
                                        height=600,
                                        margin=dict(l=50, r=50, t=50, b=50),
                                        showlegend=True,
                                        template="plotly_white"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)

                                with info_col:
                                    st.markdown("#### Details")
                                    st.markdown(f"**Type:** {suggestion['type'].capitalize()}")
                                    st.markdown(f"**Columns used:**")
                                    for col in suggestion['columns']:
                                        st.markdown(f"- {col}")

                                    # Download options
                                    html_str = fig.to_html(
                                        include_plotlyjs='cdn',
                                        full_html=False
                                    )
                                    st.download_button(
                                        label="📥 Download Interactive Plot",
                                        data=html_str,
                                        file_name=f'visualization_{i+1}.html',
                                        mime='text/html'
                                    )

                                    csv_data = df[suggestion['columns']].to_csv(index=False)
                                    st.download_button(
                                        label="📥 Download Data (CSV)",
                                        data=csv_data,
                                        file_name=f'visualization_{i+1}_data.csv',
                                        mime='text/csv'
                                    )

                            except Exception as e:
                                st.error(f"Error creating visualization {i+1}: {str(e)}")
                                continue

                with main_tabs[2]:
                    st.subheader("Advanced Data Analysis")

                    # Initialize advanced analytics
                    advanced_analytics = AdvancedAnalytics(df)

                    # Create subtabs for different analyses
                    analysis_tabs = st.tabs([
                        "Statistical Summary",
                        "Correlation Analysis",
                        "Outlier Detection",
                        "Distribution Analysis",
                        "Trend Analysis"
                    ])

                    with analysis_tabs[0]:
                        st.markdown("### Statistical Summary")
                        stats_summary = advanced_analytics.get_statistical_summary()
                        if stats_summary:
                            for col, stats in stats_summary.items():
                                with st.expander(f"Statistics for {col}"):
                                    stats_df = pd.DataFrame([stats]).T
                                    stats_df.columns = ['Value']
                                    st.dataframe(stats_df)
                        else:
                            st.info("No numeric columns found for statistical analysis.")

                    with analysis_tabs[1]:
                        st.markdown("### Correlation Analysis")
                        corr_fig = advanced_analytics.create_correlation_heatmap()
                        if corr_fig:
                            st.plotly_chart(corr_fig, use_container_width=True)
                        else:
                            st.info("Insufficient numeric columns for correlation analysis.")

                    with analysis_tabs[2]:
                        st.markdown("### Outlier Detection")
                        threshold = st.slider("IQR Threshold", 1.0, 3.0, 1.5, 0.1,
                                               help="Higher values mean fewer outliers")
                        outliers = advanced_analytics.detect_outliers(threshold)

                        for col, stats in outliers.items():
                            with st.expander(f"Outliers in {col}"):
                                st.markdown(f"""
                                - Number of outliers: {stats['count']}
                                - Percentage of outliers: {stats['percentage']:.2f}%
                                - Bounds: [{stats['bounds']['lower']:.2f}, {stats['bounds']['upper']:.2f}]
                                """)

                    with analysis_tabs[3]:
                        st.markdown("### Distribution Analysis")
                        dist_fig = advanced_analytics.create_distribution_plots()
                        if dist_fig:
                            st.plotly_chart(dist_fig, use_container_width=True)
                        else:
                            st.info("No numeric columns found for distribution analysis.")

                    with analysis_tabs[4]:
                        st.markdown("### Trend Analysis")
                        date_cols = df.select_dtypes(include=['datetime64']).columns
                        if len(date_cols) > 0:
                            selected_date = st.selectbox("Select Date Column", date_cols)
                            trends = advanced_analytics.analyze_trends(selected_date)
                            if trends:
                                for col, analysis in trends.items():
                                    with st.expander(f"Trend Analysis for {col}"):
                                        st.plotly_chart(analysis['visualization'],
                                                          use_container_width=True)
                                        st.markdown(f"""
                                        - Overall trend: {analysis['statistics']['overall_trend']}
                                        - Volatility: {analysis['statistics']['volatility']:.2f}
                                        """)
                        else:
                            st.info("No datetime columns found for trend analysis.")

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please make sure your CSV file is properly formatted and try again.")





def main():
    navigation()

    # Get current page from query params (using new API)
    current_page = st.query_params.get("page", "home")

    if current_page == "home":
        home_page()
    elif current_page == "about":
        about_page()
    elif current_page == "weather":
        weather_page()
    elif current_page == "visualizations":
        visualizations_page()
    elif current_page == "model":
        model_page()

if __name__ == "__main__":
    main()
