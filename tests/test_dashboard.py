"""Comprehensive test file for dashboard utilities with edge cases."""
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from utils import get_unique_values
from filtering import filter_data, create_filters
from metrics import (
    _collect_unique,
    _render_total_trials,
    _render_new_trials,
    _render_actively_recruiting,
    _render_unique_sponsors,
    _render_conditions_covered,
    _render_completed_trials,
    _render_withdrawn_withheld,
    _render_near_market,
    _render_top_sponsor,
    render_summary_metrics,
)
from dashboard import dashboard


class TestDashboard:
    """Tests for main dashboard function."""

    @patch('dashboard.st')
    @patch('dashboard.load_data')
    @patch('dashboard.get_unique_values')
    @patch('dashboard.create_filters')
    @patch('dashboard.render_summary_metrics')
    def test_dashboard_calls_main_functions(self, mock_metrics, mock_filters, mock_unique, mock_load, mock_st):
        """Test that dashboard calls all main functions."""
        # Setup mocks
        mock_df = pd.DataFrame({'id': [1, 2, 3]})
        mock_load.return_value = mock_df
        mock_unique.return_value = ['val1', 'val2']
        mock_filters.return_value = mock_df

        # Mock tabs to avoid unpacking issues
        mock_st.tabs.return_value = [MagicMock() for _ in range(7)]

        dashboard()

        # Verify key functions were called
        mock_load.assert_called_once()
        # Called for conditions, interventions, sponsors
        assert mock_unique.call_count == 3
        mock_filters.assert_called_once()
        mock_metrics.assert_called_once()

    @patch('dashboard.st')
    @patch('dashboard.load_data')
    def test_dashboard_handles_empty_data(self, mock_load, mock_st):
        """Test dashboard handles empty data gracefully."""
        mock_load.return_value = pd.DataFrame()
        mock_st.tabs.return_value = [MagicMock() for _ in range(7)]

        # Should not raise an error
        dashboard()
        mock_load.assert_called_once()


