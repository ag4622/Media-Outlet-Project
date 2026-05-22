"""Trial Data tab for the dashboard."""

import streamlit as st


def render_trial_data_tab(filtered_df):
    """Render the Trial Data tab."""

    st.subheader("Filtered Trial Data")

    column_order = ['title', 'trial_id', 'published_date', 'status',
                    'conditions', 'interventions', 'sponsors', 'source_link', 'last_ingested']
    available_columns = [
        col for col in column_order if col in filtered_df.columns]
    display_df = filtered_df[available_columns]

    column_rename = {
        'title': 'Title',
        'trial_id': 'Trial ID',
        'published_date': 'Published Date',
        'status': 'Status',
        'conditions': 'Conditions',
        'interventions': 'Interventions',
        'sponsors': 'Sponsors',
        'source_link': 'Source Link',
        'last_ingested': 'Last Ingested'
    }
    display_df = display_df.rename(columns=column_rename)

    st.dataframe(
        display_df,
        hide_index=True,
        width='stretch',
        column_config={
            'Source Link': st.column_config.LinkColumn()
        }
    )
