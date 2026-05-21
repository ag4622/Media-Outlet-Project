"""Creates a streamlit dashboard to display the latest clinical trials data."""

import streamlit as st
import pandas as pd
import boto3
import plotly.express as px

# Initialize DynamoDB resource at module level
dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('c23-ClinicalTrialTracker')


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
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
    if "messages" not in st.session_state:
        st.session_state.messages = []

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

        st.subheader("Clinical Trials Assistant")

        st.markdown("""
        Ask questions about:
        - clinical trials
        - sponsors
        - interventions
        - conditions
        - recent publications

        The chatbot does not store context between questions, so please include all relevant details in each question.
        """)

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Scrollable chat container
        chat_container = st.container(height=600)

        # Render chat history
        with chat_container:

            for message in st.session_state.messages:

                with st.chat_message(message["role"]):

                    st.markdown(message["content"])

        # Chat input at bottom
        if prompt := st.chat_input("Ask a question about clinical trials..."):

            # Save user message
            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })

            # Immediately render user message
            with chat_container:

                with st.chat_message("user"):

                    st.markdown(prompt)

            # Assistant response
            with chat_container:

                with st.chat_message("assistant"):

                    with st.spinner("Searching clinical trials knowledge base..."):

                        try:

                            # Ask RAG system
                            rag_response = ask_rag(question=prompt)

                            # Handle dict or string response
                            if isinstance(rag_response, dict):

                                answer = rag_response.get(
                                    "answer",
                                    "No answer returned."
                                )

                            else:

                                answer = str(rag_response)

                            # Display answer
                            st.markdown(answer)

                            # Save assistant response
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer
                            })

                        except Exception as e:

                            error_message = f"Error: {str(e)}"

                            st.error(error_message)

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": error_message
                            })

            # Refresh app
            st.rerun()

if __name__ == "__main__":
    dashboard()
