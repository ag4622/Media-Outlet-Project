"""Interventions tab for the dashboard."""

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


def categorize_intervention(intervention_text) -> str:
    """Categorize intervention by type based on text patterns."""
    intervention_lower = intervention_text.lower()

    if 'drug' in intervention_lower or 'medication' in intervention_lower:
        return 'Drug'
    if ('dietary' in intervention_lower or 'supplement' in intervention_lower
          or 'vitamin' in intervention_lower):
        return 'Dietary Supplement'
    if ('procedure' in intervention_lower or 'surgery' in intervention_lower
          or 'behavioral' in intervention_lower):
        return 'Procedure'
    if 'device' in intervention_lower:
        return 'Device'
    if 'radiation' in intervention_lower:
        return 'Radiation'
    return 'Other'


def filter_interventions_by_type(df_counts, intervention_type='All') -> pd.DataFrame:
    """Filter interventions by type."""
    if df_counts.empty or intervention_type == 'All':
        return df_counts

    intervention_col = df_counts.columns[0]
    filtered = df_counts[df_counts[intervention_col].apply(
        lambda x: categorize_intervention(x) == intervention_type)]
    return filtered.sort_values('Trial Count', ascending=False)


def render_interventions_tab(filtered_df):
    """Render the Trials by Intervention tab."""
    st.subheader("Trial Counts by Intervention")
    intervention_counts = get_trial_counts_by_category(
        filtered_df, 'interventions')

    if not intervention_counts.empty:
        all_types = sorted(intervention_counts['Interventions'].apply(
            categorize_intervention).unique().tolist())
        intervention_type = st.selectbox(
            "Filter by Intervention Type",
            options=['All'] + all_types,
            help="Select intervention type to filter the data"
        )

        filtered_interventions = filter_interventions_by_type(
            intervention_counts, intervention_type)

        if not filtered_interventions.empty:
            top_interventions = get_top_n(filtered_interventions, n=10)
            st.markdown("### Top 10 Interventions")

            if not top_interventions.empty:
                top_interventions_reversed = top_interventions.iloc[::-1]
                fig_top = px.bar(
                    top_interventions_reversed,
                    x='Trial Count',
                    y='Interventions',
                    orientation='h',
                    title="Top 10 Interventions",
                    labels={'Interventions': 'Intervention',
                            'Trial Count': 'Number of Trials'},
                    color='Trial Count',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig_top, width='stretch')

            with st.expander("View All Interventions"):
                st.dataframe(filtered_interventions, width='stretch')
        else:
            st.info("No data available for the selected intervention type.")
    else:
        st.info("No data available for the selected filters.")
