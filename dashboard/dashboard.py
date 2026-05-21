"""Creates a streamlit dashboard to display the latest clinical trials data. """

import streamlit as st
import pandas as pd
import awswrangler as wr
import boto3
import plotly.express as px

# Initialize DynamoDB resource at module level
dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('c23-ClinicalTrialTracker')


@st.cache_data(ttl=3600)
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


@st.cache_data(ttl=3600)
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


def convert_dynamodb_list_to_python(value):
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


def get_unique_values(df, column):
    """Get unique values from a column that may contain lists."""
    unique_values = set()
    for value in df.get(column, []):
        items = convert_dynamodb_list_to_python(value)
        unique_values.update(items)
    return sorted(list(unique_values))


def filter_data(df, selected_conditions, selected_interventions, selected_sponsors):
    """Filter data based on selected conditions, interventions, and sponsors."""
    filtered_df = df.copy()

    # Filter by conditions
    if selected_conditions:
        def has_condition(conds):
            conds_list = convert_dynamodb_list_to_python(conds)
            return any(c in selected_conditions for c in conds_list)
        filtered_df = filtered_df[filtered_df['conditions'].apply(
            has_condition)]

    # Filter by interventions
    if selected_interventions:
        def has_intervention(interventions):
            interventions_list = convert_dynamodb_list_to_python(interventions)
            return any(i in selected_interventions for i in interventions_list)
        filtered_df = filtered_df[filtered_df['interventions'].apply(
            has_intervention)]

    # Filter by sponsors
    if selected_sponsors:
        def has_sponsor(sponsors):
            sponsors_list = convert_dynamodb_list_to_python(sponsors)
            return any(s in selected_sponsors for s in sponsors_list)
        filtered_df = filtered_df[filtered_df['sponsors'].apply(has_sponsor)]

    return filtered_df


def get_trial_counts_by_category(df, category):
    """Get trial counts grouped by a specific category."""
    counts = {}
    for value in df.get(category, []):
        items = convert_dynamodb_list_to_python(value)
        for item in items:
            counts[item] = counts.get(item, 0) + 1

    if not counts:
        return pd.DataFrame()

    return pd.DataFrame(
        list(counts.items()),
        columns=[category.capitalize(), 'Trial Count']
    ).sort_values('Trial Count', ascending=False)


def dashboard():
    st.set_page_config(page_title="Clinical Trials Dashboard", layout="wide")
    st.title("Clinical Trials Dashboard")
    st.markdown(
        "This dashboard displays clinical trials data from clinicaltrials.gov with filtering and analytics.")

    # Load data
    df = load_data()

    # Get unique values for filters
    unique_conditions = get_unique_values(df, 'conditions')
    unique_interventions = get_unique_values(df, 'interventions')
    unique_sponsors = get_unique_values(df, 'sponsors')

    # Create sidebar for filters
    st.sidebar.header("Filters")
    selected_conditions = st.sidebar.multiselect(
        "Select Conditions",
        options=unique_conditions,
        help="Filter trials by medical conditions"
    )
    selected_interventions = st.sidebar.multiselect(
        "Select Interventions",
        options=unique_interventions,
        help="Filter trials by intervention types"
    )
    selected_sponsors = st.sidebar.multiselect(
        "Select Sponsors",
        options=unique_sponsors,
        help="Filter trials by trial sponsors"
    )

    # Filter data
    filtered_df = filter_data(df, selected_conditions,
                              selected_interventions, selected_sponsors)

    # Display summary metrics
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trials", len(df))
    with col2:
        st.metric("Filtered Trials", len(filtered_df))
    with col3:
        st.metric("Trials Shown (%)",
                  f"{(len(filtered_df)/len(df)*100):.1f}%" if len(df) > 0 else "0%")

    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Trials by Condition", "Trials by Intervention",
            "Trials by Sponsor", "Sponsor Counts", "Trial Data"]
    )

    with tab1:
        st.subheader("Trial Counts by Condition")
        condition_counts = get_trial_counts_by_category(
            filtered_df, 'conditions')
        if not condition_counts.empty:
            fig = px.bar(
                condition_counts,
                x='Trial Count',
                y='Conditions',
                orientation='h',
                title="Number of Trials by Condition",
                labels={'Conditions': 'Medical Condition',
                        'Trial Count': 'Number of Trials'},
                color='Trial Count',
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig, width='stretch')
            st.dataframe(condition_counts, width='stretch')
        else:
            st.info("No data available for the selected filters.")

    with tab2:
        st.subheader("Trial Counts by Intervention")
        intervention_counts = get_trial_counts_by_category(
            filtered_df, 'interventions')
        if not intervention_counts.empty:
            fig = px.bar(
                intervention_counts,
                x='Trial Count',
                y='Interventions',
                orientation='h',
                title="Number of Trials by Intervention",
                labels={'Interventions': 'Intervention Type',
                        'Trial Count': 'Number of Trials'},
                color='Trial Count',
                color_continuous_scale='plasma'
            )
            st.plotly_chart(fig, width='stretch')
            st.dataframe(intervention_counts, width='stretch')
        else:
            st.info("No data available for the selected filters.")

    with tab3:
        st.subheader("Trial Counts by Sponsor")
        sponsor_counts = get_trial_counts_by_category(filtered_df, 'sponsors')
        if not sponsor_counts.empty:
            fig = px.bar(
                sponsor_counts.head(20),  # Show top 20 sponsors
                x='Trial Count',
                y='Sponsors',
                orientation='h',
                title="Top 20 Sponsors by Trial Count",
                labels={'Sponsors': 'Sponsor',
                        'Trial Count': 'Number of Trials'},
                color='Trial Count',
                color_continuous_scale='blues'
            )
            fig.update_layout(yaxis_tickangle=0)
            st.plotly_chart(fig, width='stretch')
            st.dataframe(sponsor_counts, width='stretch')
        else:
            st.info("No data available for the selected filters.")

    with tab4:
        st.subheader("Sponsor Counts")
        sponsor_counts_df = get_sponsors_count()
        st.dataframe(sponsor_counts_df.head())

    with tab5:
        st.subheader("Latest Clinical Trials")
        st.dataframe(df.head())

        st.subheader("Filtered Trial Data")
        st.dataframe(filtered_df, width='stretch')


if __name__ == "__main__":
    dashboard()
