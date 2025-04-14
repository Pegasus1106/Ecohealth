# model_page.py
import os
import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_squared_error
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv


load_dotenv()
# Constants
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY", "")
BASE_URL = 'https://api.openweathermap.org/data/2.5/'

# Get Current Weather from API
def get_current_weather(city):
    url = f"{BASE_URL}weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    coords = data.get('coord', {})
    return {
        'lat': coords.get('lat', 0),
        'lon': coords.get('lon', 0),
        'city': data['name'],
        'current_temp': round(data['main']['temp']),
        'feels_like': round(data['main']['feels_like']),
        'temp_min': round(data['main']['temp_min']),
        'temp_max': round(data['main']['temp_max']),
        'humidity': round(data['main']['humidity']),
        'description': data['weather'][0]['description'],
        'country': data['sys']['country'],
        'wind_gust_dir': data['wind']['deg'],
        'pressure': data['main']['pressure'],
        'Wind_Gust_Speed': data['wind']['speed']
    }

# Load and clean historical dataset
def read_historical_data(filename):
    df = pd.read_csv(filename).dropna().drop_duplicates()
    return df

# Encode categorical variables and prepare features/target
def prepare_data(data):
    le = LabelEncoder()
    data['WindGustDir'] = le.fit_transform(data['WindGustDir'])
    data['RainTomorrow'] = le.fit_transform(data['RainTomorrow'])
    X = data[['MinTemp', 'MaxTemp', 'WindGustDir', 'WindGustSpeed', 'Humidity', 'Pressure', 'Temp']]
    y = data['RainTomorrow']
    return X, y, le

def train_rain_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    return model, mse

def prepare_regression_data(data, feature):
    X, y = [], []
    for i in range(len(data) - 1):
        X.append(data[feature].iloc[i])
        y.append(data[feature].iloc[i + 1])
    return np.array(X).reshape(-1, 1), np.array(y)

def train_regression_model(X, y):
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def predict_future(model, current_value):
    predictions = [current_value]
    for _ in range(5):
        next_value = model.predict(np.array([[predictions[-1]]]))
        predictions.append(next_value[0])
    return predictions[1:]

# Streamlit Page Function
def model_page():

    st.markdown("<h1 style='text-align: center;'>🌦️ Weather Forecast Dashboard</h1>", unsafe_allow_html=True)

    city = st.text_input("🔍 Enter City Name", "Mumbai")

    if st.button("Get Weather Info"):
        with st.spinner("Fetching weather data..."):
            try:
                current_weather = get_current_weather(city)
                lat, lon = current_weather['lat'], current_weather['lon']

                st.subheader(f"📍 Location: {current_weather['city']}, {current_weather['country']}")
                st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

                historical_data = read_historical_data("weather.csv")
                X, y, le = prepare_data(historical_data)
                rain_model, mse = train_rain_model(X, y)

                wind_deg = current_weather['wind_gust_dir'] % 360
                compass_points = [
                    ("N", 0, 11.25), ("NNE", 11.25, 33.75), ("NE", 33.75, 56.25),
                    ("ENE", 56.25, 78.75), ("E", 78.75, 101.25), ("ESE", 101.25, 123.75),
                    ("SE", 123.75, 146.25), ("SSE", 146.25, 168.75), ("S", 168.75, 191.25),
                    ("SSW", 191.25, 213.75), ("SW", 213.75, 236.25), ("WSW", 236.25, 258.75),
                    ("W", 258.75, 281.25), ("WNW", 281.25, 303.75), ("NW", 303.75, 326.25),
                    ("NNW", 326.25, 348.75), ("N", 348.75, 360)
                ]
                compass_direction = next(point for point, start, end in compass_points if start <= wind_deg < end)
                compass_direction_encoded = le.transform([compass_direction])[0] if compass_direction in le.classes_ else -1

                current_data = {
                    'MinTemp': current_weather['temp_min'],
                    'MaxTemp': current_weather['temp_max'],
                    'WindGustDir': compass_direction_encoded,
                    'WindGustSpeed': current_weather['Wind_Gust_Speed'],
                    'Humidity': current_weather['humidity'],
                    'Pressure': current_weather['pressure'],
                    'Temp': current_weather['current_temp'],
                }
                current_df = pd.DataFrame([current_data])
                rain_prediction = rain_model.predict(current_df)[0]

                temp_model = train_regression_model(*prepare_regression_data(historical_data, 'Temp'))
                hum_model = train_regression_model(*prepare_regression_data(historical_data, 'Humidity'))

                future_temp = predict_future(temp_model, current_weather['temp_min'])
                future_humidity = predict_future(hum_model, current_weather['humidity'])

                timezone = pytz.timezone('Asia/Kolkata')
                now = datetime.now(timezone).replace(minute=0, second=0, microsecond=0)
                future_times = [(now + timedelta(hours=i + 1)).strftime("%H:%M") for i in range(5)]

                # --- Weather Metrics Box ---
                with st.container():
                    st.markdown("### 🌡️ Weather Summary")
                    st.markdown("---")
                    
                    row1_col1, row1_col2, row1_col3 = st.columns(3)
                    row1_col1.metric("Current Temperature", f"{current_weather['current_temp']}°C")
                    row1_col2.metric("Feels Like", f"{current_weather['feels_like']}°C")
                    row1_col3.metric("Humidity", f"{current_weather['humidity']}%")
                    
                    row2_col1, row2_col2, row2_col3 = st.columns(3)
                    row2_col1.metric("Weather Description", current_weather['description'].title())
                    row2_col2.metric("Rain Prediction", "Yes" if rain_prediction else "No")
                    row2_col3.metric("Rain Model MSE", round(mse, 3))
                    
                    st.markdown("---")

                # --- Forecast Section ---
                st.subheader("📈 Next 5-Hour Forecast")

                forecast_df = pd.DataFrame({
                    'Time': future_times,
                    'Temperature (°C)': future_temp,
                    'Humidity (%)': future_humidity
                })

                with st.expander("🔍 Forecast Data Table"):
                    st.dataframe(forecast_df)

                st.line_chart(forecast_df.set_index("Time"))

            except Exception as e:
                st.error(f"⚠️ Error: {e}")
