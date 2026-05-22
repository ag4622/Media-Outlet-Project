"""Status tracking tab for the dashboard."""

import streamlit as st
import pandas as pd
import boto3
import plotly.graph_objects as go
from datetime import datetime
from typing import Optional, Dict, List

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('c23-ClinicalTrialTracker')

# Status color mapping
STATUS_COLORS = {
    'not yet recruiting': '#1f77b4',
    'recruiting': '#ff7f0e',
    'enrolling by invitation': '#2ca02c',
    'active, not recruiting': '#d62728',
    'withheld': '#9467bd',
    'withdrawn': '#8c564b',
    'completed': '#17becf'
}


@st.cache_data(ttl=0)
def load_all_trials() -> pd.DataFrame:
    """Load all clinical trials data from DynamoDB."""
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


def get_trial_by_id(df: pd.DataFrame, trial_id: str) -> Optional[Dict]:
    """Get a specific trial by its ID from the cached DataFrame."""
    match = df[df['trial_id'] == trial_id]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def format_list_field(value) -> str:
    """Format list fields for display."""
    if isinstance(value, list):
        if not value:
            return "N/A"
        return ", ".join(str(v) for v in value)
    elif isinstance(value, str):
        return value if value else "N/A"
    return "N/A"


def parse_date(date_value) -> Optional[datetime]:
    """Parse date from various formats."""
    if isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, str):
        try:
            return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            try:
                return datetime.strptime(date_value, '%Y-%m-%d')
            except (ValueError, AttributeError):
                return None
    return None


def extract_status_history(trial_data: Dict) -> List[Dict]:
    """Extract status history from trial data."""
    status_history = []

    if 'status_history' in trial_data and isinstance(trial_data['status_history'], list):
        for entry in trial_data['status_history']:
            if isinstance(entry, dict) and 'status' in entry and 'date' in entry:
                status_history.append({
                    'status': entry['status'].lower(),
                    'date': parse_date(entry['date'])
                })

    if not status_history:
        current_status = trial_data.get(
            'current_status') or trial_data.get('status')
        if current_status:
            ingested_date = parse_date(trial_data.get('ingested_date'))
            published_date = parse_date(trial_data.get('published_date'))
            start_date = ingested_date or published_date
            if start_date:
                status_history.append({
                    'status': current_status.lower(),
                    'date': start_date
                })

    status_history.sort(key=lambda x: x['date'] or datetime.min)
    return status_history


def calculate_status_durations(status_history: List[Dict]) -> List[Dict]:
    """Calculate duration for each status period."""
    if not status_history:
        return []

    durations = []
    now = datetime.now()

    for i, entry in enumerate(status_history):
        status = entry['status']
        start_date = entry['date']

        if not start_date:
            continue

        if i + 1 < len(status_history):
            end_date = status_history[i + 1]['date']
        else:
            end_date = now

        if end_date:
            days = (end_date - start_date).days
            if days >= 0:
                durations.append({
                    'status': status,
                    'days': days,
                    'start_date': start_date,
                    'end_date': end_date
                })

    return durations


def create_status_timeline_chart(durations: List[Dict]) -> Optional[go.Figure]:
    """Create a horizontal stacked bar chart showing status durations."""
    if not durations:
        return None

    fig = go.Figure()

    for duration in durations:
        status = duration['status']
        days = duration['days']
        color = STATUS_COLORS.get(status, '#cccccc')

        fig.add_trace(go.Bar(
            x=[days],
            y=['Trial Status Timeline'],
            orientation='h',
            name=status.title(),
            marker=dict(color=color),
            text=f"{duration['status'].title()}<br>{days} days",
            textposition='inside',
            hovertemplate=(
                f"<b>{duration['status'].title()}</b><br>"
                f"Duration: {days} days<br>"
                f"From: {duration['start_date'].strftime('%Y-%m-%d')}<br>"
                f"To: {duration['end_date'].strftime('%Y-%m-%d')}<extra></extra>"
            ),
            showlegend=True
        ))

    fig.update_layout(
        barmode='stack',
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title='Days',
        yaxis_title='',
        hovermode='x unified',
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        font=dict(size=11)
    )

    return fig


def render_status_tracking():
    """Render the status tracking tab content."""
    st.header("📊 Clinical Trial Status Tracking")

    df = load_all_trials()

    if df.empty:
        st.warning("No trial data available.")
        return

    if 'trial_id' not in df.columns:
        st.error("Trial ID field not found in data.")
        return

    trial_ids = sorted(df['trial_id'].dropna().unique())

    selected_trial_id = st.selectbox(
        "🔍 Select a Trial",
        options=trial_ids,
        placeholder="Choose a trial ID...",
        index=None
    )

    if selected_trial_id:
        trial_data = get_trial_by_id(df, selected_trial_id)

        if trial_data:
            st.subheader("Trial Information")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Title:** {trial_data.get('title', 'N/A')}")
                st.markdown(
                    f"**Sponsors:** {format_list_field(trial_data.get('sponsors'))}")
                st.markdown(
                    f"**Therapeutic Areas:** {format_list_field(trial_data.get('therapeutic_areas'))}")

            with col2:
                st.markdown(
                    f"**Interventions:** {format_list_field(trial_data.get('interventions'))}")
                published_date = trial_data.get('published_date', 'N/A')
                st.markdown(f"**Published Date:** {published_date}")
                ingested_date = trial_data.get('ingested_date', 'N/A')
                st.markdown(f"**Ingested Date:** {ingested_date}")

            st.divider()

            st.subheader("Status Timeline")

            status_history = extract_status_history(trial_data)
            durations = calculate_status_durations(status_history)

            if durations:
                chart = create_status_timeline_chart(durations)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)

                st.subheader("Status Details")
                status_df = pd.DataFrame(durations)
                status_df['start_date'] = status_df['start_date'].dt.strftime(
                    '%Y-%m-%d')
                status_df['end_date'] = status_df['end_date'].dt.strftime(
                    '%Y-%m-%d')
                status_df = status_df.rename(columns={
                    'status': 'Status',
                    'days': 'Days',
                    'start_date': 'Start Date',
                    'end_date': 'End Date'
                })
                st.dataframe(status_df, use_container_width=True,
                             hide_index=True)
            else:
                st.info("No status history available for this trial.")
        else:
            st.error(f"Could not load data for trial ID: {selected_trial_id}")
    else:
        st.info(
            "👈 Select a trial from the dropdown to view its status tracking information.")
