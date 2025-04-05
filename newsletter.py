import os
import pandas as pd
from datetime import datetime, timedelta
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content, MimeType
from apscheduler.schedulers.background import BackgroundScheduler

import weather_api as weather
import data_utils as utils
import database as db

# SendGrid API key from environment variables
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "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")
FROM_EMAIL = os.getenv("FROM_EMAIL", "uttaretejas@gmail.com")

# List of major cities in India for weather tracking
INDIA_CITIES = [
    {"city": "Mumbai", "state": "Maharashtra", "country": "India"},
    {"city": "Delhi", "state": "Delhi", "country": "India"},
    {"city": "Bangalore", "state": "Karnataka", "country": "India"},
    {"city": "Hyderabad", "state": "Telangana", "country": "India"},
    {"city": "Chennai", "state": "Tamil Nadu", "country": "India"},
    {"city": "Kolkata", "state": "West Bengal", "country": "India"},
    {"city": "Pune", "state": "Maharashtra", "country": "India"},
    {"city": "Ahmedabad", "state": "Gujarat", "country": "India"},
    {"city": "Jaipur", "state": "Rajasthan", "country": "India"},
    {"city": "Lucknow", "state": "Uttar Pradesh", "country": "India"}
]

# List of major global cities for weather tracking
GLOBAL_CITIES = [
    {"city": "New York", "state": "NY", "country": "United States"},
    {"city": "London", "state": "", "country": "United Kingdom"},
    {"city": "Tokyo", "state": "", "country": "Japan"},
    {"city": "Paris", "state": "", "country": "France"},
    {"city": "Sydney", "state": "NSW", "country": "Australia"},
    {"city": "Dubai", "state": "", "country": "United Arab Emirates"},
    {"city": "Singapore", "state": "", "country": "Singapore"},
    {"city": "Toronto", "state": "Ontario", "country": "Canada"}
]

def get_weather_forecast_for_cities(cities_list):
    """
    Get weather forecast data for a list of cities
    
    Args:
        cities_list (list): List of dictionaries with city, state, country keys
        
    Returns:
        dict: Dictionary with city names as keys and weather data as values
    """
    result = {}
    
    for city_info in cities_list:
        try:
            # Get coordinates
            coordinates = utils.get_coordinates(
                city_info["city"], 
                city_info["state"], 
                city_info["country"]
            )
            
            if coordinates:
                # Get current weather
                current = weather.get_current_weather_and_aqi(
                    coordinates["lat"], 
                    coordinates["lng"]
                )
                
                # Get forecast for the next 7 days
                forecast = weather.get_forecast_data(
                    coordinates["lat"], 
                    coordinates["lng"]
                )
                
                # Save data
                city_name = f"{city_info['city']}, {city_info['state']}, {city_info['country']}".replace(", ,", ",")
                result[city_name] = {
                    "current": current,
                    "forecast": forecast
                }
        except Exception as e:
            print(f"Error getting weather for {city_info['city']}: {str(e)}")
    
    return result

def generate_india_weather_summary(india_data):
    """
    Generate summary of weather across India
    
    Args:
        india_data (dict): Weather data for Indian cities
        
    Returns:
        dict: Dictionary with summary information
    """
    if not india_data:
        return None
    
    # Extract current temperatures
    temperatures = []
    aqi_values = []
    
    for city, data in india_data.items():
        current = data.get("current", {})
        if current:
            temp = current.get("temperature")
            aqi = current.get("aqi")
            if temp is not None:
                temperatures.append({
                    "city": city,
                    "temperature": temp
                })
            if aqi is not None:
                aqi_values.append({
                    "city": city,
                    "aqi": aqi
                })
    
    # Find highest and lowest temperatures
    highest_temp = max(temperatures, key=lambda x: x["temperature"]) if temperatures else None
    lowest_temp = min(temperatures, key=lambda x: x["temperature"]) if temperatures else None
    
    # Find best and worst AQI
    best_aqi = min(aqi_values, key=lambda x: x["aqi"]) if aqi_values else None
    worst_aqi = max(aqi_values, key=lambda x: x["aqi"]) if aqi_values else None
    
    return {
        "highest_temp": highest_temp,
        "lowest_temp": lowest_temp,
        "best_aqi": best_aqi,
        "worst_aqi": worst_aqi
    }

