import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class AdvancedAnalytics:
    def __init__(self, df):
        self.df = df
        self.numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        self.categorical_cols = df.select_dtypes(include=['object']).columns

    def get_statistical_summary(self):
        """Generate comprehensive statistical summary"""
        if len(self.numeric_cols) == 0:
            return None

        stats_summary = {}
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            stats_summary[col] = {
                'mean': data.mean(),
                'median': data.median(),
                'std': data.std(),
                'skewness': stats.skew(data),
                'kurtosis': stats.kurtosis(data),
                'q1': data.quantile(0.25),
                'q3': data.quantile(0.75),
                'iqr': data.quantile(0.75) - data.quantile(0.25),
                'min': data.min(),
                'max': data.max()
            }
        return stats_summary

    def create_correlation_heatmap(self):
        """Generate correlation heatmap"""
        if len(self.numeric_cols) < 2:
            return None

        corr_matrix = self.df[self.numeric_cols].corr()
        fig = px.imshow(
            corr_matrix,
            labels=dict(color="Correlation"),
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            color_continuous_scale='RdBu_r',
            aspect='auto'
        )
        fig.update_layout(
            title='Correlation Heatmap',
            xaxis_title='Features',
            yaxis_title='Features',
            height=600
        )
        return fig

    def detect_outliers(self, threshold=1.5):
        """Detect outliers using IQR method"""
        outliers = {}
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            outliers[col] = {
                'count': len(data[(data < lower_bound) | (data > upper_bound)]),
                'percentage': len(data[(data < lower_bound) | (data > upper_bound)]) / len(data) * 100,
                'bounds': {
                    'lower': lower_bound,
                    'upper': upper_bound
                }
            }
        return outliers

    def create_distribution_plots(self):
        """Create distribution plots for numeric columns"""
        if len(self.numeric_cols) == 0:
            return None

        # Create subplots for each numeric column
        fig = make_subplots(
            rows=len(self.numeric_cols), 
            cols=1,
            subplot_titles=list(self.numeric_cols),
            vertical_spacing=0.05
        )

        for idx, col in enumerate(self.numeric_cols, 1):
            data = self.df[col].dropna()

            # Add histogram
            fig.add_trace(
                go.Histogram(
                    x=data,
                    name=col,
                    histnorm='probability density',
                    showlegend=False,
                    nbinsx=30
                ),
                row=idx, 
                col=1
            )

            try:
                # Try to add a smoothed line using numpy's histogram and cumulative sum
                hist, bin_edges = np.histogram(data, bins=50, density=True)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

                # Simple smoothing using moving average
                window_size = 5
                smoothed = np.convolve(hist, np.ones(window_size)/window_size, mode='valid')
                x_smooth = bin_centers[window_size-1:]

                fig.add_trace(
                    go.Scatter(
                        x=x_smooth,
                        y=smoothed,
                        name=f'{col} density',
                        line=dict(color='red', width=2),
                        showlegend=False
                    ),
                    row=idx, 
                    col=1
                )
            except Exception as e:
                print(f"Could not create density curve for {col}: {str(e)}")
                continue

        fig.update_layout(
            height=300 * len(self.numeric_cols),
            title_text="Distribution Analysis",
            showlegend=False
        )
        return fig

    def analyze_trends(self, date_column=None):
        """Analyze trends in numeric columns over time"""
        if date_column is None:
            date_cols = self.df.select_dtypes(include=['datetime64']).columns
            if len(date_cols) > 0:
                date_column = date_cols[0]
            else:
                return None

        if date_column not in self.df.columns:
            return None

        trend_analysis = {}
        for col in self.numeric_cols:
            if col == date_column:
                continue

            # Calculate rolling statistics
            rolling_mean = self.df[col].rolling(window=7, min_periods=1).mean()
            rolling_std = self.df[col].rolling(window=7, min_periods=1).std()

            # Create trend visualization
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=self.df[date_column],
                y=self.df[col],
                name='Raw Data',
                mode='lines+markers',
                marker=dict(size=3)
            ))
            fig.add_trace(go.Scatter(
                x=self.df[date_column],
                y=rolling_mean,
                name='7-point Moving Average',
                line=dict(color='red')
            ))
            fig.add_trace(go.Scatter(
                x=self.df[date_column],
                y=rolling_std,
                name='7-point Standard Deviation',
                line=dict(color='green', dash='dash')
            ))

            fig.update_layout(
                title=f'Trend Analysis: {col}',
                xaxis_title=date_column,
                yaxis_title=col,
                height=400
            )

            trend_analysis[col] = {
                'visualization': fig,
                'statistics': {
                    'overall_trend': 'increasing' if self.df[col].corr(pd.Series(range(len(self.df)))) > 0 else 'decreasing',
                    'volatility': self.df[col].std() / self.df[col].mean() if self.df[col].mean() != 0 else 0
                }
            }

        return trend_analysis
