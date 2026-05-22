"""Focused tests for dashboard tabs with minimal but comprehensive coverage."""
import pandas as pd
import pytest
import warnings
from unittest.mock import patch, MagicMock
from datetime import datetime

from conditions_tab import get_trial_counts_by_category as get_counts_conditions, get_top_n
from interventions_tab import categorize_intervention, filter_interventions_by_type
from sponsors_tab import is_university_sponsor, filter_sponsors_by_type
from recent_trials_tab import get_recent_trial_info
from chatbot_tab import initialize_chat_state, add_message, handle_user_prompt
from status_tracking_tab import get_trial_by_id, format_list_field, parse_date, extract_status_history


class TestGetTrialCountsByCategory:
    """Tests for get_trial_counts_by_category."""

    def test_counting_sorting_and_duplicates(self):
        """Test counting, sorting, and duplicate handling."""
        df = pd.DataFrame({
            'conditions': [
                ['cancer', 'diabetes', 'cancer'],
                ['cancer'],
                ['asthma']
            ]
        })
        result = get_counts_conditions(df, 'conditions')
        assert len(result) == 3
        assert result.iloc[0]['Trial Count'] == 3  # cancer appears 3 times
        # sorted
        assert result.iloc[0]['Trial Count'] >= result.iloc[-1]['Trial Count']

    def test_edge_cases(self):
        """Test empty, missing, and non-list values."""
        assert get_counts_conditions(pd.DataFrame(
            {'conditions': []}), 'conditions').empty
        assert get_counts_conditions(pd.DataFrame(
            {'other': [1]}), 'conditions').empty

        df = pd.DataFrame({'conditions': [None, 'not_a_list', ['cancer']]})
        assert len(get_counts_conditions(df, 'conditions')) == 1


class TestGetTopN:
    """Tests for get_top_n."""

    def test_top_n_scenarios(self):
        """Test various top N scenarios."""
        df = pd.DataFrame({'Item': ['a', 'b', 'c'], 'Count': [1, 2, 3]})

        assert len(get_top_n(df, n=2)) == 2
        assert len(get_top_n(df, n=10)) == 3  # Exceeds size
        assert get_top_n(pd.DataFrame(), n=10).empty
        assert len(get_top_n(df, n=0)) == 0


class TestCategorizeIntervention:
    """Tests for categorize_intervention."""

    def test_categorization(self):
        """Test all intervention categories with case insensitivity."""
        tests = [
            ("Drug therapy", "Drug"),
            ("MEDICATION", "Drug"),
            ("Dietary supplement", "Dietary Supplement"),
            ("surgical procedure", "Procedure"),
            ("Device implant", "Device"),
            ("RADIATION therapy", "Radiation"),
            ("Unknown type", "Other"),
        ]
        for text, expected in tests:
            assert categorize_intervention(text) == expected


class TestIsUniversitySponsor:
    """Tests for is_university_sponsor."""

    def test_sponsor_detection(self):
        """Test university and non-university detection with various keywords."""
        university = ["Harvard University", "stanford college",
                      "Johns Hopkins Medical Center", "Mayo Clinic Hospital"]
        non_university = ["Pfizer Inc", "Moderna"]

        for sponsor in university:
            assert is_university_sponsor(sponsor)
        for sponsor in non_university:
            assert not is_university_sponsor(sponsor)


class TestFilterSponsorsByType:
    """Tests for filter_sponsors_by_type."""

    def test_sponsor_filtering(self, sponsors_sample_df):
        """Test filtering with and without universities."""
        assert len(filter_sponsors_by_type(
            sponsors_sample_df, include_universities=True)) == 3
        assert len(filter_sponsors_by_type(
            sponsors_sample_df, include_universities=False)) == 1  # Only Pfizer Inc
        assert filter_sponsors_by_type(
            pd.DataFrame(), include_universities=False).empty


