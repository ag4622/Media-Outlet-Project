"""Individual trial status tracking with timeline visualization."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import boto3
from datetime import datetime
from typing import Tuple, Optional

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('c23-ClinicalTrialTracker')


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    """Load clinical trials data from DynamoDB."""
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

    return pd.DataFrame(all_items)


def get_all_trial_ids(df: pd.DataFrame) -> list:
    """Get sorted list of all trial IDs."""
    trial_ids = df['trial_id'].dropna().unique().tolist()
    return sorted(trial_ids)


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


def filter_trials_by_criteria(df: pd.DataFrame, selected_sponsors: list,
                              selected_conditions: list, selected_interventions: list) -> pd.DataFrame:
    """Filter trials based on selected sponsors, conditions, and interventions."""
    filtered_df = df.copy()

    # Filter by sponsors (companies)
    if selected_sponsors:
        def has_sponsor(sponsors):
            sponsors_list = convert_dynamodb_list_to_python(sponsors)
            return any(s in selected_sponsors for s in sponsors_list)
        filtered_df = filtered_df[filtered_df['sponsors'].apply(has_sponsor)]

    # Filter by conditions (therapeutic areas)
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

    return filtered_df


def get_available_filters(df: pd.DataFrame, selected_sponsors: list = None,
                          selected_conditions: list = None, selected_interventions: list = None) -> dict:
    """Get available filter options based on current selections (cascading filters)."""
    if selected_sponsors is None:
        selected_sponsors = []
    if selected_conditions is None:
        selected_conditions = []
    if selected_interventions is None:
        selected_interventions = []

    # Get all available values first
    all_sponsors = get_unique_values(df, 'sponsors')
    all_conditions = get_unique_values(df, 'conditions')
    all_interventions = get_unique_values(df, 'interventions')

    # Build filters progressively - each filter shows only options from trials matching OTHER filters

    # Sponsors: show all sponsors unless conditions/interventions are selected
    available_sponsors = all_sponsors
    if selected_conditions or selected_interventions:
        temp_df = df.copy()
        if selected_conditions:
            def has_condition(conds):
                conds_list = convert_dynamodb_list_to_python(conds)
                return any(c in selected_conditions for c in conds_list)
            temp_df = temp_df[temp_df['conditions'].apply(has_condition)]
        if selected_interventions:
            def has_intervention(interventions):
                interventions_list = convert_dynamodb_list_to_python(
                    interventions)
                return any(i in selected_interventions for i in interventions_list)
            temp_df = temp_df[temp_df['interventions'].apply(has_intervention)]
        available_sponsors = get_unique_values(temp_df, 'sponsors')

    # Conditions: show all conditions unless sponsors/interventions are selected
    available_conditions = all_conditions
    if selected_sponsors or selected_interventions:
        temp_df = df.copy()
        if selected_sponsors:
            def has_sponsor(sponsors):
                sponsors_list = convert_dynamodb_list_to_python(sponsors)
                return any(s in selected_sponsors for s in sponsors_list)
            temp_df = temp_df[temp_df['sponsors'].apply(has_sponsor)]
        if selected_interventions:
            def has_intervention(interventions):
                interventions_list = convert_dynamodb_list_to_python(
                    interventions)
                return any(i in selected_interventions for i in interventions_list)
            temp_df = temp_df[temp_df['interventions'].apply(has_intervention)]
        available_conditions = get_unique_values(temp_df, 'conditions')

    # Interventions: show all interventions unless sponsors/conditions are selected
    available_interventions = all_interventions
    if selected_sponsors or selected_conditions:
        temp_df = df.copy()
        if selected_sponsors:
            def has_sponsor(sponsors):
                sponsors_list = convert_dynamodb_list_to_python(sponsors)
                return any(s in selected_sponsors for s in sponsors_list)
            temp_df = temp_df[temp_df['sponsors'].apply(has_sponsor)]
        if selected_conditions:
            def has_condition(conds):
                conds_list = convert_dynamodb_list_to_python(conds)
                return any(c in selected_conditions for c in conds_list)
            temp_df = temp_df[temp_df['conditions'].apply(has_condition)]
        available_interventions = get_unique_values(temp_df, 'interventions')

    # Get fully filtered dataframe
    fully_filtered_df = filter_trials_by_criteria(
        df, selected_sponsors, selected_conditions, selected_interventions)

    return {
        'sponsors': available_sponsors,
        'conditions': available_conditions,
        'interventions': available_interventions,
        'filtered_df': fully_filtered_df
    }


def parse_date(date_str) -> Optional[datetime]:
    """Parse date string in YYYY-MM-DD format."""
    try:
        if not date_str or pd.isna(date_str):
            return None
        return datetime.strptime(str(date_str), '%Y-%m-%d')
    except (ValueError, AttributeError, TypeError):
        return None


def get_trial_detail(df: pd.DataFrame, trial_id: str) -> Optional[pd.Series]:
    """Get trial details for a specific trial ID."""
    trial = df[df['trial_id'] == trial_id]
    if trial.empty:
        return None
    return trial.iloc[0]


def create_status_timeline(trial: pd.Series) -> Optional[Tuple[go.Figure, dict]]:
    """Create a horizontal timeline bar showing status duration.

    For now, shows time in current status from publication to today.
    Structure allows for historical status tracking as data accumulates.
    """

    # Extract dates
    published_str = trial.get('published_date')
    last_ingested_str = trial.get('last_ingested')
    current_status = trial.get('status', 'unknown').lower().strip()

    published_date = parse_date(published_str)
    if not published_date:
        return None, {'error': 'Invalid or missing publication date'}

    if last_ingested_str:
        last_ingested_date = datetime.strptime(
            last_ingested_str, '%Y-%m-%d %H:%M:%S')
    else:
        last_ingested_date = datetime.now()

    # Calculate duration in current status (days)
    duration_days = (last_ingested_date - published_date).days

    # Define colors for each status
    status_colors = {
        'not yet recruiting': '#1f77b4',      # Blue
        'recruiting': '#ff7f0e',               # Orange
        'enrolling by invitation': '#2ca02c',  # Green
        'active, not recruiting': '#d62728',  # Red
        'witheld': '#9467bd',                  # Purple
        'withdrawn': '#8c564b',                # Brown
        'completed': '#17becf'                 # Cyan
    }

    color = status_colors.get(current_status, '#999999')

    # Create horizontal timeline bar
    fig = go.Figure()

    # Add a single bar segment showing time in current status
    fig.add_trace(go.Bar(
        x=[duration_days],
        y=['Status Timeline'],
        orientation='h',
        marker=dict(
            color=color,
            line=dict(color='rgba(0,0,0,0.3)', width=2)
        ),
        text=f"{current_status.title()}<br>{duration_days} days",
        textposition='inside',
        hovertemplate='<b>Status:</b> %{customdata[0]}<br>' +
                     '<b>Duration:</b> %{x} days<br>' +
                     '<b>From:</b> %{customdata[1]}<br>' +
                     '<b>To:</b> %{customdata[2]}<extra></extra>',
        customdata=[[
            current_status.title(),
            published_date.strftime('%Y-%m-%d'),
            last_ingested_date.strftime('%Y-%m-%d')
        ]] * 1
    ))

    fig.update_layout(
        title=f'Time in Current Status: {current_status.title()}',
        xaxis_title='Days Since Publication',
        yaxis_title='',
        height=300,
        showlegend=False,
        plot_bgcolor='white',
        hovermode='x unified',
        margin=dict(l=100, r=50, t=50, b=50)
    )

    fig.update_yaxes(showticklabels=False)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    metadata = {
        'published_date': published_date.strftime('%Y-%m-%d'),
        'last_ingested': last_ingested_date.strftime('%Y-%m-%d %H:%M:%S'),
        'days_in_current_status': duration_days,
        'current_status': current_status.title()
    }

    return fig, metadata


def display_individual_trial_tracking():
    """Display individual trial status tracking."""
    st.set_page_config(page_title="Trial Status Tracker", layout="wide")
    st.title("Individual Clinical Trial Status Tracker")
    st.markdown("Search for a specific trial ID.")

    # Load data
    df = load_data()

    if df.empty:
        st.error("No data available")
        return

    # Get all trial IDs
    all_trial_ids = get_all_trial_ids(df)

    # Search/filter for trial ID
    st.subheader("Select Trial")
    selected_trial_id = st.selectbox(
        "Search for Trial ID",
        options=all_trial_ids,
        help="Select a trial ID to view its details"
    )

    if selected_trial_id:
        trial = get_trial_detail(df, selected_trial_id)

        if trial is not None:
            st.subheader(f"Trial: {selected_trial_id}")

            # Basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Status:** {trial.get('status', 'N/A')}")
            with col2:
                st.write(
                    f"**Published:** {trial.get('published_date', 'N/A')}")
            with col3:
                st.write(
                    f"**Last Ingested:** {str(trial.get('last_ingested', 'N/A'))[:10]}")

            # Title
            if pd.notna(trial.get('title')):
                st.markdown(f"**Title:** {trial.get('title')}")

            # Sponsors
            sponsors = convert_dynamodb_list_to_python(
                trial.get('sponsors', []))
            if sponsors:
                st.write(f"**Sponsors:** {', '.join(sponsors)}")

            # Conditions
            conditions = convert_dynamodb_list_to_python(
                trial.get('conditions', []))
            if conditions:
                st.write(f"**Therapeutic Areas:** {', '.join(conditions)}")

            # Interventions
            interventions = convert_dynamodb_list_to_python(
                trial.get('interventions', []))
            if interventions:
                st.write(f"**Interventions:** {', '.join(interventions)}")

            # HTML Link
            source_link = trial.get('source_link')
            if source_link:
                st.markdown(f"[🔗 View on ClinicalTrials.gov]({source_link})")

            # Display timeline
            st.subheader("Status Timeline")
            fig, metadata = create_status_timeline(trial)

            if fig and 'error' not in metadata:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Could not generate timeline: " +
                           metadata.get('error', 'Unknown error'))
        else:
            st.error(f"Trial ID {selected_trial_id} not found")


if __name__ == "__main__":
    display_individual_trial_tracking()
