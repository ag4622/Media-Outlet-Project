"""Creates a streamlit dashboard to display the latest clinical trials data."""

import streamlit as st
from utils import load_data, get_unique_values
from filtering import create_filters
from metrics import render_summary_metrics
from tabs.conditions_tab import render_conditions_tab
from tabs.interventions_tab import render_interventions_tab
from tabs.sponsors_tab import render_sponsors_tab
from tabs.recent_trials_tab import render_recent_trials
from tabs.trial_data_tab import render_trial_data_tab
from tabs.chatbot_tab import render_chatbot_tab


def dashboard():
    """Main function to create the clinical trials dashboard."""
    st.set_page_config(page_title="Clinical Trials Dashboard", layout="wide")
    st.title("Clinical Trials Dashboard")
    st.markdown(
        """This dashboard displays clinical trials data from clinicaltrials.gov
        with filtering and analytics.""")

    # Load data
    df = load_data()

    # Get unique values for filters
    unique_conditions = get_unique_values(df, 'conditions')
    unique_interventions = get_unique_values(df, 'interventions')
    unique_sponsors = get_unique_values(df, 'sponsors')

    # Create sidebar filters and filter data
    filtered_df = create_filters(
        df, unique_conditions, unique_interventions, unique_sponsors)

    # Display summary metrics
    render_summary_metrics(df, filtered_df)

    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Trials by Condition", "Trials by Intervention",
            "Trials by Sponsor", "Recent Trials", "Trial Data", "Clinical Trials Assistant"]
    )

    with tab1:
        render_conditions_tab(filtered_df)

    with tab2:
        render_interventions_tab(filtered_df)

    with tab3:
        render_sponsors_tab(filtered_df)

    with tab4:
        render_recent_trials(df)

    with tab5:
        render_trial_data_tab(df, filtered_df)

    with tab6:
        render_chatbot_tab()


if __name__ == "__main__":
    dashboard()
