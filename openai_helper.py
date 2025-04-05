import os
import json
from openai import OpenAI
import time

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
try:
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception as e:
    print(f"Error initializing OpenAI client: {str(e)}")
    client = None

def get_health_recommendations(location, temperature_c, aqi):
    """
    Get health recommendations based on location, temperature, and AQI.
    If OpenAI API is not available, falls back to rule-based recommendations.
    
    Args:
        location (str): User's location (City, State, Country)
        temperature_c (float): Current temperature in Celsius
        aqi (float): Current Air Quality Index
        
    Returns:
        str: Health recommendations
    """
    # Ensure we have valid input values
    if temperature_c is None:
        temperature_c = 22.0  # Default comfortable temperature
    if aqi is None:
        aqi = 50.0  # Default moderate AQI
        
    # Try to use OpenAI for personalized recommendations
    if client and OPENAI_API_KEY:
        try:
            # Convert temperature to Fahrenheit for reference
            temperature_f = (temperature_c * 9/5) + 32
            
            # Create a prompt for OpenAI
            prompt = f"""
            Generate health recommendations based on the following weather and air quality data:
            
            Location: {location}
            Current Temperature: {temperature_c:.1f}°C ({temperature_f:.1f}°F)
            Air Quality Index (AQI): {aqi}
            
            Provide detailed health recommendations considering:
            1. Temperature-related precautions (heat or cold)
            2. Air quality impact on health
            3. Suitable outdoor activities
            4. Special considerations for sensitive groups (children, elderly, people with respiratory conditions)
            5. Hydration and clothing recommendations
            
            Format your response as a well-structured Markdown text with clear sections and bullet points.
            """
            
            # Set retry parameters
            max_retries = 2
            retry_delay = 1
            retries = 0
            
            while retries <= max_retries:
                try:
                    # Call OpenAI API
                    # Using GPT-4o as it's the latest and most capable model
                    response = client.chat.completions.create(
                        model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                        messages=[
                            {"role": "system", "content": "You are a health advisor specializing in environmental health. Provide accurate, helpful health recommendations based on weather and air quality data."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=500
                    )
                    
                    # Extract and return the response
                    return response.choices[0].message.content
                
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        print(f"Error generating health recommendations after {max_retries} retries: {str(e)}")
                        break
                    time.sleep(retry_delay)
        except Exception as e:
            print(f"Error with OpenAI API: {str(e)}")
    
    # Fallback to rule-based recommendations if OpenAI is not available or has errors
    return generate_rule_based_recommendations(location, temperature_c, aqi)

def generate_rule_based_recommendations(location, temperature_c, aqi):
    """
    Generate rule-based health recommendations based on temperature and AQI.
    
    Args:
        location (str): User's location (City, State, Country)
        temperature_c (float): Current temperature in Celsius
        aqi (float): Current Air Quality Index
        
    Returns:
        str: Health recommendations
    """
    temperature_f = (temperature_c * 9/5) + 32
    
    # Temperature categories
    if temperature_c >= 35:
        temp_category = "extreme_heat"
    elif temperature_c >= 30:
        temp_category = "high_heat"
    elif temperature_c >= 25:
        temp_category = "warm"
    elif temperature_c >= 15:
        temp_category = "moderate"
    elif temperature_c >= 5:
        temp_category = "cool"
    elif temperature_c >= -5:
        temp_category = "cold"
    else:
        temp_category = "extreme_cold"
    
    # AQI categories
    if aqi <= 50:
        aqi_category = "good"
    elif aqi <= 100:
        aqi_category = "moderate"
    elif aqi <= 150:
        aqi_category = "unhealthy_sensitive"
    elif aqi <= 200:
        aqi_category = "unhealthy"
    elif aqi <= 300:
        aqi_category = "very_unhealthy"
    else:
        aqi_category = "hazardous"
    
    # Temperature recommendations
    temp_recommendations = {
        "extreme_heat": """
## Temperature Precautions (Extreme Heat)

* **Stay hydrated**: Drink water constantly throughout the day, even if you don't feel thirsty
* **Avoid outdoor activities**: Especially between 10 AM and 4 PM
* **Use cooling systems**: Stay in air-conditioned areas when possible
* **Wear lightweight clothing**: Choose light-colored, loose-fitting clothes
* **Take cool showers**: Consider multiple showers throughout the day
* **Check on vulnerable people**: Elderly, children, and those with health conditions are at higher risk
* **Never leave people or pets in parked vehicles**: Car temperatures can rise dangerously in minutes
        """,
        "high_heat": """
## Temperature Precautions (High Heat)

* **Stay hydrated**: Drink at least 8-10 glasses of water daily
* **Limit outdoor activities**: Consider indoor options during the hottest parts of the day
* **Wear appropriate clothing**: Light-colored, loose-fitting clothes are best
* **Use sun protection**: Apply sunscreen, wear a hat and sunglasses
* **Take breaks**: If working outdoors, take frequent breaks in shaded areas
        """,
        "warm": """
## Temperature Precautions (Warm Weather)

* **Stay hydrated**: Maintain regular water intake throughout the day
* **Dress comfortably**: Light clothing appropriate for warm conditions
* **Protect from sun**: Use sunscreen when spending extended time outdoors
* **Enjoy outdoor activities**: The weather is suitable for most outdoor activities
        """,
        "moderate": """
## Temperature Precautions (Moderate Weather)

* **Dress in layers**: Weather is comfortable but may change throughout the day
* **Stay hydrated**: Continue regular water intake
* **Enjoy outdoor activities**: Ideal conditions for most outdoor pursuits
        """,
        "cool": """
## Temperature Precautions (Cool Weather)

* **Dress in layers**: Wear a light jacket or sweater
* **Stay hydrated**: Even in cool weather, hydration remains important
* **Suitable for activity**: Excellent conditions for physical activity outdoors
        """,
        "cold": """
## Temperature Precautions (Cold Weather)

* **Dress warmly**: Wear insulated clothing, gloves, hat, and scarf
* **Layer clothing**: Multiple layers provide better insulation
* **Stay dry**: Wet clothing can lead to heat loss
* **Maintain hydration**: Continue drinking water regularly
* **Limit exposure**: Take breaks indoors when spending extended time outside
        """,
        "extreme_cold": """
## Temperature Precautions (Extreme Cold)

* **Limit outdoor exposure**: Minimize time spent outdoors
* **Dress in multiple layers**: Include thermal base layers and windproof outer layers
* **Cover extremities**: Wear insulated gloves, thick socks, hat, and face covering
* **Stay dry**: Avoid getting clothing wet, as this dramatically increases heat loss
* **Watch for signs of hypothermia**: Shivering, confusion, drowsiness
* **Check on vulnerable people**: Elderly and those with health conditions need extra attention
* **Keep emergency supplies**: Have blankets and heating sources available
        """
    }
    
    # AQI recommendations
    aqi_recommendations = {
        "good": """
## Air Quality Recommendations (Good)

* **Enjoy outdoor activities**: Air quality is good for everyone
* **No restrictions needed**: All usual outdoor activities are appropriate
* **Ventilate your home**: Opening windows is beneficial
        """,
        "moderate": """
## Air Quality Recommendations (Moderate)

* **Generally safe for most**: Air quality is acceptable for most people
* **Sensitive individuals**: People with unusual sensitivity to air pollution should consider reducing prolonged outdoor exertion
* **Ventilation**: Still generally acceptable to ventilate home
        """,
        "unhealthy_sensitive": """
## Air Quality Recommendations (Unhealthy for Sensitive Groups)

* **At-risk groups**: People with heart or lung disease, older adults, children, and teenagers should reduce prolonged or heavy outdoor exertion
* **Everyone else**: It's OK to be active outside, but take more breaks and do less intense activities
* **Watch for symptoms**: Unusual coughing, shortness of breath, or fatigue
* **Indoor air**: Consider using air purifiers indoors and keep windows closed
        """,
        "unhealthy": """
## Air Quality Recommendations (Unhealthy)

* **Limit outdoor activities**: Everyone should reduce prolonged or heavy exertion
* **Move activities indoors**: Consider rescheduling outdoor events
* **Sensitive groups**: People with respiratory or heart conditions, children, and elderly should avoid all outdoor physical activities
* **Use masks**: Consider wearing N95/KN95 masks when outdoors
* **Indoor air quality**: Keep windows closed and use air purifiers if available
        """,
        "very_unhealthy": """
## Air Quality Recommendations (Very Unhealthy)

* **Avoid outdoor activities**: Everyone should avoid all outdoor physical activities
* **Stay indoors**: Keep windows and doors closed
* **Use air purifiers**: Run HEPA air purifiers if available
* **Wear masks**: Use N95/KN95 masks if you must go outside
* **Check local advisories**: Follow any evacuation orders or health advisories
* **Sensitive groups**: People with heart or respiratory conditions may need to take additional precautions
        """,
        "hazardous": """
## Air Quality Recommendations (Hazardous)

* **Health emergency**: Air quality is at emergency conditions
* **Stay indoors**: Remain indoors with windows and doors closed
* **Limit all exertion**: Even indoor physical activity should be kept to a minimum
* **Use air purifiers**: Run HEPA air purifiers continuously
* **Wear masks**: Use N95/KN95 masks even indoors in buildings with poor filtration
* **Consider relocation**: If possible, temporarily relocate to an area with better air quality
* **Check for emergency alerts**: Follow all local emergency instructions
        """
    }
    
    # Put together the full recommendation
    recommendations = f"""
# Health Recommendations for {location}

Current conditions: **{temperature_c:.1f}°C ({temperature_f:.1f}°F)** with Air Quality Index of **{aqi}**

{temp_recommendations[temp_category]}

{aqi_recommendations[aqi_category]}

## General Health Recommendations

* **Stay informed**: Monitor local weather and air quality forecasts
* **Pre-existing conditions**: Consult your healthcare provider for personalized advice if you have medical conditions
* **Adjust activities**: Plan your outdoor activities based on weather and air quality conditions
* **Emergency preparedness**: Know the signs of heat-related illness and respiratory distress

*These recommendations are general guidelines based on current conditions. Individual needs may vary.*
    """
    
    return recommendations
