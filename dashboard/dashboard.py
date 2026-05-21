"""Creates a streamlit dashboard to display the latest clinical trials data. """

import streamlit as st
import pandas as pd
import boto3
import plotly.express as px

# Initialize DynamoDB resource at module level
dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('c23-ClinicalTrialTracker')


@st.cache_data(ttl=3600)
def load_data(table_name="c23-ClinicalTrialTracker") -> pd.DataFrame:
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


@st.cache_data(ttl=3600)
def get_trials_sponsors() -> pd.DataFrame:
    """Get all trial IDs and sponsors with pagination."""
    all_items = []
    last_evaluated_key = None

    while True:
        scan_kwargs = {
            'ProjectionExpression': 'trial_id, sponsors'
        }
        if last_evaluated_key:
            scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

        response = table.scan(**scan_kwargs)
        all_items.extend(response.get('Items', []))

        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break

    return pd.DataFrame(all_items)


def get_sponsors_count() -> pd.DataFrame:
    """Get count of sponsors across all trials. Needs editing"""
    df = get_trials_sponsors()
    sponsor_counts = {}
    for sponsors in df['sponsors']:
        # sponsors is in DynamoDB format: {'L': [{'S': 'Sponsor Name'}, ...]}
        if isinstance(sponsors, dict) and 'L' in sponsors:
            for sponsor_item in sponsors['L']:
                if isinstance(sponsor_item, dict) and 'S' in sponsor_item:
                    sponsor_name = sponsor_item['S']
                    sponsor_counts[sponsor_name] = sponsor_counts.get(
                        sponsor_name, 0) + 1
    return pd.DataFrame(
        list(sponsor_counts.items()),
        columns=['Sponsor', 'Count']
    ).sort_values('Count', ascending=False)


def convert_dynamodb_list_to_python(value) -> list:
    """Convert DynamoDB list format to Python list."""
    if isinstance(value, dict) and 'L' in value:
        result = []
        for item in value['L']:
            if isinstance(item, dict) and 'S' in item:
                result.append(item['S'])
        return result
    elif isinstance(value, list):
        return value
    return []


def get_unique_values(df, column) -> list:
    """Get unique values from a column that may contain lists."""
    unique_values = set()
    for value in df.get(column, []):
        items = convert_dynamodb_list_to_python(value)
        unique_values.update(items)
    return sorted(list(unique_values))


def filter_data(df, selected_conditions, selected_interventions, selected_sponsors) -> pd.DataFrame:
    """Filter data based on selected conditions, interventions, and sponsors."""
    filtered_df = df.copy()

    # Filter by conditions
    if selected_conditions:
        def has_condition(conds):
            conds_list = convert_dynamodb_list_to_python(conds)
            return any(c in selected_conditions for c in conds_list)
        filtered_df = filtered_df[filtered_df['conditions'].apply(
            has_condition)]

    # Filter by interventions
    if selected_interventions:
        def has_intervention(interventions):
            interventions_list = convert_dynamodb_list_to_python(interventions)
            return any(i in selected_interventions for i in interventions_list)
        filtered_df = filtered_df[filtered_df['interventions'].apply(
            has_intervention)]

    # Filter by sponsors
    if selected_sponsors:
        def has_sponsor(sponsors):
            sponsors_list = convert_dynamodb_list_to_python(sponsors)
            return any(s in selected_sponsors for s in sponsors_list)
        filtered_df = filtered_df[filtered_df['sponsors'].apply(has_sponsor)]

    return filtered_df


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


def prepare_pie_chart_data(df_counts, top_n=10) -> pd.DataFrame:
    """Prepare data for pie chart with 'Other' grouping for items beyond top_n."""
    if df_counts.empty:
        return df_counts

    top_items = df_counts.head(top_n)
    other_count = df_counts.iloc[top_n:]['Trial Count'].sum()

    if other_count > 0:
        category_col = df_counts.columns[0]
        other_row = pd.DataFrame({
            category_col: ['Other'],
            'Trial Count': [other_count]
        })
        pie_data = pd.concat([top_items, other_row], ignore_index=True)
    else:
        pie_data = top_items

    return pie_data


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
    elif 'dietary' in intervention_lower or 'supplement' in intervention_lower or 'vitamin' in intervention_lower:
        return 'Dietary Supplement'
    elif 'procedure' in intervention_lower or 'surgery' in intervention_lower or 'behavioral' in intervention_lower:
        return 'Procedure'
    elif 'device' in intervention_lower:
        return 'Device'
    elif 'radiation' in intervention_lower:
        return 'Radiation'
    else:
        return 'Other'


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


def filter_interventions_by_type(df_counts, intervention_type='All') -> pd.DataFrame:
    """Filter interventions by type."""
    if df_counts.empty or intervention_type == 'All':
        return df_counts

    intervention_col = df_counts.columns[0]
    filtered = df_counts[df_counts[intervention_col].apply(
        lambda x: categorize_intervention(x) == intervention_type)]
    return filtered.sort_values('Trial Count', ascending=False)


def dashboard():
    """Main function to create the clinical trials dashboard."""
    st.set_page_config(page_title="Clinical Trials Dashboard", layout="wide")
    st.title("Clinical Trials Dashboard")
    st.markdown(
        "This dashboard displays clinical trials data from clinicaltrials.gov with filtering and analytics.")

    # Load data
    df = load_data()

    # Get unique values for filters
    unique_conditions = get_unique_values(df, 'conditions')
    unique_interventions = get_unique_values(df, 'interventions')
    unique_sponsors = get_unique_values(df, 'sponsors')

    # Create sidebar for filters
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

    # Filter data
    filtered_df = filter_data(df, selected_conditions,
                              selected_interventions, selected_sponsors)

    # Display summary metrics
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trials", len(df))
    with col2:
        st.metric("Filtered Trials", len(filtered_df))
    with col3:
        st.metric("Trials Shown (%)",
                  f"{(len(filtered_df)/len(df)*100):.1f}%" if len(df) > 0 else "0%")

    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Trials by Condition", "Trials by Intervention",
            "Trials by Sponsor", "Recent Trials", "Trial Data"]
    )

    with tab1:
        st.subheader("Trial Counts by Condition")
        condition_counts = get_trial_counts_by_category(
            filtered_df, 'conditions')
        if not condition_counts.empty:
            top_conditions = get_top_n(condition_counts, n=10)

            st.markdown("### Top 10 Conditions")
            if not top_conditions.empty:
                # Reverse to show highest at top
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

    with tab2:
        st.subheader("Trial Counts by Intervention")

        # Intervention type filter
        intervention_counts = get_trial_counts_by_category(
            filtered_df, 'interventions')

        if not intervention_counts.empty:
            # Get unique intervention types
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
                    # Reverse to show highest at top
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

    with tab3:
        st.subheader("Trial Counts by Sponsor")

        # Sponsor type filter
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
                    # Reverse to show highest at top
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

    with tab4:
        st.subheader("Most Recent Trials")
        render_recent_trials()

    with tab5:
        st.subheader("Latest Clinical Trials")
        st.dataframe(df.head())

        st.subheader("Filtered Trial Data")
        st.dataframe(filtered_df, width='stretch')


if __name__ == "__main__":
    dashboard()
