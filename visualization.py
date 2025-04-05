import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import data_utils as utils

def plot_temperature_history(historical_data):
    """
    Create a temperature history plot using Plotly.

    Args:
        historical_data (list): List of dictionaries containing historical weather data

    Returns:
        go.Figure: Plotly figure object
    """
    # Convert to pandas DataFrame
    df = pd.DataFrame(historical_data)

    # Convert date strings to datetime objects
    df['date'] = pd.to_datetime(df['date'])

    # Sort by date
    df = df.sort_values('date')

    # Calculate rolling averages (7-day window)
    df['rolling_avg_temp'] = df['temperature'].rolling(window=7, min_periods=1).mean()

    # Calculate overall statistics
    temp_min = df['temperature'].min()
    temp_max = df['temperature'].max()
    temp_avg = df['temperature'].mean()

    # Add Fahrenheit temperatures
    df['temperature_f'] = df['temperature'].apply(utils.celsius_to_fahrenheit)
    df['rolling_avg_temp_f'] = df['rolling_avg_temp'].apply(utils.celsius_to_fahrenheit)

    # Create figure
    fig = go.Figure()

    # Add temperature in Celsius
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['temperature'],
        name='Daily Temperature (°C)',
        line=dict(color='#1f77b4', width=1),
        hovertemplate='%{x|%b %d, %Y}<br>Temperature: %{y:.1f}°C<extra></extra>'
    ))

    # Add rolling average
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['rolling_avg_temp'],
        name='7-day Average (°C)',
        line=dict(color='#1f77b4', width=2),
        hovertemplate='%{x|%b %d, %Y}<br>7-day Avg: %{y:.1f}°C<extra></extra>'
    ))

    # Add horizontal lines for statistics
    fig.add_hline(y=temp_max, line_dash="dash", line_color="red",
                  annotation_text=f"Max: {temp_max:.1f}°C")
    fig.add_hline(y=temp_min, line_dash="dash", line_color="blue",
                  annotation_text=f"Min: {temp_min:.1f}°C")
    fig.add_hline(y=temp_avg, line_dash="dash", line_color="green",
                  annotation_text=f"Avg: {temp_avg:.1f}°C")

    # Update layout
    fig.update_layout(
        title='Temperature History (Past 6 Months)',
        xaxis=dict(
            title='Date',
            tickformat='%b %Y',
            showgrid=True
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

    return fig

def plot_aqi_history(historical_data):
    """
    Create an AQI history plot using Plotly.

    Args:
        historical_data (list): List of dictionaries containing historical AQI data

    Returns:
        go.Figure: Plotly figure object
    """
    # Convert to pandas DataFrame
    df = pd.DataFrame(historical_data)

    # Convert date strings to datetime objects
    df['date'] = pd.to_datetime(df['date'])

    # Sort by date
    df = df.sort_values('date')

    # Calculate rolling average (7-day window)
    df['rolling_avg_aqi'] = df['aqi'].rolling(window=7, min_periods=1).mean()

    # Calculate overall statistics
    aqi_min = df['aqi'].min()
    aqi_max = df['aqi'].max()
    aqi_avg = df['aqi'].mean()

    # Create figure
    fig = go.Figure()

    # Add colored background rectangles for AQI categories
    y_ranges = [
        (0, 50, "#00e400", "Good"),
        (51, 100, "#ffff00", "Moderate"),
        (101, 150, "#ff7e00", "Unhealthy for Sensitive Groups"),
        (151, 200, "#ff0000", "Unhealthy"),
        (201, 300, "#99004c", "Very Unhealthy"),
        (301, max(df['aqi'].max(), 301), "#7e0023", "Hazardous")
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

    # Add AQI data
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['aqi'],
        name='Daily AQI',
        line=dict(color='#2ca02c', width=1),
        hovertemplate='%{x|%b %d, %Y}<br>AQI: %{y:.1f}<extra></extra>'
    ))

    # Add rolling average
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['rolling_avg_aqi'],
        name='7-day Average',
        line=dict(color='#2ca02c', width=2),
        hovertemplate='%{x|%b %d, %Y}<br>7-day Avg: %{y:.1f}<extra></extra>'
    ))

    # Add horizontal lines for statistics
    fig.add_hline(y=aqi_max, line_dash="dash", line_color="red",
                  annotation_text=f"Max: {aqi_max:.1f}")
    fig.add_hline(y=aqi_min, line_dash="dash", line_color="blue",
                  annotation_text=f"Min: {aqi_min:.1f}")
    fig.add_hline(y=aqi_avg, line_dash="dash", line_color="green",
                  annotation_text=f"Avg: {aqi_avg:.1f}")

    # Add annotations for AQI categories
    for y_min, y_max, color, label in y_ranges:
        fig.add_annotation(
            xref="paper",
            x=1.01,
            y=(y_min + y_max) / 2,
            text=label,
            showarrow=False,
            font=dict(size=10),
            align="left"
        )

    # Update layout
    fig.update_layout(
        title='Air Quality Index History (Past 6 Months)',
        xaxis=dict(
            title='Date',
            tickformat='%b %Y',
            showgrid=True
        ),
        yaxis=dict(
            title='Air Quality Index (AQI)',
            showgrid=True,
            range=[0, max(max(df['aqi']) * 1.1, 300)]
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hovermode='x unified',
        margin=dict(l=60, r=100, t=50, b=50)
    )

    return fig

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
        title='7-Day Weather & AQI Forecast',
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