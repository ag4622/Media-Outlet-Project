"""Trial Data tab for the dashboard."""

import streamlit as st


def render_trial_data_tab(df, filtered_df):
    """Render the Trial Data tab."""
    st.subheader("Latest Clinical Trials")
    st.dataframe(df.head())

    st.subheader("Filtered Trial Data")
    st.dataframe(filtered_df, width='stretch')
