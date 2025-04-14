import requests
import os
import math
import random
from datetime import datetime, timedelta, date
import time
from dotenv import load_dotenv

load_dotenv()


# API keys with validation
TOMORROW_API_KEY = os.environ.get("TOMORROW_IO_API_KEY", "")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY", "")

print(f"TOMORROW_API_KEY present: {bool(TOMORROW_API_KEY)}")
print(f"OPENWEATHER_API_KEY present: {bool(OPENWEATHER_API_KEY)}")

if not TOMORROW_API_KEY or not OPENWEATHER_API_KEY:
    print("Warning: One or more API keys are missing!")

# API base URLs
TOMORROW_BASE_URL = "https://api.tomorrow.io/v4"
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

def calculate_aqi_from_pollutants(components):
    """
    Calculate AQI based on individual pollutant concentrations using Environmental Protection Agency standards.

    Args:
        components (dict): Dictionary containing pollutant concentrations

    Returns:
        int: Calculated AQI value
    """
    # EPA breakpoints for AQI calculation
    pm25_breakpoints = [
        (0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500)
    ]

    pm10_breakpoints = [
        (0, 54, 0, 50),
        (55, 154, 51, 100),
        (155, 254, 101, 150),
        (255, 354, 151, 200),
        (355, 424, 201, 300),
        (425, 604, 301, 500)
    ]

    def calculate_pollutant_aqi(concentration, breakpoints):
        for low_conc, high_conc, low_aqi, high_aqi in breakpoints:
            if low_conc <= concentration <= high_conc:
                return int(((high_aqi - low_aqi) / (high_conc - low_conc)) * 
                         (concentration - low_conc) + low_aqi)
        return 500  # Maximum AQI value for off-scale readings

    aqi_values = []

    # Calculate AQI for PM2.5
    if 'pm2_5' in components:
        pm25_aqi = calculate_pollutant_aqi(components['pm2_5'], pm25_breakpoints)
        aqi_values.append(pm25_aqi)

    # Calculate AQI for PM10
    if 'pm10' in components:
        pm10_aqi = calculate_pollutant_aqi(components['pm10'], pm10_breakpoints)
        aqi_values.append(pm10_aqi)

    # Return the highest AQI value (worst air quality)
    return max(aqi_values) if aqi_values else 50

