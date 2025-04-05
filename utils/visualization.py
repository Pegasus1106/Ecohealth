import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

class VisualizationGenerator:
    def __init__(self, df):
        self.df = df

    def create_visualization(self, viz_type, columns, title):
        """Generate visualization based on type and columns"""
        try:
            # Validate columns based on data types
            numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).columns
            categorical_cols = self.df.select_dtypes(include=['object']).columns

            if viz_type == 'scatter':
                # Ensure we use numeric columns for scatter plots
                valid_cols = [col for col in columns if col in numeric_cols]
                if len(valid_cols) < 2:
                    valid_cols = list(numeric_cols)[:2]
                return self._create_scatter_plot(valid_cols[:2], title)

            elif viz_type == 'line':
                # For line plots, prefer datetime + numeric, fallback to numeric pairs
                if len(columns) == 2 and columns[0] in self.df.columns and columns[1] in numeric_cols:
                    return self._create_line_plot(columns, title)
                else:
                    return self._create_line_plot([numeric_cols[0], numeric_cols[1]], title)

            elif viz_type == 'bar':
                # For bar plots, prefer categorical + numeric
                if len(columns) == 2 and columns[0] in categorical_cols and columns[1] in numeric_cols:
                    return self._create_bar_plot(columns, title)
                elif len(categorical_cols) > 0 and len(numeric_cols) > 0:
                    return self._create_bar_plot([categorical_cols[0], numeric_cols[0]], title)
                else:
                    return self._create_bar_plot([numeric_cols[0]], title)

            elif viz_type == 'histogram':
                # For histograms, use numeric columns
                valid_col = columns[0] if columns[0] in numeric_cols else numeric_cols[0]
                return self._create_histogram([valid_col], title)

            elif viz_type == 'box':
                # For box plots, prefer categorical + numeric
                if len(columns) == 2 and columns[0] in categorical_cols and columns[1] in numeric_cols:
                    return self._create_box_plot(columns, title)
                elif len(categorical_cols) > 0 and len(numeric_cols) > 0:
                    return self._create_box_plot([categorical_cols[0], numeric_cols[0]], title)
                else:
                    return self._create_box_plot([numeric_cols[0]], title)
            else:
                raise ValueError(f"Unsupported visualization type: {viz_type}")
        except Exception as e:
            raise Exception(f"Error creating visualization: {str(e)}")

    def _create_scatter_plot(self, columns, title):
        fig = px.scatter(
            self.df,
            x=columns[0],
            y=columns[1],
            title=title,
            template='plotly_white'
        )
        return fig

    def _create_line_plot(self, columns, title):
        fig = px.line(
            self.df,
            x=columns[0],
            y=columns[1],
            title=title,
            template='plotly_white'
        )
        return fig

    def _create_bar_plot(self, columns, title):
        if len(columns) == 2:
            fig = px.bar(
                self.df,
                x=columns[0],
                y=columns[1],
                title=title,
                template='plotly_white'
            )
        else:
            fig = px.bar(
                self.df,
                x=columns[0],
                title=title,
                template='plotly_white'
            )
        return fig

    def _create_histogram(self, columns, title):
        fig = px.histogram(
            self.df,
            x=columns[0],
            title=title,
            template='plotly_white'
        )
        return fig

    def _create_box_plot(self, columns, title):
        if len(columns) == 2:
            fig = px.box(
                self.df,
                x=columns[0],
                y=columns[1],
                title=title,
                template='plotly_white'
            )
        else:
            fig = px.box(
                self.df,
                x=columns[0],
                title=title,
                template='plotly_white'
            )
        return fig