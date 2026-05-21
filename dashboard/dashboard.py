"""Creates a streamlit dashboard to display the latest clinical trials data. """

import streamlit as st
import pandas as pd
import boto3

# Initialize DynamoDB resource at module level
dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('c23-ClinicalTrialTracker')


@st.cache_data
def load_data():
    """Load clinical trails data from the dynamodb table."""
    all_items = []
    last_evaluated_key = None

    while True:
        scan_kwargs = {}
        if last_evaluated_key:
            scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

        response = table.scan(**scan_kwargs)
        all_items.extend(response.get('Items', []))

        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break

    df = pd.DataFrame(all_items)
    return df


def get_recent_trial_info():
    """Get the trials from that were published today with title and link."""
    df = load_data()
    most_recent_date = df['published_date'].max()
    recent_trials = df[df['published_date'] ==
                       most_recent_date][['title', 'source_link']].reset_index(drop=True)
    return recent_trials


def render_recent_trials():
    """Render the most recent trials in the dashboard."""
    recent_trials = get_recent_trial_info()

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


def dashboard():
    """Main function to render the clinical trials dashboard."""
    st.title("Clinical Trials Dashboard")
    st.markdown(
        "This dashboard displays the latest clinical trials data from clinicaltrials.gov.")

    st.subheader("Most Recent Trials")
    render_recent_trials()


if __name__ == "__main__":
    dashboard()
