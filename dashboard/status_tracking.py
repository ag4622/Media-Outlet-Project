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
    st.markdown(
        "Search for a specific trial ID to view its status timeline.")

    # Load data
    df = load_data()

    if df.empty:
        st.error("No data available")
        return

    # Get all trial IDs
    trial_ids = get_all_trial_ids(df)

    if not trial_ids:
        st.error("No trial IDs found in database")
        return

    # Search/filter for trial ID
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_trial_id = st.selectbox(
            "Search for Trial ID",
            options=trial_ids,
            help="Select a trial ID to view its status timeline",
            key="trial_search"
        )

    with col2:
        if st.button("Search", use_container_width=True):
            pass  # Trigger re-run

    if selected_trial_id:
        trial = get_trial_detail(df, selected_trial_id)

        if trial is not None:
            # Display trial information
            st.subheader(f"Trial: {selected_trial_id}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", trial.get('status', 'N/A').title())
            with col2:
                st.metric("Published", trial.get('published_date', 'N/A'))
            with col3:
                st.metric("Last Ingested", trial.get(
                    'last_ingested', 'N/A')[:10])

            # Display title
            if pd.notna(trial.get('title')):
                st.markdown(f"**Title:** {trial.get('title')}")

            # Display timeline
            st.subheader("Status Timeline")
            fig, metadata = create_status_timeline(trial)

            if fig and 'error' not in metadata:
                st.plotly_chart(fig, use_container_width=True)

                # Display metadata
                with st.expander("Timeline Details"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.text(f"Published: {metadata['published_date']}")
                    with col2:
                        st.text(f"Last Updated: {metadata['last_ingested']}")
                    with col3:
                        st.text(
                            f"Current Status: {metadata['current_status']}")
                    with col4:
                        st.text(
                            f"Days in Status: {metadata['days_in_current_status']}")
            else:
                st.warning("Could not generate timeline: " +
                           metadata.get('error', 'Unknown error'))

            # Display additional trial details
            with st.expander("Full Trial Details"):
                trial_dict = trial.to_dict()
                # Clean up for display - filter out raw_description and None/NaN values
                display_data = {}
                for k, v in trial_dict.items():
                    if k not in ['raw_description']:
                        # Skip None values
                        if v is None:
                            continue
                        # Skip NaN values for scalar types
                        try:
                            if pd.isna(v):
                                continue
                        except (ValueError, TypeError):
                            # For non-scalar types (lists, dicts), keep them
                            pass
                        display_data[k] = v
                st.json(display_data)
        else:
            st.error(f"Trial ID {selected_trial_id} not found")


if __name__ == "__main__":
    display_individual_trial_tracking()
