"""Metrics display for the dashboard."""

from datetime import datetime, timedelta
from collections import Counter
import streamlit as st


def _collect_unique(series):
    """Collect unique items from a Series of lists, strings, or iterables."""
    unique = set()
    for value in series.dropna():
        if isinstance(value, (list, tuple, set)):
            unique.update(value)
        elif isinstance(value, str):
            unique.add(value)
    return unique


def render_summary_metrics(df, filtered_df):
    """Display key metrics for clinical trial monitoring."""
    st.subheader("Key Metrics")

    # Compute normalized status once for reuse across all metrics
    has_status = 'status' in filtered_df.columns
    if has_status:
        status_lower = filtered_df['status'].fillna('').str.lower()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Trials", len(df))

    with col2:
        if 'published_date' in df.columns:
            thirty_days_ago = (
                datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            new_trials = len(df[df['published_date'] >= thirty_days_ago])
        else:
            new_trials = 0
        st.metric("New Trials (30 Days)", new_trials)

    with col3:
        recruiting = (status_lower == 'recruiting').sum() if has_status else 0
        st.metric("Actively Recruiting", recruiting)

    col4, col5, col6 = st.columns(3)

    with col4:
        if 'sponsors' in filtered_df.columns:
            sponsors = _collect_unique(filtered_df['sponsors'])
            st.metric("Unique Sponsors", len(sponsors))
        else:
            st.metric("Unique Sponsors", 0)

    with col5:
        if 'conditions' in filtered_df.columns:
            conditions = _collect_unique(filtered_df['conditions'])
            st.metric("Conditions Covered", len(conditions))
        else:
            st.metric("Conditions Covered", 0)

    with col6:
        completed = (status_lower == 'completed').sum() if has_status else 0
        st.metric("Completed Trials", completed)

    # Strategic metrics for competitive intelligence
    col7, col8, col9 = st.columns(3)

    with col7:
        failed = status_lower.isin(
            ['withdrawn', 'withheld']).sum() if has_status else 0
        st.metric("Withdrawn / Withheld", failed,
                  help="Trials that were pulled. High numbers in a "
                       "therapeutic area may signal scientific risk — "
                       "or whitespace if your team has solved the problem.")

    with col8:
        near_market = (
            status_lower == 'active, not recruiting').sum() if has_status else 0
        st.metric("Near-Market Competitors", near_market,
                  help="Trials in data analysis phase — expect regulatory "
                       "filings and product launches from these soon.")

    with col9:
        # Top sponsor concentration — how many trials the biggest player has
        if 'sponsors' in filtered_df.columns:
            sponsor_counts = Counter()
            for value in filtered_df['sponsors'].dropna():
                if isinstance(value, (list, tuple, set)):
                    sponsor_counts.update(value)
                elif isinstance(value, str):
                    sponsor_counts[value] += 1
            if sponsor_counts:
                top_sponsor, top_count = sponsor_counts.most_common(1)[0]
                st.metric("Top Sponsor Trials", top_count,
                          help=f"Most active sponsor: {top_sponsor}. "
                          "Shows who dominates the filtered space.")
            else:
                st.metric("Top Sponsor Trials", 0)
        else:
            st.metric("Top Sponsor Trials", 0)