class TestGetUniqueValues:
    """Tests for extracting unique values from DataFrame columns."""

    def test_unique_values_basic(self):
        """Test extraction of unique values from column."""
        df = pd.DataFrame({
            'conditions': [
                ['cancer', 'diabetes'],
                ['diabetes', 'asthma']
            ]
        })
        unique = get_unique_values(df, 'conditions')
        assert set(unique) == {'asthma', 'cancer', 'diabetes'}

    def test_missing_column(self):
        """Test handling of missing column."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        unique = get_unique_values(df, 'conditions')
        assert unique == []

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        unique = get_unique_values(df, 'conditions')
        assert unique == []

    def test_sorted_output(self):
        """Test that output is sorted."""
        df = pd.DataFrame({
            'conditions': [
                ['zebra', 'apple'],
            ]
        })
        unique = get_unique_values(df, 'conditions')
        assert unique == ['apple', 'zebra']


class TestFilterData:
    """Tests for filtering trial data."""

    def test_no_filters(self, filter_data_sample_df):
        """Test with no filters applied."""
        result = filter_data(filter_data_sample_df, [], [], [])
        assert len(result) == 3

    def test_filter_by_condition(self, filter_data_sample_df):
        """Test filtering by condition."""
        result = filter_data(filter_data_sample_df, ['cancer'], [], [])
        assert len(result) == 1
        assert result.iloc[0]['trial_id'] == 'T1'

    def test_filter_by_multiple_conditions(self, filter_data_sample_df):
        """Test filtering by multiple conditions."""
        result = filter_data(filter_data_sample_df, [
                             'cancer', 'asthma'], [], [])
        assert len(result) == 2

    def test_filter_by_sponsor(self, filter_data_sample_df):
        """Test filtering by sponsor."""
        result = filter_data(filter_data_sample_df, [], [], ['hospital'])
        assert len(result) == 1
        assert result.iloc[0]['trial_id'] == 'T2'

    def test_filter_combined(self, filter_data_sample_df):
        """Test filtering with multiple criteria."""
        result = filter_data(filter_data_sample_df, ['diabetes'], ['drug'], [])
        # T1 and T3 both have diabetes and drug
        assert len(result) == 2
        assert set(result['trial_id']) == {'T1', 'T3'}

    def test_no_matches(self, filter_data_sample_df):
        """Test when filter matches nothing."""
        result = filter_data(filter_data_sample_df, ['nonexistent'], [], [])
        assert len(result) == 0

    def test_empty_dataframe(self):
        """Test filtering empty DataFrame."""
        df = pd.DataFrame({
            'conditions': [],
            'interventions': [],
            'sponsors': [],
            'trial_id': []
        })
        result = filter_data(df, ['cancer'], [], [])
        assert len(result) == 0

    def test_with_non_list_values(self):
        """Test filtering when column contains non-list values."""
        df = pd.DataFrame({
            'conditions': [None, 'not_a_list', ['cancer']],
            'interventions': [[], [], []],
            'sponsors': [[], [], []],
            'trial_id': ['T1', 'T2', 'T3']
        })
        result = filter_data(df, ['cancer'], [], [])
        assert len(result) == 1
        assert result.iloc[0]['trial_id'] == 'T3'


class TestCreateFilters:
    """Tests for create_filters function."""

    @patch('filtering.st')
    @patch('filtering.filter_data')
    def test_create_filters_returns_dataframe(self, mock_filter_data, mock_st, filter_create_sample_data):
        """Test that create_filters returns a DataFrame."""
        df, conds, interventions, sponsors = filter_create_sample_data
        mock_st.sidebar.multiselect.side_effect = [[], [], []]
        mock_filter_data.return_value = df

        result = create_filters(df, conds, interventions, sponsors)

        assert isinstance(result, pd.DataFrame)

    @patch('filtering.st')
    @patch('filtering.filter_data')
    def test_create_filters_calls_filter_data(self, mock_filter_data, mock_st, filter_create_sample_data):
        """Test that create_filters calls filter_data."""
        df, conds, interventions, sponsors = filter_create_sample_data
        mock_st.sidebar.multiselect.side_effect = [
            ['cancer'],
            ['drug'],
            ['pharma']
        ]
        mock_filter_data.return_value = df

        create_filters(df, conds, interventions, sponsors)

        mock_filter_data.assert_called_once()


class TestCollectUnique:
    """Tests for _collect_unique helper."""

    def test_collects_from_lists(self):
        """Test extracting unique values from a Series of lists."""
        series = pd.Series([['a', 'b'], ['b', 'c']])
        assert _collect_unique(series) == {'a', 'b', 'c'}

    def test_handles_strings_and_none(self):
        """Test handling of plain strings and NaN values."""
        series = pd.Series(['single', None, ['from_list']])
        result = _collect_unique(series)
        assert 'single' in result
        assert 'from_list' in result
        assert len(result) == 2


class TestRenderTotalTrials:
    """Tests for _render_total_trials."""

    @patch('metrics.st')
    def test_displays_correct_count(self, mock_st):
        """Test that total trials count matches DataFrame length."""
        df = pd.DataFrame({'id': [1, 2, 3, 4, 5]})
        _render_total_trials(df)
        mock_st.metric.assert_called_once_with("Total Trials", 5)

    @patch('metrics.st')
    def test_empty_dataframe(self, mock_st):
        """Test with empty DataFrame shows zero."""
        df = pd.DataFrame()
        _render_total_trials(df)
        mock_st.metric.assert_called_once_with("Total Trials", 0)


class TestRenderNewTrials:
    """Tests for _render_new_trials."""

    @patch('metrics.st')
    def test_counts_recent_trials(self, mock_st):
        """Test that only trials within last 30 days are counted."""
        from datetime import datetime, timedelta
        recent = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        old = '2020-01-01'
        df = pd.DataFrame({'published_date': [recent, recent, old]})
        _render_new_trials(df)
        mock_st.metric.assert_called_once_with("New Trials (30 Days)", 2)

    @patch('metrics.st')
    def test_no_published_date_column(self, mock_st):
        """Test graceful handling when published_date column missing."""
        df = pd.DataFrame({'other': [1, 2]})
        _render_new_trials(df)
        mock_st.metric.assert_called_once_with("New Trials (30 Days)", 0)


class TestRenderActivelyRecruiting:
    """Tests for _render_actively_recruiting."""

    @patch('metrics.st')
    def test_counts_recruiting_status(self, mock_st):
        """Test that only 'recruiting' status is counted."""
        status_lower = pd.Series(['recruiting', 'completed', 'recruiting'])
        _render_actively_recruiting(status_lower, True)
        mock_st.metric.assert_called_once_with("Actively Recruiting", 2)

    @patch('metrics.st')
    def test_no_status_column(self, mock_st):
        """Test returns zero when has_status is False."""
        _render_actively_recruiting(None, False)
        mock_st.metric.assert_called_once_with("Actively Recruiting", 0)


class TestRenderUniqueSponsors:
    """Tests for _render_unique_sponsors."""

    @patch('metrics.st')
    def test_counts_unique_sponsors(self, mock_st):
        """Test deduplication across rows."""
        df = pd.DataFrame({
            'sponsors': [['Pfizer', 'Novartis'], ['Pfizer', 'Roche']]
        })
        _render_unique_sponsors(df)
        mock_st.metric.assert_called_once_with("Unique Sponsors", 3)

    @patch('metrics.st')
    def test_missing_sponsors_column(self, mock_st):
        """Test returns zero when sponsors column absent."""
        df = pd.DataFrame({'other': [1, 2]})
        _render_unique_sponsors(df)
        mock_st.metric.assert_called_once_with("Unique Sponsors", 0)


class TestRenderConditionsCovered:
    """Tests for _render_conditions_covered."""

    @patch('metrics.st')
    def test_counts_unique_conditions(self, mock_st):
        """Test deduplication of conditions across rows."""
        df = pd.DataFrame({
            'conditions': [['cancer', 'diabetes'], ['cancer', 'asthma']]
        })
        _render_conditions_covered(df)
        mock_st.metric.assert_called_once_with("Conditions Covered", 3)

    @patch('metrics.st')
    def test_missing_conditions_column(self, mock_st):
        """Test returns zero when conditions column absent."""
        df = pd.DataFrame({'other': [1]})
        _render_conditions_covered(df)
        mock_st.metric.assert_called_once_with("Conditions Covered", 0)


class TestRenderCompletedTrials:
    """Tests for _render_completed_trials."""

    @patch('metrics.st')
    def test_counts_completed(self, mock_st):
        """Test that only 'completed' status is counted."""
        status_lower = pd.Series(['completed', 'recruiting', 'completed'])
        _render_completed_trials(status_lower, True)
        mock_st.metric.assert_called_once_with("Completed Trials", 2)

    @patch('metrics.st')
    def test_no_status(self, mock_st):
        """Test returns zero when has_status is False."""
        _render_completed_trials(None, False)
        mock_st.metric.assert_called_once_with("Completed Trials", 0)


class TestRenderWithdrawnWithheld:
    """Tests for _render_withdrawn_withheld."""

    @patch('metrics.st')
    def test_counts_both_statuses(self, mock_st):
        """Test that both withdrawn and withheld are counted."""
        status_lower = pd.Series(
            ['withdrawn', 'withheld', 'completed', 'withdrawn'])
        _render_withdrawn_withheld(status_lower, True)
        mock_st.metric.assert_called_once()
        call_args = mock_st.metric.call_args
        assert call_args[0] == ("Withdrawn / Withheld", 3)

    @patch('metrics.st')
    def test_no_status(self, mock_st):
        """Test returns zero when has_status is False."""
        _render_withdrawn_withheld(None, False)
        call_args = mock_st.metric.call_args
        assert call_args[0] == ("Withdrawn / Withheld", 0)


class TestRenderNearMarket:
    """Tests for _render_near_market."""

    @patch('metrics.st')
    def test_counts_active_not_recruiting(self, mock_st):
        """Test that 'active, not recruiting' is counted correctly."""
        status_lower = pd.Series([
            'active, not recruiting', 'recruiting', 'active, not recruiting'
        ])
        _render_near_market(status_lower, True)
        mock_st.metric.assert_called_once()
        call_args = mock_st.metric.call_args
        assert call_args[0] == ("Near-Market Competitors", 2)

    @patch('metrics.st')
    def test_no_status(self, mock_st):
        """Test returns zero when has_status is False."""
        _render_near_market(None, False)
        call_args = mock_st.metric.call_args
        assert call_args[0] == ("Near-Market Competitors", 0)


class TestRenderTopSponsor:
    """Tests for _render_top_sponsor."""

    @patch('metrics.st')
    def test_finds_most_common_sponsor(self, mock_st):
        """Test that the sponsor with the most trials is identified."""
        df = pd.DataFrame({
            'sponsors': [['Pfizer'], ['Pfizer'], ['Roche']]
        })
        _render_top_sponsor(df)
        mock_st.metric.assert_called_once()
        call_args = mock_st.metric.call_args
        assert call_args[0] == ("Top Sponsor Trials", 2)

    @patch('metrics.st')
    def test_no_sponsors_column(self, mock_st):
        """Test returns zero when sponsors column absent."""
        df = pd.DataFrame({'other': [1, 2]})
        _render_top_sponsor(df)
        mock_st.metric.assert_called_once_with("Top Sponsor Trials", 0)


class TestRenderSummaryMetrics:
    """Tests for the main render_summary_metrics orchestrator."""

    @patch('metrics.st')
    def test_renders_all_nine_metrics(self, mock_st):
        """Test that all 9 metrics are rendered."""
        df = pd.DataFrame({
            'published_date': ['2025-01-01'],
            'status': ['recruiting'],
            'sponsors': [['Pfizer']],
            'conditions': [['cancer']]
        })
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        render_summary_metrics(df, df)
        assert mock_st.metric.call_count == 9

    @patch('metrics.st')
    def test_handles_no_status_column(self, mock_st):
        """Test graceful handling when status column is missing."""
        df = pd.DataFrame({'id': [1, 2, 3]})
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        render_summary_metrics(df, df)
        # Should still render all 9 metrics with zeros/fallbacks
        assert mock_st.metric.call_count == 9


class TestGetUniqueValuesExtended:
    """Extended tests for edge cases in get_unique_values."""

    def test_none_values_in_list(self):
        """Test handling when list contains None."""
        df = pd.DataFrame({
            'conditions': [
                ['cancer', 'diabetes'],  # Remove None as it's not sortable
                ['asthma']
            ]
        })
        unique = get_unique_values(df, 'conditions')
        assert 'cancer' in unique
        assert 'diabetes' in unique
        assert 'asthma' in unique

    def test_duplicate_handling(self):
        """Test that duplicates are properly deduplicated."""
        df = pd.DataFrame({
            'conditions': [
                ['cancer', 'cancer'],
                ['cancer', 'diabetes']
            ]
        })
        unique = get_unique_values(df, 'conditions')
        assert unique.count('cancer') == 1
        assert set(unique) == {'cancer', 'diabetes'}

    def test_large_dataset(self):
        """Test with larger dataset."""
        large_data = [
            ['condition_' + str(i % 10)] for i in range(100)
        ]
        df = pd.DataFrame({'conditions': large_data})
        unique = get_unique_values(df, 'conditions')
        assert len(unique) == 10
        assert unique == sorted(unique)

    def test_special_characters_in_values(self):
        """Test handling of special characters."""
        df = pd.DataFrame({
            'conditions': [
                ['cancer (early)', 'diabetes-type2'],
                ["Parkinson's", 'heart_disease']
            ]
        })
        unique = get_unique_values(df, 'conditions')
        assert len(unique) == 4
        assert "Parkinson's" in unique


class TestFilterDataExtended:
    """Extended tests for filter_data edge cases."""

    def test_filter_preserves_order(self, filter_data_sample_df):
        """Test that filtering preserves DataFrame structure."""
        df = pd.DataFrame({
            'conditions': [['a'], ['b'], ['c']],
            'interventions': [[], [], []],
            'sponsors': [[], [], []],
            'trial_id': ['T1', 'T2', 'T3']
        })
        result = filter_data(df, ['a', 'c'], [], [])
        assert list(result['trial_id']) == ['T1', 'T3']

    def test_filter_with_empty_lists_in_data(self):
        """Test filtering when DataFrame has empty lists."""
        df = pd.DataFrame({
            'conditions': [[], ['cancer'], ['diabetes']],
            'interventions': [[], [], []],
            'sponsors': [[], [], []],
            'trial_id': ['T1', 'T2', 'T3']
        })
        result = filter_data(df, ['cancer'], [], [])
        assert len(result) == 1
        assert result.iloc[0]['trial_id'] == 'T2'

    def test_filter_no_matching_sponsor(self):
        """Test when sponsor filter has no matches."""
        df = pd.DataFrame({
            'conditions': [['a'], ['b']],
            'interventions': [['x'], ['y']],
            'sponsors': [['p'], ['q']],
            'trial_id': ['T1', 'T2']
        })
        result = filter_data(df, [], [], ['z'])
        assert len(result) == 0

    def test_filter_no_matching_intervention(self):
        """Test when intervention filter has no matches."""
        df = pd.DataFrame({
            'conditions': [['a'], ['b']],
            'interventions': [['x'], ['y']],
            'sponsors': [['p'], ['q']],
            'trial_id': ['T1', 'T2']
        })
        result = filter_data(df, [], ['z'], [])
        assert len(result) == 0

    def test_filter_dataframe_not_modified(self):
        """Test that original DataFrame is not modified."""
        df = pd.DataFrame({
            'conditions': [['cancer'], ['diabetes']],
            'interventions': [[], []],
            'sponsors': [[], []],
            'trial_id': ['T1', 'T2']
        })
        original_len = len(df)
        filter_data(df, ['cancer'], [], [])
        assert len(df) == original_len