def get_current_weather_and_aqi(lat, lon):
    """
    Get current weather data from Open-Meteo API and AQI from OpenWeatherMap API.

    Args:
        lat (float): Latitude
        lon (float): Longitude

    Returns:
        dict: Dictionary containing current temperature, AQI, and other weather data
    """
    result = {
        'temperature': None,
        'temperature_apparent': None,  # Feels like temperature
        'humidity': None,
        'wind_speed': None,
        'precipitation_probability': None,
        'cloud_cover': None,          # Cloud coverage percentage
        'pressure': None,             # Atmospheric pressure at sea level
        'visibility': None,           # Visibility in km
        'aqi': None,
        'error': None
    }

    # Get weather data from Open-Meteo
    weather_success = False
    try:
        # Open-Meteo API doesn't require an API key
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,cloud_cover,pressure_msl,visibility,wind_speed_10m",
            "timezone": "auto",
            "forecast_days": 1
        }

        print(f"Fetching weather data from Open-Meteo for location: {lat},{lon}")
        weather_response = requests.get(weather_url, params=weather_params)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        current = weather_data.get('current', {})
        print(f"Open-Meteo response: {current}")

        if current:
            # Extract the data from Open-Meteo response
            result['temperature'] = current.get('temperature_2m')
            result['temperature_apparent'] = current.get('apparent_temperature')
            result['humidity'] = current.get('relative_humidity_2m')
            result['wind_speed'] = current.get('wind_speed_10m')
            result['precipitation_probability'] = current.get('precipitation_probability')
            result['cloud_cover'] = current.get('cloud_cover')
            result['pressure'] = current.get('pressure_msl')
            
            # Open-Meteo visibility is in meters, convert to km
            visibility_m = current.get('visibility')
            if visibility_m is not None:
                result['visibility'] = visibility_m / 1000  # Convert from meters to km
            
            weather_success = all(v is not None for v in [
                result['temperature'],
                result['humidity'],
                result['wind_speed']
            ])

    except Exception as e:
        print(f"Error getting weather data from Open-Meteo: {str(e)}")
        result['error'] = f"Open-Meteo API error: {str(e)}"

    # If Tomorrow.io fails, try OpenWeatherMap as fallback
    if not weather_success:
        try:
            if not OPENWEATHER_API_KEY:
                raise ValueError("OpenWeatherMap API key is missing")

            weather_url = f"{OPENWEATHER_BASE_URL}/weather"
            weather_params = {
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            }

            print(f"Fetching weather data from OpenWeatherMap for location: {lat},{lon}")
            weather_response = requests.get(weather_url, params=weather_params)
            weather_response.raise_for_status()
            weather_data = weather_response.json()
            print(f"OpenWeatherMap response: {weather_data}")

            if 'main' in weather_data:
                result['temperature'] = weather_data['main'].get('temp')
                result['temperature_apparent'] = weather_data['main'].get('feels_like')
                result['humidity'] = weather_data['main'].get('humidity')
                result['pressure'] = weather_data['main'].get('pressure')
            
            if 'wind' in weather_data:
                result['wind_speed'] = weather_data['wind'].get('speed')
            
            if 'clouds' in weather_data:
                result['cloud_cover'] = weather_data['clouds'].get('all')
                
            if 'visibility' in weather_data:
                # OpenWeatherMap visibility is in meters, convert to km
                visibility_m = weather_data.get('visibility')
                if visibility_m is not None:
                    result['visibility'] = visibility_m / 1000  # Convert to km

        except Exception as e:
            print(f"Error getting weather data from OpenWeatherMap: {str(e)}")
            if result['error']:
                result['error'] += f"\nOpenWeatherMap API error: {str(e)}"
            else:
                result['error'] = f"OpenWeatherMap API error: {str(e)}"

    # Get AQI data from OpenWeatherMap
    try:
        if not OPENWEATHER_API_KEY:
            raise ValueError("OpenWeatherMap API key is missing")

        aqi_url = f"{OPENWEATHER_BASE_URL}/air_pollution"
        aqi_params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY
        }

        print(f"Fetching AQI data from OpenWeatherMap for location: {lat},{lon}")
        aqi_response = requests.get(aqi_url, params=aqi_params)
        aqi_response.raise_for_status()
        aqi_data = aqi_response.json()
        print(f"AQI response: {aqi_data}")

        if 'list' in aqi_data and aqi_data['list']:
            components = aqi_data['list'][0].get('components', {})
            if components:
                result['aqi'] = calculate_aqi_from_pollutants(components)

    except Exception as e:
        print(f"Error getting AQI data from OpenWeatherMap: {str(e)}")
        if result['error']:
            result['error'] += f"\nAQI API error: {str(e)}"
        else:
            result['error'] = f"AQI API error: {str(e)}"

    # Set default values if any data is missing
    if result['temperature'] is None:
        result['temperature'] = 22.0
    if result['temperature_apparent'] is None:
        # If we have temperature but not feels-like, assume they're the same
        result['temperature_apparent'] = result['temperature']
    if result['humidity'] is None:
        result['humidity'] = 50.0
    if result['wind_speed'] is None:
        result['wind_speed'] = 5.0
    if result['precipitation_probability'] is None:
        result['precipitation_probability'] = 0.0
    if result['cloud_cover'] is None:
        result['cloud_cover'] = 10.0
    if result['pressure'] is None:
        result['pressure'] = 1013.25  # Standard atmospheric pressure at sea level
    if result['visibility'] is None:
        result['visibility'] = 10.0  # 10km visibility (clear day)
    if result['aqi'] is None:
        result['aqi'] = 50.0

    return result

