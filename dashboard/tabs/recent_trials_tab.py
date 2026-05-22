"""Recent Trials tab for the dashboard."""

import streamlit as st
import pandas as pd


def get_recent_trial_info(df):
    """Get the trials from that were published today with title and link."""
    if df.empty:
        st.error("No data available")
        return pd.DataFrame()
    if 'published_date' not in df.columns:
        st.error("published_date column not found in data")
        return pd.DataFrame()
    if 'title' not in df.columns or 'source_link' not in df.columns:
        st.error("Required columns (title, source_link) not found in data")
        return pd.DataFrame()

    df_copy = df.copy()
    try:
        df_copy['published_date'] = pd.to_datetime(
            df_copy['published_date'], errors='coerce')
    except Exception as e:
        st.error(f"Error parsing dates: {e}")
        return pd.DataFrame()
    most_recent_date = df_copy['published_date'].max()
    if pd.isna(most_recent_date):
        st.error("No valid dates found in published_date column")
        return pd.DataFrame()
    recent_trials = df_copy[df_copy['published_date'] ==
                            most_recent_date][['title', 'source_link']].reset_index(drop=True)
    st.text(
        f"Latest trials published on: {most_recent_date.strftime('%B %d, %Y')}")
    return recent_trials


def render_recent_trials(df):
    """Render the most recent trials tab."""
    st.subheader("Most Recent Trials")
    recent_trials = get_recent_trial_info(df)

    if not recent_trials.empty:
        search_title = st.text_input(
            "🔍 Filter by title keyword",
            placeholder="e.g., cancer, cardiovascular, diabetes..."
        )

        if search_title:
            filtered_trials = recent_trials[
                recent_trials['title'].str.contains(
                    search_title, case=False, na=False)
            ].copy()
        else:
            filtered_trials = recent_trials.copy()

        filtered_trials = filtered_trials.rename(columns={
            'title': 'Title',
            'source_link': 'Link'
        })

        st.dataframe(
            filtered_trials,
            column_config={
                "Title": st.column_config.TextColumn("Title"),
                "Link": st.column_config.LinkColumn("View Trial")
            },
            hide_index=True,
            width='stretch'
        )

        if search_title and filtered_trials.empty:
            st.info(f"No trials found matching '{search_title}'")
    else:
        st.info("No recent trials found.")
