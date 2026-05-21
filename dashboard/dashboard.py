"""Creates a streamlit dashboard to display the latest clinical trials data. """

import streamlit as st
import pandas as pd
import awswrangler as wr
import boto3

# Initialize DynamoDB resource at module level
dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('c23-ClinicalTrialTracker')


@st.cache_data
def load_data(table_name="c23-ClinicalTrialTracker"):
    """Load clinical trails data from the dynamodb table."""
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


@st.cache_data
def get_trials_sponsors():
    """Get all trial IDs and sponsors with pagination."""
    all_items = []
    last_evaluated_key = None

    while True:
        scan_kwargs = {
            'ProjectionExpression': 'trial_id, sponsors'
        }
        if last_evaluated_key:
            scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

        response = table.scan(**scan_kwargs)
        all_items.extend(response.get('Items', []))

        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break

    return pd.DataFrame(all_items)


def get_sponsors_count():
    """Get count of sponsors across all trials. Needs editing"""
    df = get_trials_sponsors()
    sponsor_counts = {}
    for sponsors in df['sponsors']:
        # sponsors is in DynamoDB format: {'L': [{'S': 'Sponsor Name'}, ...]}
        if isinstance(sponsors, dict) and 'L' in sponsors:
            for sponsor_item in sponsors['L']:
                if isinstance(sponsor_item, dict) and 'S' in sponsor_item:
                    sponsor_name = sponsor_item['S']
                    sponsor_counts[sponsor_name] = sponsor_counts.get(
                        sponsor_name, 0) + 1
    return pd.DataFrame(list(sponsor_counts.items()), columns=['Sponsor', 'Count']).sort_values('Count', ascending=False)


def dashboard():
    st.title("Clinical Trials Dashboard")
    st.markdown(
        "This dashboard displays the latest clinical trials data from clinicaltrials.gov.")

    # Load data
    df = load_data()
    st.subheader("Latest Clinical Trials")
    st.dataframe(df.head())

    st.subheader("Sponsor Counts")
    sponsor_counts_df = get_sponsors_count()
    st.dataframe(sponsor_counts_df.head())


if __name__ == "__main__":
    dashboard()
