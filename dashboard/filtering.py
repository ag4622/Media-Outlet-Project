"""Filtering logic for trial data."""

import streamlit as st
import pandas as pd


def filter_data(df, selected_conditions, selected_interventions, selected_sponsors) -> pd.DataFrame:
    """Filter data based on selected conditions, interventions, and sponsors."""
    filtered_df = df.copy()

    # Filter by conditions
    if selected_conditions:
        def has_condition(conds):
            conds_list = conds if isinstance(conds, list) else []
            return any(c in selected_conditions for c in conds_list)
        filtered_df = filtered_df[filtered_df['conditions'].apply(
            has_condition)]

    # Filter by interventions
    if selected_interventions:
        def has_intervention(interventions):
            interventions_list = interventions if isinstance(
                interventions, list) else []
            return any(i in selected_interventions for i in interventions_list)
        filtered_df = filtered_df[filtered_df['interventions'].apply(
            has_intervention)]

    # Filter by sponsors
    if selected_sponsors:
        def has_sponsor(sponsors):
            sponsors_list = sponsors if isinstance(sponsors, list) else []
            return any(s in selected_sponsors for s in sponsors_list)
        filtered_df = filtered_df[filtered_df['sponsors'].apply(has_sponsor)]

    return filtered_df


def create_filters(df, unique_conditions, unique_interventions, unique_sponsors) -> pd.DataFrame:
    """Create sidebar filters and apply filtering to the dataframe."""
    st.sidebar.header("Filters")

    selected_conditions = st.sidebar.multiselect(
        "Select Conditions",
        options=unique_conditions,
        help="Filter trials by medical conditions"
    )
    selected_interventions = st.sidebar.multiselect(
        "Select Interventions",
        options=unique_interventions,
        help="Filter trials by intervention types"
    )
    selected_sponsors = st.sidebar.multiselect(
        "Select Sponsors",
        options=unique_sponsors,
        help="Filter trials by trial sponsors"
    )

    filtered_df = filter_data(df, selected_conditions,
                              selected_interventions, selected_sponsors)

    return filtered_df