def generate_global_weather_summary(global_data):
    """
    Generate summary of weather around the world
    
    Args:
        global_data (dict): Weather data for global cities
        
    Returns:
        dict: Dictionary with summary information
    """
    return generate_india_weather_summary(global_data)  # Same logic applies

def generate_html_email_content(subscriber, india_data, global_data):
    """
    Generate HTML content for email newsletter
    
    Args:
        subscriber (Subscriber): Subscriber object from database
        india_data (dict): Weather data for Indian cities
        global_data (dict): Weather data for global cities
        
    Returns:
        str: HTML content for email
    """
    # Get summaries
    india_summary = generate_india_weather_summary(india_data)
    global_summary = generate_global_weather_summary(global_data)
    
    # Generate date strings
    today = datetime.now()
    week_end = (today + timedelta(days=6)).strftime('%B %d, %Y')
    today_str = today.strftime('%B %d, %Y')
    
    # Start building HTML content
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weather & Health Advisor - Weekly Update</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #3498db;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 15px;
                text-align: center;
                font-size: 12px;
                border-radius: 0 0 5px 5px;
                margin-top: 20px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .highlight {{
                background-color: #ffffcc;
                padding: 10px;
                border-radius: 5px;
                margin: 15px 0;
            }}
            .temperature {{
                color: #e74c3c;
            }}
            .aqi {{
                color: #27ae60;
            }}
            .unsubscribe {{
                color: #7f8c8d;
                font-size: 12px;
            }}
            .city-section {{
                margin-bottom: 30px;
                border-bottom: 1px solid #eee;
                padding-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Weather & Health Advisor</h1>
            <p>Weekly Weather Update: {today_str} - {week_end}</p>
        </div>
        
        <p>Hello {subscriber.name},</p>
        
        <p>Here's your weekly weather update with forecasts, air quality information, and health insights for the coming week.</p>
    """
    
    # Add India weather highlights
    if india_summary:
        html += """
        <h2>📍 Weather Highlights Across India</h2>
        <div class="highlight">
        """
        
        if india_summary.get("highest_temp"):
            html += f"""
            <p>🔥 <strong>Highest Temperature:</strong> 
               <span class="temperature">{india_summary["highest_temp"]["temperature"]:.1f}°C</span> in 
               {india_summary["highest_temp"]["city"].split(",")[0]}
            </p>
            """
            
        if india_summary.get("lowest_temp"):
            html += f"""
            <p>❄️ <strong>Lowest Temperature:</strong> 
               <span class="temperature">{india_summary["lowest_temp"]["temperature"]:.1f}°C</span> in 
               {india_summary["lowest_temp"]["city"].split(",")[0]}
            </p>
            """
            
        if india_summary.get("best_aqi"):
            html += f"""
            <p>🌱 <strong>Best Air Quality:</strong> 
               <span class="aqi">AQI {india_summary["best_aqi"]["aqi"]:.1f}</span> in 
               {india_summary["best_aqi"]["city"].split(",")[0]}
            </p>
            """
            
        if india_summary.get("worst_aqi"):
            html += f"""
            <p>🧪 <strong>Poorest Air Quality:</strong> 
               <span class="aqi">AQI {india_summary["worst_aqi"]["aqi"]:.1f}</span> in 
               {india_summary["worst_aqi"]["city"].split(",")[0]}
            </p>
            """
            
        html += """
        </div>
        """
    
    # Add Global weather highlights
    if global_summary:
        html += """
        <h2>🌎 Global Weather Highlights</h2>
        <div class="highlight">
        """
        
        if global_summary.get("highest_temp"):
            html += f"""
            <p>🔥 <strong>Highest Temperature:</strong> 
               <span class="temperature">{global_summary["highest_temp"]["temperature"]:.1f}°C</span> in 
               {global_summary["highest_temp"]["city"].split(",")[0]}
            </p>
            """
            
        if global_summary.get("lowest_temp"):
            html += f"""
            <p>❄️ <strong>Lowest Temperature:</strong> 
               <span class="temperature">{global_summary["lowest_temp"]["temperature"]:.1f}°C</span> in 
               {global_summary["lowest_temp"]["city"].split(",")[0]}
            </p>
            """
            
        if global_summary.get("best_aqi"):
            html += f"""
            <p>🌱 <strong>Best Air Quality:</strong> 
               <span class="aqi">AQI {global_summary["best_aqi"]["aqi"]:.1f}</span> in 
               {global_summary["best_aqi"]["city"].split(",")[0]}
            </p>
            """
            
        if global_summary.get("worst_aqi"):
            html += f"""
            <p>🧪 <strong>Poorest Air Quality:</strong> 
               <span class="aqi">AQI {global_summary["worst_aqi"]["aqi"]:.1f}</span> in 
               {global_summary["worst_aqi"]["city"].split(",")[0]}
            </p>
            """
            
        html += """
        </div>
        """
    
    # Add subscriber's location weather if available
    if subscriber.location_city and subscriber.location_state and subscriber.location_country:
        try:
            subscriber_location = f"{subscriber.location_city}, {subscriber.location_state}, {subscriber.location_country}".replace(", ,", ",")
            coordinates = utils.get_coordinates(
                subscriber.location_city,
                subscriber.location_state,
                subscriber.location_country
            )
            
            if coordinates:
                current = weather.get_current_weather_and_aqi(
                    coordinates["lat"], 
                    coordinates["lng"]
                )
                
                forecast = weather.get_forecast_data(
                    coordinates["lat"], 
                    coordinates["lng"]
                )
                
                html += f"""
                <h2>📌 Weather for Your Location: {subscriber_location}</h2>
                
                <h3>Current Conditions</h3>
                <p>
                    Temperature: <span class="temperature">{current.get('temperature', 'N/A'):.1f}°C</span><br>
                    Humidity: {current.get('humidity', 'N/A'):.1f}%<br>
                    Wind Speed: {current.get('wind_speed', 'N/A'):.1f} m/s<br>
                    Air Quality Index: <span class="aqi">{current.get('aqi', 'N/A'):.1f}</span> 
                    ({utils.get_aqi_label(current.get('aqi', 0))})
                </p>
                
                <h3>7-Day Forecast</h3>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Min Temp (°C)</th>
                        <th>Max Temp (°C)</th>
                        <th>Avg Temp (°C)</th>
                        <th>AQI</th>
                    </tr>
                """
                
                for day in forecast:
                    date_obj = datetime.fromisoformat(day['date']).strftime('%a, %b %d')
                    html += f"""
                    <tr>
                        <td>{date_obj}</td>
                        <td>{day['temp_min']:.1f}</td>
                        <td>{day['temp_max']:.1f}</td>
                        <td>{day['temp_avg']:.1f}</td>
                        <td>{day['aqi_avg']:.1f}</td>
                    </tr>
                    """
                
                html += """
                </table>
                """
        except Exception as e:
            print(f"Error generating subscriber location forecast: {str(e)}")
    
    # Add detailed city forecasts for India
    html += """
    <h2>📊 Detailed Forecasts - Major Cities in India</h2>
    """
    
    # Display data for each Indian city
    for city_name, data in india_data.items():
        short_city_name = city_name.split(",")[0]
        current = data.get("current", {})
        forecast = data.get("forecast", [])
        
        if current and forecast:
            html += f"""
            <div class="city-section">
                <h3>{short_city_name}</h3>
                <p>
                    Current Temperature: <span class="temperature">{current.get('temperature', 'N/A'):.1f}°C</span><br>
                    Current AQI: <span class="aqi">{current.get('aqi', 'N/A'):.1f}</span> 
                    ({utils.get_aqi_label(current.get('aqi', 0))})
                </p>
                
                <h4>Weekly Temperature Range</h4>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Min (°C)</th>
                        <th>Max (°C)</th>
                    </tr>
            """
            
            for day in forecast[:5]:  # Show only next 5 days to keep email compact
                date_obj = datetime.fromisoformat(day['date']).strftime('%a, %b %d')
                html += f"""
                <tr>
                    <td>{date_obj}</td>
                    <td>{day['temp_min']:.1f}</td>
                    <td>{day['temp_max']:.1f}</td>
                </tr>
                """
            
            html += """
                </table>
            </div>
            """
    
    # Add global city highlights (compact version)
    html += """
    <h2>🌍 Global Weather Snapshot</h2>
    <table>
        <tr>
            <th>City</th>
            <th>Current Temp (°C)</th>
            <th>AQI</th>
            <th>Weekly High (°C)</th>
            <th>Weekly Low (°C)</th>
        </tr>
    """
    
    for city_name, data in global_data.items():
        short_city_name = city_name.split(",")[0]
        current = data.get("current", {})
        forecast = data.get("forecast", [])
        
        if current and forecast:
            # Find weekly high and low
            weekly_high = max([day['temp_max'] for day in forecast]) if forecast else "N/A"
            weekly_low = min([day['temp_min'] for day in forecast]) if forecast else "N/A"
            
            html += f"""
            <tr>
                <td>{short_city_name}</td>
                <td>{current.get('temperature', 'N/A'):.1f}</td>
                <td>{current.get('aqi', 'N/A'):.1f}</td>
                <td>{weekly_high if weekly_high == 'N/A' else f'{weekly_high:.1f}'}</td>
                <td>{weekly_low if weekly_low == 'N/A' else f'{weekly_low:.1f}'}</td>
            </tr>
            """
    
    html += """
    </table>
    """
    
    # Add footer and unsubscribe link
    html += f"""
        <div class="footer">
            <p>This newsletter is sent weekly to provide you with weather updates and health recommendations.</p>
            <p class="unsubscribe">
                If you wish to unsubscribe, <a href="https://your-app-url.com/unsubscribe?email={subscriber.email}">click here</a>.
            </p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_newsletter_to_subscriber(subscriber):
    """
    Generate and send newsletter to a single subscriber
    
    Args:
        subscriber (Subscriber): Subscriber database object
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not SENDGRID_API_KEY:
        print("SendGrid API key is missing. Cannot send newsletter.")
        return False
    
    try:
        # Get weather data for Indian cities
        india_data = get_weather_forecast_for_cities(INDIA_CITIES)
        
        # Get weather data for global cities
        global_data = get_weather_forecast_for_cities(GLOBAL_CITIES)
        
        # Generate email content
        html_content = generate_html_email_content(subscriber, india_data, global_data)
        
        # Configure email
        from_email = Email(FROM_EMAIL)
        to_email = To(subscriber.email)
        subject = f"Your Weekly Weather Update - {datetime.now().strftime('%B %d, %Y')}"
        content = Content(MimeType.html, html_content)
        
        mail = Mail(from_email, to_email, subject, content)
        
        # Send email
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        response = sg.client.mail.send.post(request_body=mail.get())
        
        if response.status_code >= 200 and response.status_code < 300:
            # Update last email sent timestamp
            db.update_last_email_sent(subscriber.email)
            print(f"Newsletter sent to {subscriber.email}")
            return True
        else:
            print(f"Failed to send newsletter to {subscriber.email}: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"Error sending newsletter to {subscriber.email}: {str(e)}")
        return False

def send_newsletters():
    """Send newsletters to all active subscribers"""
    if not SENDGRID_API_KEY:
        print("SendGrid API key is missing. Skipping newsletter sending.")
        return
    
    print(f"Starting newsletter sending job at {datetime.now()}")
    subscribers = db.get_active_subscribers()
    
    for subscriber in subscribers:
        try:
            send_newsletter_to_subscriber(subscriber)
        except Exception as e:
            print(f"Error processing subscriber {subscriber.email}: {str(e)}")
    
    print(f"Completed newsletter sending job at {datetime.now()}")

# Initialize scheduler
scheduler = BackgroundScheduler()

def start_scheduler():
    """Start the newsletter scheduler"""
    try:
        # Only add the job if scheduler is not already running
        if not scheduler.running:
            # Schedule to run weekly on Sunday at 8 AM
            scheduler.add_job(send_newsletters, 'cron', day_of_week='sun', hour=8)
            scheduler.start()
            print("Newsletter scheduler started")
        else:
            print("Newsletter scheduler is already running")
    except Exception as e:
        print(f"Error starting scheduler: {str(e)}")

def stop_scheduler():
    """Stop the newsletter scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            print("Newsletter scheduler stopped")
    except Exception as e:
        print(f"Error stopping scheduler: {str(e)}")

def get_previous_week_report():
    """
    Generate a summary of the previous week's weather data for the welcome email
    
    Returns:
        dict: Dictionary with previous week's weather summary
    """
    # Define the cities to include in the report
    india_cities = [
        {"city": "Mumbai", "state": "Maharashtra", "country": "India"},
        {"city": "Delhi", "state": "Delhi", "country": "India"},
        {"city": "Bangalore", "state": "Karnataka", "country": "India"},
        {"city": "Chennai", "state": "Tamil Nadu", "country": "India"},
        {"city": "Kolkata", "state": "West Bengal", "country": "India"},
    ]
    
    global_cities = [
        {"city": "New York", "state": "NY", "country": "USA"},
        {"city": "London", "state": "", "country": "UK"},
        {"city": "Tokyo", "state": "", "country": "Japan"},
        {"city": "Sydney", "state": "", "country": "Australia"},
        {"city": "Paris", "state": "", "country": "France"},
    ]
    
    # Get data for these cities
    india_data = get_weather_forecast_for_cities(india_cities)
    global_data = get_weather_forecast_for_cities(global_cities)
    
    # Add overview field to summaries for the welcome email
    india_summary = generate_india_weather_summary(india_data)
    if india_summary:
        india_summary["overview"] = "Latest weather conditions across major Indian cities."
    else:
        india_summary = {
            "overview": "Weather data for India is currently unavailable.",
            "highest_temp": None,
            "lowest_temp": None,
            "best_aqi": None, 
            "worst_aqi": None
        }
    
    global_summary = generate_global_weather_summary(global_data)
    if global_summary:
        global_summary["overview"] = "Current weather conditions in major cities around the world."
    else:
        global_summary = {
            "overview": "Global weather data is currently unavailable.",
            "highest_temp": None,
            "lowest_temp": None,
            "best_aqi": None,
            "worst_aqi": None
        }
    
    # For display in the welcome email
    processed_india_data = {}
    for city, data in india_data.items():
        if city and data and data.get("current"):
            processed_india_data[city] = {
                "temperature": data["current"].get("temperature", 0),
                "aqi": data["current"].get("aqi", 0),
                "conditions": "Partly Cloudy"
            }
    
    processed_global_data = {}
    for city, data in global_data.items():
        if city and data and data.get("current"):
            processed_global_data[city] = {
                "temperature": data["current"].get("temperature", 0),
                "aqi": data["current"].get("aqi", 0),
                "conditions": "Partly Cloudy"
            }
    
    # Create summary data
    temp_values_india = [data["temperature"] for city, data in processed_india_data.items() if "temperature" in data]
    aqi_values_india = [data["aqi"] for city, data in processed_india_data.items() if "aqi" in data]
    
    temp_values_global = [data["temperature"] for city, data in processed_global_data.items() if "temperature" in data]
    aqi_values_global = [data["aqi"] for city, data in processed_global_data.items() if "aqi" in data]
    
    # Create temperature and AQI range strings for welcome email
    if temp_values_india:
        india_summary["temp_range"] = f"{min(temp_values_india):.1f}°C to {max(temp_values_india):.1f}°C"
    else:
        india_summary["temp_range"] = "Data unavailable"
        
    if aqi_values_india:
        india_summary["aqi_range"] = f"{min(aqi_values_india):.0f} to {max(aqi_values_india):.0f}"
    else:
        india_summary["aqi_range"] = "Data unavailable"
        
    if temp_values_global:
        global_summary["temp_range"] = f"{min(temp_values_global):.1f}°C to {max(temp_values_global):.1f}°C"
    else:
        global_summary["temp_range"] = "Data unavailable"
        
    if aqi_values_global:
        global_summary["aqi_range"] = f"{min(aqi_values_global):.0f} to {max(aqi_values_global):.0f}"
    else:
        global_summary["aqi_range"] = "Data unavailable"
    
    return {
        "india_data": processed_india_data,
        "global_data": processed_global_data,
        "india_summary": india_summary,
        "global_summary": global_summary,
        "date": datetime.now().strftime("%d %B, %Y")
    }


def send_welcome_email(subscriber):
    """
    Send a welcome email to a new subscriber with previous week's weather data
    
    Args:
        subscriber (Subscriber): Subscriber database object
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    global SENDGRID_API_KEY, FROM_EMAIL
    
    # Check if environmental variables are properly set
    if not SENDGRID_API_KEY:
        print("SendGrid API key is missing. Cannot send welcome email.")
        return False
        
    if not FROM_EMAIL:
        print("FROM_EMAIL is not configured. Cannot send welcome email.")
        return False
    
    try:
        # First, get previous week's weather report data
        print(f"Generating previous week's weather report for welcome email to {subscriber.email}")
        try:
            weather_report = get_previous_week_report()
        except Exception as e:
            print(f"Error generating weather report, using fallback data: {str(e)}")
            # Create fallback data to ensure email still works
            weather_report = {
                "india_data": {},
                "global_data": {},
                "india_summary": {
                    "overview": "Weather data for India is currently being updated.",
                    "temp_range": "Data unavailable",
                    "aqi_range": "Data unavailable"
                },
                "global_summary": {
                    "overview": "Global weather data is currently being updated.",
                    "temp_range": "Data unavailable",
                    "aqi_range": "Data unavailable"
                },
                "date": datetime.now().strftime("%d %B, %Y")
            }
        
        # Configure email
        from_email = Email(FROM_EMAIL)
        to_email = To(subscriber.email)
        subject = "Welcome to IcoHealth Weather Newsletter!"
        
        # Generate HTML content for welcome email with previous week's data
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to IcoHealth Weather Newsletter</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #3498db;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    padding: 20px;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    text-align: center;
                    font-size: 12px;
                    border-radius: 0 0 5px 5px;
                    margin-top: 20px;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                .highlight {{
                    background-color: #ffffcc;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .unsubscribe {{
                    color: #7f8c8d;
                    font-size: 12px;
                }}
                .weather-section {{
                    background-color: #f1f9fe;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .weather-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                .weather-table th, .weather-table td {{
                    padding: 8px;
                    border-bottom: 1px solid #ddd;
                    text-align: left;
                }}
                .weather-table th {{
                    background-color: #3498db;
                    color: white;
                }}
                .weather-table tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>IcoHealth Weather Newsletter</h1>
                <p>Weather Report: {weather_report["date"]}</p>
            </div>
            
            <div class="content">
                <h2>Welcome, {subscriber.name}!</h2>
                
                <p>Thank you for subscribing to our weekly weather newsletter. You're now part of our community that receives personalized weather insights and health recommendations.</p>
                
                <div class="highlight">
                    <h3>What to Expect:</h3>
                    <ul>
                        <li>📅 <strong>Weekly Delivery:</strong> Every Sunday at 8 AM</li>
                        <li>🌡️ <strong>Personalized Weather:</strong> Forecast for your location ({subscriber.location_city if subscriber.location_city else "your area"})</li>
                        <li>🏙️ <strong>City Updates:</strong> Weather trends for major cities in India</li>
                        <li>🌎 <strong>Global Insights:</strong> Temperature and AQI information from around the world</li>
                        <li>🧠 <strong>Health Tips:</strong> Personalized recommendations based on your local weather conditions</li>
                    </ul>
                </div>
                
                <p>Here's a sample of our weekly weather insights to get you started:</p>
                
                <!-- India Weather Section -->
                <div class="weather-section">
                    <h3>🇮🇳 India Weather Highlights</h3>
                    <p><strong>Summary:</strong> {weather_report["india_summary"]["overview"]}</p>
                    
                    <table class="weather-table">
                        <tr>
                            <th>City</th>
                            <th>Temp (°C)</th>
                            <th>AQI</th>
                            <th>Conditions</th>
                        </tr>
        """
        
        # Add India cities data
        for city, data in weather_report["india_data"].items():
            if data.get("temperature") is not None:
                html_content += f"""
                        <tr>
                            <td>{city}</td>
                            <td>{data.get("temperature"):.1f}°C</td>
                            <td>{data.get("aqi"):.0f}</td>
                            <td>{data.get("conditions", "Partly Cloudy")}</td>
                        </tr>
                """
        
        html_content += f"""
                    </table>
                    
                    <p><strong>Temperature Range:</strong> {weather_report["india_summary"]["temp_range"]}</p>
                    <p><strong>AQI Range:</strong> {weather_report["india_summary"]["aqi_range"]}</p>
                </div>
                
                <!-- Global Weather Section -->
                <div class="weather-section">
                    <h3>🌎 Global Weather Highlights</h3>
                    <p><strong>Summary:</strong> {weather_report["global_summary"]["overview"]}</p>
                    
                    <table class="weather-table">
                        <tr>
                            <th>City</th>
                            <th>Temp (°C)</th>
                            <th>AQI</th>
                            <th>Conditions</th>
                        </tr>
        """
        
        # Add Global cities data
        for city, data in weather_report["global_data"].items():
            if data.get("temperature") is not None:
                html_content += f"""
                        <tr>
                            <td>{city}</td>
                            <td>{data.get("temperature"):.1f}°C</td>
                            <td>{data.get("aqi"):.0f}</td>
                            <td>{data.get("conditions", "Partly Cloudy")}</td>
                        </tr>
                """
        
        html_content += f"""
                    </table>
                    
                    <p><strong>Temperature Range:</strong> {weather_report["global_summary"]["temp_range"]}</p>
                    <p><strong>AQI Range:</strong> {weather_report["global_summary"]["aqi_range"]}</p>
                </div>
                
                <p>Your next newsletter will be delivered this Sunday at 8 AM. We're excited to help you stay informed about weather patterns and make health-conscious decisions based on environmental conditions.</p>
                
                <p>If you have any questions or feedback, feel free to reply to this email.</p>
                
                <p>Stay healthy and weather-wise!</p>
                
                <p>The IcoHealth Team</p>
            </div>
            
            <div class="footer">
                <p>This is an automated message from IcoHealth Weather & Health Advisor.</p>
                <p class="unsubscribe">
                    If you wish to unsubscribe, <a href="https://your-app-url.com/unsubscribe?email={subscriber.email}">click here</a>.
                </p>
            </div>
        </body>
        </html>
        """
        
        content = Content(MimeType.html, html_content)
        mail = Mail(from_email, to_email, subject, content)
        
        # Send email
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        response = sg.client.mail.send.post(request_body=mail.get())
        
        if response.status_code >= 200 and response.status_code < 300:
            print(f"Welcome email with weather data sent to {subscriber.email}")
            return True
        else:
            print(f"Failed to send welcome email to {subscriber.email}: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"Error sending welcome email to {subscriber.email}: {str(e)}")
        return False