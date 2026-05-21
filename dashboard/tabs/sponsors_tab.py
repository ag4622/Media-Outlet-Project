"""Sponsors tab for the dashboard."""

import streamlit as st
import plotly.express as px
import pandas as pd
from utils import convert_dynamodb_list_to_python


def get_trial_counts_by_category(df, category) -> pd.DataFrame:
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


def get_top_n(df_counts, n=10) -> pd.DataFrame:
    """Get top N items from counts."""
    if df_counts.empty:
        return pd.DataFrame()
    return df_counts.head(n)


def is_university_sponsor(sponsor_name) -> bool:
    """Check if sponsor is a university based on keywords."""
    university_keywords = ['university', 'college',
                           'institute', 'school of', 'medical center', 'hospital']
    sponsor_lower = sponsor_name.lower()
    return any(keyword in sponsor_lower for keyword in university_keywords)


def filter_sponsors_by_type(df_counts, include_universities=True) -> pd.DataFrame:
    """Filter sponsors based on university inclusion."""
    if df_counts.empty:
        return df_counts

    if include_universities:
        return df_counts
    else:
        # Filter out universities
        sponsor_col = df_counts.columns[0]
        return df_counts[~df_counts[sponsor_col].apply(is_university_sponsor)]


def render_sponsors_tab(filtered_df):
    """Render the Trials by Sponsor tab."""
    st.subheader("Trial Counts by Sponsor")

    include_universities = st.checkbox(
        "Include University Sponsors", value=True)
    sponsor_counts = get_trial_counts_by_category(filtered_df, 'sponsors')

    if not sponsor_counts.empty:
        filtered_sponsors = filter_sponsors_by_type(
            sponsor_counts, include_universities)

        if not filtered_sponsors.empty:
            top_sponsors = get_top_n(filtered_sponsors, n=10)
            st.markdown("### Top 10 Sponsors")

            if not top_sponsors.empty:
                top_sponsors_reversed = top_sponsors.iloc[::-1]
                fig_top = px.bar(
                    top_sponsors_reversed,
                    x='Trial Count',
                    y='Sponsors',
                    orientation='h',
                    title="Top 10 Sponsors",
                    labels={'Sponsors': 'Sponsor',
                            'Trial Count': 'Number of Trials'},
                    color='Trial Count',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig_top, width='stretch')

            with st.expander("View All Sponsors"):
                st.dataframe(filtered_sponsors, width='stretch')
        else:
            st.info("No sponsors match the current filter.")
    else:
        st.info("No data available for the selected filters.")
