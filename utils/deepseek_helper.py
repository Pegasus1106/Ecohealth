import pandas as pd
import numpy as np
import requests
import os
import json

class DeepSeekAnalyzer:
    def __init__(self):
        self.api_key = os.environ.get('sk-849bac25a048438faeedcd4c7d834382')
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.visualization_types = ['scatter', 'line', 'bar', 'histogram', 'box']

    def analyze_dataset(self, df):
        """Analyze dataset using DeepSeek API and suggest visualizations"""
        try:
            # Get dataset information
            column_types = self._get_column_types(df)
            data_summary = self._get_data_summary(df)

            # Prepare prompt for DeepSeek
            prompt = self._create_analysis_prompt(df, column_types, data_summary)

            # Get suggestions from DeepSeek API
            suggestions = self._get_deepseek_suggestions(prompt, df)

            return {
                'suggestions': suggestions
            }
        except Exception as e:
            print(f"Error in DeepSeek analysis: {str(e)}")
            # Fallback to basic analysis if DeepSeek fails
            return self._fallback_analysis(df)

    def _get_column_types(self, df):
        """Determine column types"""
        column_types = {}
        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                column_types[column] = 'numeric'
            elif pd.api.types.is_datetime64_any_dtype(df[column]):
                column_types[column] = 'datetime'
            else:
                column_types[column] = 'categorical'
        return column_types

    def _get_data_summary(self, df):
        """Get summary statistics of the dataset"""
        summary = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'numeric_columns': len(df.select_dtypes(include=['int64', 'float64']).columns),
            'categorical_columns': len(df.select_dtypes(include=['object']).columns),
            'datetime_columns': len(df.select_dtypes(include=['datetime64']).columns)
        }
        return summary

    def _create_analysis_prompt(self, df, column_types, data_summary):
        """Create a prompt for DeepSeek API"""
        column_info = []
        for col, type_ in column_types.items():
            if type_ == 'numeric':
                stats = {
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'mean': float(df[col].mean())
                }
                column_info.append(f"{col} ({type_}): range [{stats['min']:.2f} - {stats['max']:.2f}], mean: {stats['mean']:.2f}")
            else:
                unique_vals = df[col].nunique()
                column_info.append(f"{col} ({type_}): {unique_vals} unique values")

        prompt = f"""Analyze this dataset and suggest 5 meaningful visualizations:
Dataset Summary:
- Total rows: {data_summary['total_rows']}
- Columns: {data_summary['total_columns']}
Column Information:
{chr(10).join(column_info)}

For each visualization, provide:
1. Type (scatter, line, bar, histogram, or box)
2. Columns to use (use actual column names from the dataset)
3. Title
4. Reason for this visualization

Return in JSON format with keys: type, columns (list), title, reasoning"""
        return prompt

    def _get_deepseek_suggestions(self, prompt, df):
        """Get visualization suggestions from DeepSeek API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': 'You are a data visualization expert.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7
            }

            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()

            suggestions = self._parse_deepseek_response(response.json())
            return self._validate_suggestions(suggestions, df)

        except Exception as e:
            print(f"DeepSeek API error: {str(e)}")
            return self._fallback_analysis(df)

    def _validate_suggestions(self, suggestions, df):
        """Validate and fix suggestions to ensure they use valid columns"""
        valid_suggestions = []
        columns = list(df.columns)
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()

        for sugg in suggestions:
            # Ensure columns exist in the dataset
            valid_columns = [col for col in sugg['columns'] if col in columns]
            if not valid_columns:
                continue

            # For scatter plots, ensure we have two numeric columns
            if sugg['type'] == 'scatter' and len(valid_columns) < 2:
                remaining_numeric = [col for col in numeric_cols if col not in valid_columns]
                if remaining_numeric:
                    valid_columns.append(remaining_numeric[0])

            valid_suggestions.append({
                'type': sugg['type'],
                'columns': valid_columns,
                'title': sugg['title']
            })

        # If we don't have enough valid suggestions, add fallback ones
        if len(valid_suggestions) < 5:
            fallback = self._fallback_analysis(df)
            valid_suggestions.extend(fallback[len(valid_suggestions):])

        return valid_suggestions[:5]

    def _parse_deepseek_response(self, response):
        """Parse DeepSeek API response into visualization suggestions"""
        try:
            content = response['choices'][0]['message']['content']
            suggestions = json.loads(content)

            formatted_suggestions = []
            for sugg in suggestions:
                formatted_suggestions.append({
                    'type': sugg['type'],
                    'columns': sugg['columns'],
                    'title': sugg['title']
                })

            return formatted_suggestions

        except Exception as e:
            print(f"Error parsing DeepSeek response: {str(e)}")
            return []

    def _fallback_analysis(self, df):
        """Generate basic visualization suggestions if DeepSeek API fails"""
        if df is None or df.empty:
            return []

        suggestions = []
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        # 1. Scatter plot (if we have 2+ numeric columns)
        if len(numeric_cols) >= 2:
            suggestions.append({
                'type': 'scatter',
                'columns': [numeric_cols[0], numeric_cols[1]],
                'title': f'Correlation: {numeric_cols[0]} vs {numeric_cols[1]}'
            })

        # 2. Line plot (if we have datetime and numeric)
        if datetime_cols and numeric_cols:
            suggestions.append({
                'type': 'line',
                'columns': [datetime_cols[0], numeric_cols[0]],
                'title': f'Time Series: {numeric_cols[0]} over time'
            })
        elif len(numeric_cols) >= 2:  # Fallback to line plot with numeric columns
            suggestions.append({
                'type': 'line',
                'columns': [numeric_cols[0], numeric_cols[1]],
                'title': f'Trend: {numeric_cols[1]} by {numeric_cols[0]}'
            })

        # 3. Bar chart (categorical and numeric)
        if categorical_cols and numeric_cols:
            suggestions.append({
                'type': 'bar',
                'columns': [categorical_cols[0], numeric_cols[0]],
                'title': f'{numeric_cols[0]} by {categorical_cols[0]}'
            })
        elif numeric_cols:  # Fallback to bar chart with numeric column
            suggestions.append({
                'type': 'bar',
                'columns': [numeric_cols[0]],
                'title': f'Distribution of {numeric_cols[0]}'
            })

        # 4. Histogram (numeric)
        if numeric_cols:
            suggestions.append({
                'type': 'histogram',
                'columns': [numeric_cols[0]],
                'title': f'Distribution of {numeric_cols[0]}'
            })

        # 5. Box plot (categorical and numeric)
        if categorical_cols and numeric_cols:
            suggestions.append({
                'type': 'box',
                'columns': [categorical_cols[0], numeric_cols[0]],
                'title': f'{numeric_cols[0]} Distribution by {categorical_cols[0]}'
            })
        elif numeric_cols:  # Fallback to box plot with numeric column
            suggestions.append({
                'type': 'box',
                'columns': [numeric_cols[0]],
                'title': f'Distribution of {numeric_cols[0]}'
            })

        # Ensure we have 5 suggestions
        while len(suggestions) < 5 and numeric_cols:
            suggestions.append({
                'type': 'histogram',
                'columns': [numeric_cols[0]],
                'title': f'Distribution of {numeric_cols[0]} (Alternative View)'
            })

        return suggestions[:5]

    def _get_correlations(self, df):
        """Calculate correlations between numeric columns"""
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        return df[numeric_cols].corr() if len(numeric_cols) > 0 else pd.DataFrame()