def get_historical_data(lat, lon, start_date, end_date):
    """
    Get last 24 hours weather data for visualizations.
    Tries to fetch real data from OpenWeatherMap API,
    then falls back to forecast data for recent hours.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        start_date (datetime): Start date (should be 24 hours before end_date)
        end_date (datetime): End date (usually current time)
        
    Returns:
        list: List of dictionaries containing last 24 hours data with 'is_last_24h' flag
    """
    try:
        # Make sure start_date and end_date are valid
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            # Convert to datetime if they're strings
            try:
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date)
                else:
                    start_date = datetime.now() - timedelta(days=90)
                    
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date)
                else:
                    end_date = datetime.now()
            except:
                # If anything fails, use default time range
                start_date = datetime.now() - timedelta(days=90)
                end_date = datetime.now()
        
        # Make sure end_date is after start_date
        if end_date <= start_date:
            end_date = start_date + timedelta(days=1)

        # First, get current weather and AQI data
        current_data = get_current_weather_and_aqi(lat, lon)
        
        if not current_data or 'temperature' not in current_data or current_data['temperature'] is None:
            current_temp = 22.0
            current_aqi = 50.0
        else:
            # Verify if temperature seems realistic (between -50°C and 50°C)
            temp = current_data.get('temperature')
            if temp is not None and (-50 <= temp <= 50):
                current_temp = temp
            else:
                # Fallback to a reasonable temperature based on location and month
                # Get the current season for the location
                today = date.today()
                month = today.month
                is_northern = lat > 0
                
                # Estimate temperature based on latitude and season
                if abs(lat) < 23.5:  # Tropical zone
                    current_temp = 28.0  # Generally warm
                elif abs(lat) < 45:  # Temperate zone
                    if is_northern:
                        # Northern hemisphere
                        if month in [12, 1, 2]:  # Winter
                            current_temp = 5.0
                        elif month in [3, 4, 5]:  # Spring
                            current_temp = 15.0
                        elif month in [6, 7, 8]:  # Summer
                            current_temp = 25.0
                        else:  # Fall
                            current_temp = 18.0
                    else:
                        # Southern hemisphere (reverse seasons)
                        if month in [12, 1, 2]:  # Summer
                            current_temp = 25.0
                        elif month in [3, 4, 5]:  # Fall
                            current_temp = 18.0
                        elif month in [6, 7, 8]:  # Winter
                            current_temp = 5.0
                        else:  # Spring
                            current_temp = 15.0
                else:  # Polar zones
                    if is_northern:
                        if month in [5, 6, 7, 8, 9]:  # Warmer months
                            current_temp = 10.0
                        else:  # Colder months
                            current_temp = -10.0
                    else:
                        if month in [11, 12, 1, 2, 3]:  # Warmer months
                            current_temp = 10.0
                        else:  # Colder months
                            current_temp = -10.0
                
                print(f"Using fallback temperature {current_temp}°C instead of {temp}°C which seemed unrealistic")
                
            current_aqi = current_data.get('aqi', 50.0)
            
        # Try to get historical data from external APIs
        all_data = []
        current_time = datetime.now()
        
        # Get current date/time
        current_hour = current_time.replace(minute=0, second=0, microsecond=0)
        
        # Attempt to get 5-day forecast data (including past days when available)
        print("Attempting to fetch 5-day forecast with hourly data...")
        forecast_data = []
        try:
            if OPENWEATHER_API_KEY:
                forecast_url = f"{OPENWEATHER_BASE_URL}/forecast"
                forecast_params = {
                    "lat": lat, 
                    "lon": lon,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric"
                }
                
                forecast_response = requests.get(forecast_url, params=forecast_params)
                forecast_response.raise_for_status()
                forecast_json = forecast_response.json()
                
                if 'list' in forecast_json:
                    forecast_data = forecast_json['list']
                    print(f"Retrieved {len(forecast_data)} points from forecast API")
        except Exception as e:
            print(f"Error fetching forecast data: {str(e)}")

        # Try to get Air Quality data as well
        aqi_data = []
        try:
            if OPENWEATHER_API_KEY:
                # Current AQI
                current_aqi_url = f"{OPENWEATHER_BASE_URL}/air_pollution"
                current_aqi_params = {
                    "lat": lat,
                    "lon": lon,
                    "appid": OPENWEATHER_API_KEY
                }
                
                current_aqi_response = requests.get(current_aqi_url, params=current_aqi_params)
                current_aqi_response.raise_for_status()
                current_aqi_json = current_aqi_response.json()
                
                if 'list' in current_aqi_json:
                    aqi_data.extend(current_aqi_json['list'])
                
                # AQI forecast
                aqi_forecast_url = f"{OPENWEATHER_BASE_URL}/air_pollution/forecast"
                aqi_forecast_params = {
                    "lat": lat,
                    "lon": lon,
                    "appid": OPENWEATHER_API_KEY
                }
                
                aqi_forecast_response = requests.get(aqi_forecast_url, params=aqi_forecast_params)
                aqi_forecast_response.raise_for_status()
                aqi_forecast_json = aqi_forecast_response.json()
                
                if 'list' in aqi_forecast_json:
                    aqi_data.extend(aqi_forecast_json['list'])
                    print(f"Retrieved {len(aqi_data)} points from AQI APIs")
        except Exception as e:
            print(f"Error fetching AQI data: {str(e)}")
        
        # Generate last 24 hours data
        print("Generating 24-hour data...")
        
        # Store temperature deviations for this location by hour
        # Based on typical daily temperature patterns
        hourly_temp_deviations = [
            -2.5, -3.0, -3.2, -3.5, -3.0, -2.5,  # 0-5 AM (coldest before dawn)
            -1.5, -0.5, 1.0, 2.5, 4.0, 5.0,      # 6-11 AM (warming up)
            5.5, 5.8, 5.5, 5.0, 4.0, 3.0,        # 12-5 PM (warmest, then cooling)
            1.5, 0.0, -1.0, -1.5, -2.0, -2.2     # 6-11 PM (cooling for night)
        ]
        
        # For last 24 hours data
        for hour_offset in range(24):
            # Calculate the timestamp for this hour
            timestamp = current_hour - timedelta(hours=24-hour_offset)
            hour_of_day = timestamp.hour
            
            # Variables to store the data for this hour
            temp_found = False
            temp = None
            aqi_found = False
            aqi = None
            
            # Search for this time in the forecast data 
            # (sometimes forecast includes recent past hours)
            for fc_item in forecast_data:
                fc_time = datetime.fromtimestamp(fc_item['dt'])
                # If within 2 hours (handles interpolation needs)
                if abs((fc_time - timestamp).total_seconds()) < 7200:
                    if 'main' in fc_item and 'temp' in fc_item['main']:
                        temp = fc_item['main']['temp']
                        temp_found = True
                        print(f"Found actual forecast temperature for {timestamp}: {temp}°C")
                        break
            
            # If no temperature found in forecast, generate based on current_temp
            if not temp_found:
                # Use the hourly deviation array 
                hourly_deviation = hourly_temp_deviations[hour_of_day]
                random_factor = random.uniform(-0.5, 0.5)  # Small random adjustment
                temp = current_temp + hourly_deviation + random_factor
                
            # Look for AQI data for this hour
            for aqi_item in aqi_data:
                aqi_time = datetime.fromtimestamp(aqi_item['dt'])
                if abs((aqi_time - timestamp).total_seconds()) < 7200:
                    if 'components' in aqi_item:
                        aqi = calculate_aqi_from_pollutants(aqi_item['components'])
                        aqi_found = True
                        print(f"Found actual AQI for {timestamp}: {aqi}")
                        break
                    elif 'main' in aqi_item and 'aqi' in aqi_item['main']:
                        # Convert 1-5 scale to AQI value
                        aqi = aqi_item['main']['aqi'] * 50
                        aqi_found = True
                        break
            
            # If no AQI found, generate based on current AQI and time patterns
            if not aqi_found:
                # AQI tends to be worse during rush hours
                if 7 <= hour_of_day <= 9:  # Morning rush
                    aqi_factor = 1.2
                elif 16 <= hour_of_day <= 19:  # Evening rush
                    aqi_factor = 1.15
                elif 11 <= hour_of_day <= 15:  # Mid-day (often better)
                    aqi_factor = 0.9
                elif 22 <= hour_of_day <= 4:  # Night (usually better)
                    aqi_factor = 0.85
                else:
                    aqi_factor = 1.0
                
                # Add small random adjustment
                random_factor = random.uniform(0.9, 1.1)
                aqi = current_aqi * aqi_factor * random_factor
            
            # Ensure values are within reasonable ranges
            aqi = min(500, max(1, aqi))
            
            # Add the data point to our dataset
            all_data.append({
                'date': timestamp.isoformat(),
                'temperature': temp,
                'aqi': aqi,
                'is_last_24h': True,
                'hour': hour_of_day
            })
        
       
        # We're only focusing on the last 24 hours data
        
        # Add current day data
        all_data.append({
            'date': current_time.isoformat(),
            'temperature': current_temp,
            'aqi': current_aqi,
            'is_last_24h': False
        })
        
        return all_data
        
    except Exception as e:
        print(f"Error generating last 24 hours data: {str(e)}")
        # Return minimal dataset to prevent further errors
        current_time = datetime.now()
        
        # Get current weather as fallback
        current_data = get_current_weather_and_aqi(lat, lon)
        current_temp = current_data.get('temperature', 22.0) if current_data else 22.0
        current_aqi = current_data.get('aqi', 50.0) if current_data else 50.0
        
        # Basic fallback dataset for 24-hour data
        historical_data = []
        
        # Add 24-hour data with realistic daily variation
        for h in range(24):
            hour_time = current_time - timedelta(hours=24-h)
            hour_of_day = hour_time.hour
            
            # Simple temperature variation based on time of day
            if hour_of_day < 6:  # Early morning (coldest)
                temp_factor = -3
            elif hour_of_day < 14:  # Morning to afternoon (warming)
                temp_factor = (hour_of_day - 6) * 0.5
            else:  # Afternoon to night (cooling)
                temp_factor = 4 - ((hour_of_day - 14) * 0.5)
            
            # Simple AQI variation based on time of day
            if hour_of_day < 8:  # Morning rush hour
                aqi_factor = 1.1
            elif hour_of_day < 17:  # Mid-day
                aqi_factor = 0.9
            elif hour_of_day < 21:  # Evening rush hour
                aqi_factor = 1.05
            else:  # Night
                aqi_factor = 0.95
            
            historical_data.append({
                'date': hour_time.isoformat(),
                'temperature': current_temp + temp_factor,
                'aqi': min(500, max(1, current_aqi * aqi_factor)),
                'is_last_24h': True,
                'hour': hour_of_day
            })
        
        return historical_data

