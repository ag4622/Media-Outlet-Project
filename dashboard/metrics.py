"""Metrics display for the dashboard."""

import streamlit as st


def render_summary_metrics(df, filtered_df):
    """Display summary metrics for total and filtered trials."""
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trials", len(df))
    with col2:
        st.metric("Filtered Trials", len(filtered_df))
    with col3:
        st.metric("Trials Shown (%)",
                  f"{(len(filtered_df)/len(df)*100):.1f}%" if len(df) > 0 else "0%")
