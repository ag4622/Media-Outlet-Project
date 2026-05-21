"""Utility functions for DynamoDB operations and data loading."""

import streamlit as st
import pandas as pd
import boto3

# Initialize DynamoDB resource at module level
dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('c23-ClinicalTrialTracker')


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    """Load clinical trials data from the DynamoDB table."""
    all_items = []
    last_evaluated_key = None

    while True:
        scan_kwargs = {}
        if last_evaluated_key:
            scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

        response = table.scan(**scan_kwargs)
        all_items.extend(response.get('Items', []))

        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break

    df = pd.DataFrame(all_items)
    return df


def convert_dynamodb_list_to_python(value) -> list:
    """Convert DynamoDB list format to Python list."""
    if isinstance(value, dict) and 'L' in value:
        result = []
        for item in value['L']:
            if isinstance(item, dict) and 'S' in item:
                result.append(item['S'])
        return result
    elif isinstance(value, list):
        return value
    return []


def get_unique_values(df, column) -> list:
    """Get unique values from a column that may contain lists."""
    unique_values = set()
    for value in df.get(column, []):
        items = convert_dynamodb_list_to_python(value)
        unique_values.update(items)
    return sorted(list(unique_values))