def get_last_week_data(lat, lon):
    """
    Get last week's weather data using Open-Meteo API for temperature data
    and OpenWeatherMap API for AQI data.
    This includes min/max/avg temperature, air quality, and humidity.

    Args:
        lat (float): Latitude
        lon (float): Longitude

    Returns:
        list: List of dictionaries containing last week's daily weather data
    """
    try:
        print("Fetching last week's weather data using Open-Meteo API")
        
        # Calculate the date range for the last 7 days (not including today)
        current_date = datetime.now().date()
        past_week_start = (current_date - timedelta(days=7)).isoformat()
        past_week_end = (current_date - timedelta(days=1)).isoformat()
        
        # Prepare to collect data
        result = []
        
        # Get historical temperature data from Open-Meteo API
        # Open-Meteo is a free weather API that doesn't require API keys
        open_meteo_url = "https://archive-api.open-meteo.com/v1/archive"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": past_week_start,
            "end_date": past_week_end,
            "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,relative_humidity_2m_mean",
            "timezone": "auto"
        }
        
        try:
            response = requests.get(open_meteo_url, params=weather_params)
            response.raise_for_status()
            weather_data = response.json()
            
            # Check if we have valid daily data
            if 'daily' in weather_data and 'time' in weather_data['daily']:
                days = weather_data['daily']['time']
                temp_min = weather_data['daily'].get('temperature_2m_min', [])
                temp_max = weather_data['daily'].get('temperature_2m_max', [])
                temp_avg = weather_data['daily'].get('temperature_2m_mean', [])
                humidity = weather_data['daily'].get('relative_humidity_2m_mean', [])
                
                # Create a dictionary to store temperature and humidity data by date
                daily_weather = {}
                for i in range(len(days)):
                    date_key = days[i]
                    daily_weather[date_key] = {
                        'date': date_key,
                        'temp_min': temp_min[i] if i < len(temp_min) else None,
                        'temp_max': temp_max[i] if i < len(temp_max) else None,
                        'temp_avg': temp_avg[i] if i < len(temp_avg) else None,
                        'humidity_avg': humidity[i] if i < len(humidity) else None,
                        'aqi_avg': None  # Will be filled with AQI data
                    }
        except Exception as e:
            print(f"Error fetching historical weather data from Open-Meteo: {str(e)}")
            daily_weather = {}
        
        # Try to get historical AQI data from OpenWeatherMap
        if OPENWEATHER_API_KEY:
            try:
                # Current time as Unix timestamp
                current_time_unix = int(time.time())
                # 8 days ago as Unix timestamp (to include full 7 days)
                start_time_unix = current_time_unix - (8 * 24 * 60 * 60)
                
                # Get AQI data from OpenWeatherMap
                aqi_url = f"{OPENWEATHER_BASE_URL}/air_pollution/history"
                aqi_params = {
                    "lat": lat,
                    "lon": lon,
                    "start": start_time_unix,
                    "end": current_time_unix,
                    "appid": OPENWEATHER_API_KEY
                }
                
                aqi_response = requests.get(aqi_url, params=aqi_params)
                aqi_response.raise_for_status()
                aqi_data = aqi_response.json()
                
                # Process AQI data by day
                if 'list' in aqi_data:
                    # Group AQI values by date
                    aqi_by_date = {}
                    for item in aqi_data['list']:
                        dt = datetime.fromtimestamp(item['dt'])
                        date_key = dt.date().isoformat()
                        
                        if date_key not in aqi_by_date:
                            aqi_by_date[date_key] = []
                        
                        # Calculate AQI from components or use provided AQI
                        if 'components' in item:
                            aqi = calculate_aqi_from_pollutants(item['components'])
                            aqi_by_date[date_key].append(aqi)
                        elif 'main' in item and 'aqi' in item['main']:
                            # Convert 1-5 scale to AQI value
                            aqi = item['main']['aqi'] * 50
                            aqi_by_date[date_key].append(aqi)
                    
                    # Calculate average AQI for each day and add to daily_weather
                    for date_key, aqi_values in aqi_by_date.items():
                        if date_key in daily_weather and aqi_values:
                            daily_weather[date_key]['aqi_avg'] = sum(aqi_values) / len(aqi_values)
            except Exception as e:
                print(f"Error getting AQI data from OpenWeatherMap: {str(e)}")
        
        # Fill in missing AQI values with approximate data
        current_data = get_current_weather_and_aqi(lat, lon)
        current_aqi = current_data.get('aqi', 50) if current_data else 50
        
        for date_key, data in daily_weather.items():
            if data['aqi_avg'] is None:
                # Generate a reasonable AQI value with some daily variation
                data['aqi_avg'] = max(10, min(300, current_aqi + random.uniform(-15, 15)))
        
        # Convert daily_weather dictionary to a list for output
        for date_key, data in daily_weather.items():
            result.append(data)
        
        # If we got no data from Open-Meteo, fill with approximate data
        if not result:
            past_week_dates = []
            for i in range(1, 8):  # 1 to 7 days before today
                past_date = current_date - timedelta(days=i)
                past_week_dates.append(past_date)
            
            # Sort dates in ascending order (oldest to newest)
            past_week_dates.sort()
            
            # Get current weather to use as reference
            current_temp = current_data.get('temperature', 22) if current_data else 22
            current_humidity = current_data.get('humidity', 50) if current_data else 50
            
            # Create approximate data for each day
            for date in past_week_dates:
                date_key = date.isoformat()
                
                # Use current temp with some daily variation
                day_temp = current_temp + random.uniform(-5, 5)
                temp_min = day_temp - random.uniform(3, 7)
                temp_max = day_temp + random.uniform(3, 7)
                
                # Use current humidity with some variation
                humidity = max(10, min(95, current_humidity + random.uniform(-10, 10)))
                
                # Use current AQI with some variation
                aqi = max(10, min(300, current_aqi + random.uniform(-15, 15)))
                
                result.append({
                    'date': date_key,
                    'temp_min': temp_min,
                    'temp_max': temp_max,
                    'temp_avg': day_temp,
                    'humidity_avg': humidity,
                    'aqi_avg': aqi
                })
        
        # Sort results by date to ensure chronological order
        result.sort(key=lambda x: x['date'])
        
        return result
        
    except Exception as e:
        print(f"Error getting last week's historical data: {str(e)}")
        # Return minimal dataset to prevent errors
        current_date = datetime.now().date()
        return [
            {
                'date': (current_date - timedelta(days=i)).isoformat(),
                'temp_min': 15 + random.uniform(-3, 3),
                'temp_max': 25 + random.uniform(-3, 3),
                'temp_avg': 20 + random.uniform(-3, 3),
                'humidity_avg': 50 + random.uniform(-10, 10),
                'aqi_avg': 50 + random.uniform(-10, 10)
            }
            for i in range(1, 8)  # Past 7 days (not including today)
        ]

