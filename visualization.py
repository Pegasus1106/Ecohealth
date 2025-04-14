import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import data_utils as utils


def plot_temperature_last_24h(historical_data):
    """
    Create a temperature plot for the last 24 hours using Plotly.

    Args:
        historical_data (list): List of dictionaries containing historical weather data

    Returns:
        go.Figure: Plotly figure object
    """
    # Convert to pandas DataFrame
    df = pd.DataFrame(historical_data)

    # Filter only the 24h data
    df_24h = df[df['is_last_24h'].fillna(False)]
    
    if len(df_24h) == 0:
        # No 24h data found, create an empty figure with a message
        fig = go.Figure()
        fig.update_layout(
            title='Last 24 Hours Temperature Data',
            annotations=[{
                'text': 'No 24-hour data available',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    # Convert date strings to datetime objects
    df_24h['date'] = pd.to_datetime(df_24h['date'])

    # Sort by date
    df_24h = df_24h.sort_values('date')

    # Add Fahrenheit temperatures
    df_24h['temperature_f'] = df_24h['temperature'].apply(utils.celsius_to_fahrenheit)

    # Create figure
    fig = go.Figure()

    # Add temperature in Celsius
    fig.add_trace(go.Scatter(
        x=df_24h['date'],
        y=df_24h['temperature'],
        name='Hourly Temperature (°C)',
        line=dict(color='#ff7f0e', width=2),
        mode='lines+markers',
        hovertemplate='%{x|%I:%M %p}<br>Temperature: %{y:.1f}°C<extra></extra>'
    ))

    # Calculate overall statistics
    temp_min = df_24h['temperature'].min()
    temp_max = df_24h['temperature'].max()
    temp_current = df_24h.iloc[-1]['temperature'] if not df_24h.empty else None

    # Add horizontal lines for statistics
    fig.add_hline(y=temp_max, line_dash="dash", line_color="red",
                  annotation_text=f"Max: {temp_max:.1f}°C")
    fig.add_hline(y=temp_min, line_dash="dash", line_color="blue",
                  annotation_text=f"Min: {temp_min:.1f}°C")

    # Add annotations for current temperature
    if temp_current is not None:
        fig.add_annotation(
            x=df_24h['date'].iloc[-1],
            y=temp_current,
            text=f"Current: {temp_current:.1f}°C",
            showarrow=True,
            arrowhead=1,
            arrowcolor="#ff7f0e",
            arrowsize=1,
            arrowwidth=2
        )

    # Add time of day background
    # Morning (6 AM - 12 PM): Light yellow
    # Afternoon (12 PM - 6 PM): Light orange
    # Evening (6 PM - 12 AM): Light blue
    # Night (12 AM - 6 AM): Dark blue
    now = datetime.now()
    yesterday = now - pd.Timedelta(days=1)
    
    time_ranges = [
        (yesterday.replace(hour=0, minute=0), yesterday.replace(hour=6, minute=0), "rgba(25, 25, 112, 0.2)", "Night"),
        (yesterday.replace(hour=6, minute=0), yesterday.replace(hour=12, minute=0), "rgba(255, 255, 224, 0.2)", "Morning"),
        (yesterday.replace(hour=12, minute=0), yesterday.replace(hour=18, minute=0), "rgba(255, 222, 173, 0.2)", "Afternoon"),
        (yesterday.replace(hour=18, minute=0), yesterday.replace(hour=0, minute=0) + pd.Timedelta(days=1), "rgba(176, 224, 230, 0.2)", "Evening"),
        (now.replace(hour=0, minute=0), now.replace(hour=6, minute=0), "rgba(25, 25, 112, 0.2)", "Night"),
        (now.replace(hour=6, minute=0), now.replace(hour=12, minute=0), "rgba(255, 255, 224, 0.2)", "Morning"),
        (now.replace(hour=12, minute=0), now.replace(hour=18, minute=0), "rgba(255, 222, 173, 0.2)", "Afternoon"),
        (now.replace(hour=18, minute=0), now, "rgba(176, 224, 230, 0.2)", "Evening"),
    ]
    
    # Add time of day background shading
    for start, end, color, label in time_ranges:
        if start <= end:  # Normal case
            fig.add_shape(
                type="rect",
                x0=start,
                x1=end,
                y0=temp_min - 1,
                y1=temp_max + 1,
                fillcolor=color,
                opacity=0.8,
                layer="below",
                line_width=0,
            )
            
            # Add time of day label
            fig.add_annotation(
                x=(start + (end - start)/2),
                y=temp_min - 1.5,
                text=label,
                showarrow=False,
                font=dict(size=10),
            )

    # Update layout
    fig.update_layout(
        title='Temperature - Last 24 Hours',
        xaxis=dict(
            title='Time',
            tickformat='%I:%M %p',
            showgrid=True,
            type='date'
        ),
        yaxis=dict(
            title='Temperature (°C)',
            showgrid=True
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hovermode='x',
        margin=dict(l=60, r=60, t=50, b=50)
    )

    return fig

# This function has been removed as we no longer display historical AQI data (past 3 months)
    
def plot_aqi_last_24h(historical_data):
    """
    Create an AQI plot for the last 24 hours using Plotly.

    Args:
        historical_data (list): List of dictionaries containing historical AQI data

    Returns:
        go.Figure: Plotly figure object
    """
    # Convert to pandas DataFrame
    df = pd.DataFrame(historical_data)

    # Filter only the 24h data
    df_24h = df[df['is_last_24h'].fillna(False)]
    
    if len(df_24h) == 0:
        # No 24h data found, create an empty figure with a message
        fig = go.Figure()
        fig.update_layout(
            title='Last 24 Hours AQI Data',
            annotations=[{
                'text': 'No 24-hour data available',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    # Convert date strings to datetime objects
    df_24h['date'] = pd.to_datetime(df_24h['date'])

    # Sort by date
    df_24h = df_24h.sort_values('date')

    # Calculate overall statistics
    aqi_min = df_24h['aqi'].min()
    aqi_max = df_24h['aqi'].max()
    aqi_current = df_24h.iloc[-1]['aqi'] if not df_24h.empty else None

    # Create figure
    fig = go.Figure()
    
    # Add colored background for AQI categories
    y_ranges = [
        (0, 50, "#00e400", "Good"),
        (51, 100, "#ffff00", "Moderate"),
        (101, 150, "#ff7e00", "Unhealthy for Sensitive Groups"),
        (151, 200, "#ff0000", "Unhealthy"),
        (201, 300, "#99004c", "Very Unhealthy"),
        (301, max(df_24h['aqi'].max(), 301), "#7e0023", "Hazardous")
    ]

    for y_min, y_max, color, label in y_ranges:
        fig.add_shape(
            type="rect",
            xref="paper",
            yref="y",
            x0=0,
            x1=1,
            y0=y_min,
            y1=y_max,
            fillcolor=color,
            opacity=0.2,
            layer="below",
            line_width=0,
        )
        
        # Add AQI category labels
        fig.add_annotation(
            xref="paper",
            x=1.01,
            y=(y_min + y_max) / 2,
            text=label,
            showarrow=False,
            font=dict(size=10),
            align="left"
        )

    # Add AQI data
    fig.add_trace(go.Scatter(
        x=df_24h['date'],
        y=df_24h['aqi'],
        name='Hourly AQI',
        line=dict(color='#9467bd', width=2),
        mode='lines+markers',
        hovertemplate='%{x|%I:%M %p}<br>AQI: %{y:.1f}<extra></extra>'
    ))

    # Add horizontal lines for statistics
    fig.add_hline(y=aqi_max, line_dash="dash", line_color="red",
                  annotation_text=f"Max: {aqi_max:.1f}")
    fig.add_hline(y=aqi_min, line_dash="dash", line_color="blue",
                  annotation_text=f"Min: {aqi_min:.1f}")

    # Add annotation for current AQI
    if aqi_current is not None:
        fig.add_annotation(
            x=df_24h['date'].iloc[-1],
            y=aqi_current,
            text=f"Current: {aqi_current:.1f}",
            showarrow=True,
            arrowhead=1,
            arrowcolor="#9467bd",
            arrowsize=1,
            arrowwidth=2
        )
    
    # Add time of day background
    # Morning (6 AM - 12 PM): Light yellow
    # Afternoon (12 PM - 6 PM): Light orange
    # Evening (6 PM - 12 AM): Light blue
    # Night (12 AM - 6 AM): Dark blue
    now = datetime.now()
    yesterday = now - pd.Timedelta(days=1)
    
    time_ranges = [
        (yesterday.replace(hour=0, minute=0), yesterday.replace(hour=6, minute=0), "rgba(25, 25, 112, 0.1)", "Night"),
        (yesterday.replace(hour=6, minute=0), yesterday.replace(hour=12, minute=0), "rgba(255, 255, 224, 0.1)", "Morning"),
        (yesterday.replace(hour=12, minute=0), yesterday.replace(hour=18, minute=0), "rgba(255, 222, 173, 0.1)", "Afternoon"),
        (yesterday.replace(hour=18, minute=0), yesterday.replace(hour=0, minute=0) + pd.Timedelta(days=1), "rgba(176, 224, 230, 0.1)", "Evening"),
        (now.replace(hour=0, minute=0), now.replace(hour=6, minute=0), "rgba(25, 25, 112, 0.1)", "Night"),
        (now.replace(hour=6, minute=0), now.replace(hour=12, minute=0), "rgba(255, 255, 224, 0.1)", "Morning"),
        (now.replace(hour=12, minute=0), now.replace(hour=18, minute=0), "rgba(255, 222, 173, 0.1)", "Afternoon"),
        (now.replace(hour=18, minute=0), now, "rgba(176, 224, 230, 0.1)", "Evening"),
    ]
    
    # Add time of day background shading
    for start, end, color, label in time_ranges:
        if start <= end:  # Normal case
            fig.add_shape(
                type="rect",
                x0=start,
                x1=end,
                y0=0,  # Start from 0 for AQI
                y1=max(df_24h['aqi'].max() * 1.1, 100),
                fillcolor=color,
                opacity=0.8,
                layer="below",
                line_width=0,
            )
            
            # Add time of day label at the bottom
            fig.add_annotation(
                x=(start + (end - start)/2),
                y=0,
                text=label,
                showarrow=False,
                font=dict(size=10),
                yshift=-20
            )

    # Update layout
    fig.update_layout(
        title='Air Quality Index - Last 24 Hours',
        xaxis=dict(
            title='Time',
            tickformat='%I:%M %p',
            showgrid=True,
            type='date'
        ),
        yaxis=dict(
            title='Air Quality Index (AQI)',
            showgrid=True,
            range=[0, max(max(df_24h['aqi']) * 1.1, 100)]
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hovermode='x',
        margin=dict(l=60, r=100, t=50, b=50)
    )

    return fig

def plot_last_week_data(last_week_data):
    """
    Create a line chart for last week's temperature, air quality, and humidity data.

    Args:
        last_week_data (list): List of dictionaries containing last week's data

    Returns:
        go.Figure: Plotly figure object for temperature
        go.Figure: Plotly figure object for AQI and humidity
    """
    # Convert to pandas DataFrame
    df = pd.DataFrame(last_week_data)
    
    # Convert date strings to datetime objects and format for display
    df['date'] = pd.to_datetime(df['date'])
    df['date_display'] = df['date'].dt.strftime('%b %d')
    
    # Create first figure for temperature
    temp_fig = go.Figure()
    
    # Add temperature range (min to max)
    temp_fig.add_trace(go.Scatter(
        x=df['date_display'],
        y=df['temp_max'],
        name='Max Temperature',
        line=dict(color='red', width=0),
        mode='lines',
        showlegend=False
    ))

    temp_fig.add_trace(go.Scatter(
        x=df['date_display'],
        y=df['temp_min'],
        name='Temperature Range',
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.2)',
        line=dict(color='blue', width=0),
        mode='lines',
        showlegend=True
    ))
    
    # Add average temperature line
    temp_fig.add_trace(go.Scatter(
        x=df['date_display'],
        y=df['temp_avg'],
        name='Average Temperature',
        line=dict(color='red', width=2),
        mode='lines+markers'
    ))
    
    # Update layout for temperature
    temp_fig.update_layout(
        title='Last Week Temperature Data',
        xaxis=dict(
            title='Date',
            showgrid=True,
            tickmode='array',
            tickvals=df['date_display'].tolist()
        ),
        yaxis=dict(
            title='Temperature (°C)',
            showgrid=True
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hovermode='x unified',
        margin=dict(l=60, r=60, t=50, b=50)
    )
    
    # Create second figure for AQI and Humidity
    aqi_humidity_fig = go.Figure()
    
    # Add Air Quality Index
    aqi_humidity_fig.add_trace(go.Scatter(
        x=df['date_display'],
        y=df['aqi_avg'],
        name='Air Quality Index',
        line=dict(color='green', width=2),
        mode='lines+markers'
    ))
    
    # Add Humidity
    aqi_humidity_fig.add_trace(go.Scatter(
        x=df['date_display'],
        y=df['humidity_avg'],
        name='Humidity (%)',
        line=dict(color='blue', width=2),
        mode='lines+markers',
        yaxis='y2'
    ))
    
    # Add colored background for AQI categories
    y_ranges = [
        (0, 50, "#00e400", "Good"),
        (51, 100, "#ffff00", "Moderate"),
        (101, 150, "#ff7e00", "Unhealthy for Sensitive Groups"),
        (151, 200, "#ff0000", "Unhealthy"),
        (201, 300, "#99004c", "Very Unhealthy"),
        (301, 500, "#7e0023", "Hazardous")
    ]
    
    for y_min, y_max, color, label in y_ranges:
        aqi_humidity_fig.add_shape(
            type="rect",
            xref="paper",
            yref="y",
            x0=0,
            x1=1,
            y0=y_min,
            y1=y_max,
            fillcolor=color,
            opacity=0.1,
            layer="below",
            line_width=0,
        )
    
    # Update layout for AQI and Humidity
    aqi_humidity_fig.update_layout(
        title='Last Week Air Quality and Humidity Data',
        xaxis=dict(
            title='Date',
            showgrid=True,
            tickmode='array',
            tickvals=df['date_display'].tolist()
        ),
        yaxis=dict(
            title='Air Quality Index (AQI)',
            showgrid=True,
            range=[0, max(max(df['aqi_avg'] * 1.1), 100) if not df['aqi_avg'].isna().all() else 100]
        ),
        yaxis2=dict(
            title='Humidity (%)',
            overlaying='y',
            side='right',
            showgrid=False,
            range=[0, 100]
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hovermode='x unified',
        margin=dict(l=60, r=60, t=50, b=50)
    )
    
    return temp_fig, aqi_humidity_fig

def plot_forecast(forecast_data):
    """
    Create a forecast plot using Plotly.

    Args:
        forecast_data (list): List of dictionaries containing forecast data

    Returns:
        go.Figure: Plotly figure object
    """
    # Convert to pandas DataFrame
    df = pd.DataFrame(forecast_data)

    # Convert date strings to datetime objects
    df['date'] = pd.to_datetime(df['date'])

    # Create figure with secondary y-axis
    fig = go.Figure()

    # Add temperature range
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['temp_max'],
        name='Max Temperature',
        line=dict(color='red', width=0),
        mode='lines',
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['temp_min'],
        name='Temperature Range',
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.2)',
        line=dict(color='blue', width=0),
        mode='lines',
        showlegend=True
    ))

    # Add average temperature line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['temp_avg'],
        name='Average Temperature',
        line=dict(color='red', width=2),
        mode='lines+markers'
    ))

    # Add AQI data on secondary y-axis
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['aqi_avg'],
        name='AQI',
        line=dict(color='green', width=2),
        mode='lines+markers',
        yaxis='y2'
    ))

    # Update layout
    fig.update_layout(
        title='Weather & AQI Forecast',
        xaxis=dict(
            title='Date',
            tickformat='%b %d',
            showgrid=True
        ),
        yaxis=dict(
            title='Temperature (°C)',
            showgrid=True
        ),
        yaxis2=dict(
            title='Air Quality Index',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hovermode='x unified',
        margin=dict(l=60, r=60, t=50, b=50)
    )

    return fig
