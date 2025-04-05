import requests
import os

def get_coordinates(city, state, country):
    """
    Get coordinates (latitude, longitude) for a location using OpenStreetMap Nominatim API.
    
    Args:
        city (str): City name
        state (str): State or province
        country (str): Country name
        
    Returns:
        dict: Dictionary with lat and lng keys
    """
    try:
        # Build a query string from provided location components
        query_parts = []
        if city:
            query_parts.append(city)
        if state:
            query_parts.append(state)
        if country:
            query_parts.append(country)
        
        query = ", ".join(query_parts)
        
        # Call Nominatim API
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "WeatherHealthApp/1.0"  # Required by Nominatim
        }
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()   #error
        
        data = response.json()
        if data and len(data) > 0:
            return {
                "lat": float(data[0]["lat"]),
                "lng": float(data[0]["lon"])
            }
        else:
            return None
            
    except Exception as e:
        print(f"Error getting coordinates: {str(e)}")
        return None

def celsius_to_fahrenheit(celsius):
    """
    Convert temperature from Celsius to Fahrenheit.
    
    Args:
        celsius (float): Temperature in Celsius
        
    Returns:
        float: Temperature in Fahrenheit
    """
    return (celsius * 9/5) + 32

def get_aqi_label(aqi):
    """
    Get descriptive label for AQI value.
    
    Args:
        aqi (float): Air Quality Index value
        
    Returns:
        str: AQI category label
    """
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

def get_aqi_color(aqi):
    """
    Get color representation for AQI value.
    
    Args:
        aqi (float): Air Quality Index value
        
    Returns:
        str: Hex color code
    """
    if aqi <= 50:
        return "#00e400"  # Green
    elif aqi <= 100:
        return "#ffff00"  # Yellow
    elif aqi <= 150:
        return "#ff7e00"  # Orange
    elif aqi <= 200:
        return "#ff0000"  # Red
    elif aqi <= 300:
        return "#99004c"  # Purple
    else:
        return "#7e0023"  # Maroon
