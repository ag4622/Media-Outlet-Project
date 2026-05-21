"""Creates a streamlit dashboard to display the latest clinical trials data. """

import streamlit as st
import pandas as pd
import awswrangler as wr
import boto3
import altair as alt

# Initialize DynamoDB resource at module level
dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('c23-ClinicalTrialTracker')


@st.cache_data
def load_data(table_name="c23-ClinicalTrialTracker"):
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


def get_sponsors_count():
    """Get the count of each sponsor from the DynamoDB table."""
    df = load_data()[['sponsors', 'trial_id']]
    sponsor_counts = {}
    for sponsors_list in df['sponsors']:
        if isinstance(sponsors_list, list):
            for sponsor in sponsors_list:
                sponsor_counts[sponsor] = sponsor_counts.get(sponsor, 0) + 1
    result_df = pd.DataFrame(list(sponsor_counts.items()),
                             columns=['Sponsor', 'Count'])
    return result_df


def render_sponsor_counts_chart():
    """Render a bar chart of sponsor counts using Altair."""
    sponsor_counts_df = get_sponsors_count()
    sponsor_counts_df = sponsor_counts_df.sort_values(
        'Count', ascending=False).reset_index(drop=True).head(10)
    chart = alt.Chart(sponsor_counts_df).mark_bar().encode(
        x=alt.X('Sponsor:N', sort=list(sponsor_counts_df['Sponsor'])),
        y='Count:Q'
    ).properties(width=600, height=400)
    st.altair_chart(chart, width='stretch')


def dashboard():
    st.title("Clinical Trials Dashboard")
    st.markdown(
        "This dashboard displays the latest clinical trials data from clinicaltrials.gov.")

    # Load data
    df = load_data()
    st.subheader("Latest Clinical Trials")
    st.dataframe(df.head())

    st.subheader("Sponsor Counts")
    render_sponsor_counts_chart()


if __name__ == "__main__":
    dashboard()