def get_forecast_data(lat, lon):
    """
    Get 7-day forecast data from OpenWeatherMap API.

    Args:
        lat (float): Latitude
        lon (float): Longitude

    Returns:
        list: List of dictionaries containing forecast data
    """
    try:
        if not OPENWEATHER_API_KEY:
            raise ValueError("OpenWeatherMap API key is missing")

        forecast_url = f"{OPENWEATHER_BASE_URL}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }

        print(f"Fetching forecast data from OpenWeatherMap for location: {lat},{lon}")
        response = requests.get(forecast_url, params=params)
        response.raise_for_status()
        forecast_data = response.json()

        # Get AQI forecast
        aqi_forecast_url = f"{OPENWEATHER_BASE_URL}/air_pollution/forecast"
        aqi_params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY
        }

        print(f"Fetching AQI forecast data from OpenWeatherMap for location: {lat},{lon}")
        aqi_response = requests.get(aqi_forecast_url, params=aqi_params)
        aqi_response.raise_for_status()
        aqi_forecast = aqi_response.json()

        # Process and combine weather and AQI forecasts
        processed_forecast = []
        if 'list' in forecast_data:
            # Group forecasts by day
            daily_forecasts = {}

            for item in forecast_data['list']:
                dt = datetime.fromtimestamp(item['dt'])
                date_key = dt.date()

                if date_key not in daily_forecasts:
                    daily_forecasts[date_key] = {
                        'temps': [],
                        'date': date_key.isoformat(),
                    }

                daily_forecasts[date_key]['temps'].append(item['main']['temp'])

            # Get corresponding AQI data
            for item in aqi_forecast.get('list', []):
                dt = datetime.fromtimestamp(item['dt'])
                date_key = dt.date()

                if date_key in daily_forecasts:
                    components = item.get('components', {})
                    aqi = calculate_aqi_from_pollutants(components)

                    if 'aqi_values' not in daily_forecasts[date_key]:
                        daily_forecasts[date_key]['aqi_values'] = []

                    daily_forecasts[date_key]['aqi_values'].append(aqi)

            # Calculate daily statistics
            for date_key, data in daily_forecasts.items():
                temps = data['temps']
                aqi_values = data.get('aqi_values', [50])  # Default AQI if none available

                processed_forecast.append({
                    'date': data['date'],
                    'temp_min': min(temps),
                    'temp_max': max(temps),
                    'temp_avg': sum(temps) / len(temps),
                    'aqi_min': min(aqi_values),
                    'aqi_max': max(aqi_values),
                    'aqi_avg': sum(aqi_values) / len(aqi_values)
                })

            # Sort by date and limit to 7 days
            processed_forecast.sort(key=lambda x: x['date'])
            processed_forecast = processed_forecast[:7]

        return processed_forecast

    except Exception as e:
        print(f"Error getting forecast data: {str(e)}")
        # Return minimal dataset to prevent errors
        return [
            {
                'date': (datetime.now() + timedelta(days=i)).date().isoformat(),
                'temp_min': 20.0,
                'temp_max': 25.0,
                'temp_avg': 22.5,
                'aqi_min': 45,
                'aqi_max': 55,
                'aqi_avg': 50
            }
            for i in range(7)
        ]
