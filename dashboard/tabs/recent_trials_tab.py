"""Recent Trials tab for the dashboard."""

import streamlit as st


def get_recent_trial_info(df):
    """Get the trials from that were published today with title and link."""
    most_recent_date = df['published_date'].max()
    recent_trials = df[df['published_date'] ==
                       most_recent_date][['title', 'source_link']].reset_index(drop=True)
    return recent_trials


def render_recent_trials(df):
    """Render the most recent trials tab."""
    st.subheader("Most Recent Trials")
    recent_trials = get_recent_trial_info(df)

    if not recent_trials.empty:
        # Add filter by title
        search_title = st.text_input(
            "🔍 Filter by title keyword",
            placeholder="e.g., cancer, cardiovascular, diabetes..."
        )

        # Filter based on search term
        if search_title:
            filtered_trials = recent_trials[
                recent_trials['title'].str.contains(
                    search_title, case=False, na=False)
            ].copy()
        else:
            filtered_trials = recent_trials.copy()

        # Rename columns for display
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
