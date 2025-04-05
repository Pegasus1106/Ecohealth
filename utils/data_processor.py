import pandas as pd
import numpy as np

class DataProcessor:
    def __init__(self):
        self.supported_dtypes = ['int64', 'float64', 'object', 'datetime64']
    
    def read_data(self, file):
        """Read and perform initial data processing"""
        try:
            df = pd.read_csv(file)
            return self.preprocess_data(df)
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
    def preprocess_data(self, df):
        """Perform basic data preprocessing"""
        # Remove completely empty columns
        df = df.dropna(axis=1, how='all')
        
        # Convert date columns
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    pass
        
        # Handle missing values
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        categorical_columns = df.select_dtypes(include=['object']).columns
        
        # Fill numeric missing values with median
        df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())
        
        # Fill categorical missing values with mode
        df[categorical_columns] = df[categorical_columns].fillna(df[categorical_columns].mode().iloc[0])
        
        return df
    
    def get_column_types(self, df):
        """Analyze column types for visualization suggestions"""
        column_types = {}
        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                column_types[column] = 'numeric'
            elif pd.api.types.is_datetime64_any_dtype(df[column]):
                column_types[column] = 'datetime'
            else:
                column_types[column] = 'categorical'
        return column_types
