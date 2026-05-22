"""Metrics display for the dashboard."""

import streamlit as st
from datetime import datetime, timedelta


def render_summary_metrics(df, filtered_df):
    """Display key metrics for clinical trial monitoring."""
    st.subheader("Key Metrics")

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
        recruiting = len(
            filtered_df[filtered_df['status'].str.lower() == 'recruiting']
        ) if 'status' in filtered_df.columns else 0
        st.metric("Actively Recruiting", recruiting)

    col4, col5, col6 = st.columns(3)

    with col4:
        if 'sponsors' in filtered_df.columns:
            sponsors = set()
            for s in filtered_df['sponsors'].dropna():
                if isinstance(s, list):
                    sponsors.update(s)
            st.metric("Unique Sponsors", len(sponsors))
        else:
            st.metric("Unique Sponsors", 0)

    with col5:
        if 'conditions' in filtered_df.columns:
            conditions = set()
            for c in filtered_df['conditions'].dropna():
                if isinstance(c, list):
                    conditions.update(c)
            st.metric("Conditions Covered", len(conditions))
        else:
            st.metric("Conditions Covered", 0)

    with col6:
        completed = len(
            filtered_df[filtered_df['status'].str.lower() == 'completed']
        ) if 'status' in filtered_df.columns else 0
        st.metric("Completed Trials", completed)

    # Strategic metrics for competitive intelligence
    col7, col8, col9 = st.columns(3)

    with col7:
        # Withdrawn/Withheld — signals failed programmes in a space
        failed = len(
            filtered_df[filtered_df['status'].str.lower().isin(
                ['withdrawn', 'withheld'])]
        ) if 'status' in filtered_df.columns else 0
        st.metric("Withdrawn / Withheld", failed,
                  help="Trials that were pulled. High numbers in a "
                       "therapeutic area may signal scientific risk — "
                       "or whitespace if your team has solved the problem.")

    with col8:
        # Near-market threats — trials done recruiting, crunching data
        near_market = len(
            filtered_df[filtered_df['status'].str.lower()
                        == 'active, not recruiting']
        ) if 'status' in filtered_df.columns else 0
        st.metric("Near-Market Competitors", near_market,
                  help="Trials in data analysis phase — expect regulatory "
                       "filings and product launches from these soon.")

    with col9:
        # Top sponsor concentration — how many trials the biggest player has
        if 'sponsors' in filtered_df.columns:
            from collections import Counter
            sponsor_counts = Counter()
            for s in filtered_df['sponsors'].dropna():
                if isinstance(s, list):
                    sponsor_counts.update(s)
            if sponsor_counts:
                top_sponsor, top_count = sponsor_counts.most_common(1)[0]
                st.metric("Top Sponsor Trials", top_count,
                          help=f"Most active sponsor: {top_sponsor}. "
                          "Shows who dominates the filtered space.")
            else:
                st.metric("Top Sponsor Trials", 0)
        else:
            st.metric("Top Sponsor Trials", 0)
