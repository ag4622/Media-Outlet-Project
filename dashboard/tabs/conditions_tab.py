"""Conditions tab for the dashboard."""

import streamlit as st
import plotly.express as px
import pandas as pd


def get_trial_counts_by_category(df, category) -> pd.DataFrame:
    """Get trial counts grouped by a specific category."""
    counts = {}
    for value in df.get(category, []):
        items = value if isinstance(value, list) else []
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


def render_conditions_tab(filtered_df):
    """Render the Trials by Condition tab."""
    st.subheader("Trial Counts by Condition")
    condition_counts = get_trial_counts_by_category(filtered_df, 'conditions')

    if not condition_counts.empty:
        top_conditions = get_top_n(condition_counts, n=10)
        st.markdown("### Top 10 Conditions")

        if not top_conditions.empty:
            top_conditions_reversed = top_conditions.iloc[::-1]
            fig_top = px.bar(
                top_conditions_reversed,
                x='Trial Count',
                y='Conditions',
                orientation='h',
                title="Top 10 Conditions",
                labels={'Conditions': 'Condition',
                        'Trial Count': 'Number of Trials'},
                color='Trial Count',
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig_top, width='stretch')

        with st.expander("View All Conditions"):
            st.dataframe(condition_counts, width='stretch')
    else:
        st.info("No data available for the selected filters.")