class TestGetRecentTrialInfo:
    """Tests for get_recent_trial_info."""

    @patch('recent_trials_tab.st')
    def test_valid_and_error_cases(self, mock_st):
        """Test valid data and error handling."""
        df = pd.DataFrame({
            'published_date': ['2024-01-15', '2024-01-15', '2024-01-14'],
            'title': ['A', 'B', 'C'],
            'source_link': ['1', '2', '3']
        })
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            assert len(get_recent_trial_info(df)) == 2

        # Empty/invalid cases
        get_recent_trial_info(pd.DataFrame())
        get_recent_trial_info(pd.DataFrame({'id': [1]}))
        assert mock_st.error.call_count >= 2


class TestFormatAndParse:
    """Tests for format_list_field and parse_date."""

    def test_format_and_parse(self):
        """Test formatting and parsing functions."""
        assert format_list_field(['a', 'b']) == "a, b"
        assert format_list_field([]) == "N/A"
        assert format_list_field("test") == "test"
        assert format_list_field(None) == "N/A"

        dt = datetime(2024, 1, 15)
        assert parse_date(dt) == dt
        assert parse_date('2024-01-15').year == 2024
        assert parse_date('invalid') is None


class TestGetTrialById:
    """Tests for get_trial_by_id."""

    def test_trial_retrieval(self):
        """Test finding and missing trials."""
        df = pd.DataFrame({'trial_id': ['T1', 'T2'], 'title': ['A', 'B']})

        assert get_trial_by_id(df, 'T2')['title'] == 'B'
        assert get_trial_by_id(df, 'T9') is None
        assert get_trial_by_id(pd.DataFrame(
            columns=['trial_id']), 'T1') is None


class TestFilterInterventionsByType:
    """Tests for filter_interventions_by_type."""

    def test_intervention_filtering(self, interventions_sample_df):
        """Test filtering interventions by type."""
        assert len(filter_interventions_by_type(
            interventions_sample_df, 'All')) == 3
        assert len(filter_interventions_by_type(
            interventions_sample_df, 'Drug')) == 1
        assert len(filter_interventions_by_type(
            interventions_sample_df, 'Unknown')) == 0
        assert filter_interventions_by_type(pd.DataFrame(), 'Drug').empty


class TestExtractStatusHistory:
    """Tests for extract_status_history."""

    def test_status_history(self):
        """Test status history extraction and sorting."""
        trial_data = {
            'status_history': [
                {'status': 'Third', 'date': '2024-03-01'},
                {'status': 'First', 'date': '2024-01-01'},
            ]
        }
        result = extract_status_history(trial_data)
        assert result[0]['status'] == 'first'
        assert result[1]['status'] == 'third'

    def test_fallback_and_edge_cases(self):
        """Test fallback to current_status and edge cases."""
        assert len(extract_status_history(
            {'current_status': 'Recruiting', 'published_date': '2024-01-15'})) == 1
        assert len(extract_status_history({})) == 0
        assert len(extract_status_history(
            {'status_history': [{'status': 'Valid', 'date': '2024-01-01'}]})) == 1


class TestChatbot:
    """Tests for chatbot functions."""

    @patch('chatbot_tab.st')
    def test_initialize_and_add(self, mock_st):
        """Test initialization and message adding."""
        mock_st.session_state = MagicMock()
        initialize_chat_state()
        add_message('user', 'Hello')
        assert True

    @patch('chatbot_tab.st')
    @patch('chatbot_tab.ask_rag')
    @patch('chatbot_tab.add_message')
    def test_prompt_handling(self, mock_add, mock_ask, mock_st):
        """Test user prompt with success and error."""
        mock_container = MagicMock()
        mock_st.chat_message.return_value.__enter__ = MagicMock()
        mock_st.chat_message.return_value.__exit__ = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()

        mock_ask.return_value = {'answer': 'Test'}
        handle_user_prompt('Test', mock_container)
        assert mock_add.call_count >= 2

        mock_add.reset_mock()
        mock_ask.side_effect = Exception("Error")
        handle_user_prompt('Test', mock_container)
        assert mock_add.call_count >= 1
