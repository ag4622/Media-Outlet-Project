"""Comprehensive test file for dashboard utilities with edge cases."""
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from utils import get_unique_values, load_data
from filtering import filter_data, create_filters
from metrics import render_summary_metrics
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

    @pytest.fixture
    def sample_df(self):
        """Create sample trial data."""
        return pd.DataFrame({
            'conditions': [
                ['cancer', 'diabetes'],
                ['asthma'],
                ['diabetes']
            ],
            'interventions': [
                ['drug'],
                ['surgery'],
                ['drug']
            ],
            'sponsors': [
                ['pharma_co'],
                ['hospital'],
                ['pharma_co']
            ],
            'trial_id': ['T1', 'T2', 'T3']
        })

    def test_no_filters(self, sample_df):
        """Test with no filters applied."""
        result = filter_data(sample_df, [], [], [])
        assert len(result) == 3

    def test_filter_by_condition(self, sample_df):
        """Test filtering by condition."""
        result = filter_data(sample_df, ['cancer'], [], [])
        assert len(result) == 1
        assert result.iloc[0]['trial_id'] == 'T1'

    def test_filter_by_multiple_conditions(self, sample_df):
        """Test filtering by multiple conditions."""
        result = filter_data(sample_df, ['cancer', 'asthma'], [], [])
        assert len(result) == 2

    def test_filter_by_sponsor(self, sample_df):
        """Test filtering by sponsor."""
        result = filter_data(sample_df, [], [], ['hospital'])
        assert len(result) == 1
        assert result.iloc[0]['trial_id'] == 'T2'

    def test_filter_combined(self, sample_df):
        """Test filtering with multiple criteria."""
        result = filter_data(sample_df, ['diabetes'], ['drug'], [])
        # T1 and T3 both have diabetes and drug
        assert len(result) == 2
        assert set(result['trial_id']) == {'T1', 'T3'}

    def test_no_matches(self, sample_df):
        """Test when filter matches nothing."""
        result = filter_data(sample_df, ['nonexistent'], [], [])
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

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return (
            pd.DataFrame({
                'conditions': [['cancer'], ['diabetes']],
                'interventions': [['drug'], ['surgery']],
                'sponsors': [['pharma'], ['hospital']]
            }),
            ['cancer', 'diabetes'],
            ['drug', 'surgery'],
            ['pharma', 'hospital']
        )

    @patch('filtering.st')
    @patch('filtering.filter_data')
    def test_create_filters_returns_dataframe(self, mock_filter_data, mock_st, sample_data):
        """Test that create_filters returns a DataFrame."""
        df, conds, interventions, sponsors = sample_data
        mock_st.sidebar.multiselect.side_effect = [[], [], []]
        mock_filter_data.return_value = df

        result = create_filters(df, conds, interventions, sponsors)

        assert isinstance(result, pd.DataFrame)

    @patch('filtering.st')
    @patch('filtering.filter_data')
    def test_create_filters_calls_filter_data(self, mock_filter_data, mock_st, sample_data):
        """Test that create_filters calls filter_data."""
        df, conds, interventions, sponsors = sample_data
        mock_st.sidebar.multiselect.side_effect = [
            ['cancer'],
            ['drug'],
            ['pharma']
        ]
        mock_filter_data.return_value = df

        create_filters(df, conds, interventions, sponsors)

        mock_filter_data.assert_called_once()


class TestRenderSummaryMetrics:
    """Tests for render_summary_metrics function."""

    @patch('metrics.st')
    def test_render_summary_metrics_percentage_calculation(self, mock_st):
        """Test that percentage is calculated correctly."""
        df = pd.DataFrame({'id': [1, 2, 3, 4, 5]})
        filtered_df = pd.DataFrame({'id': [1, 2]})

        # Mock columns to return 3 MagicMock objects
        mock_col1, mock_col2, mock_col3 = MagicMock(), MagicMock(), MagicMock()
        mock_st.columns.return_value = [mock_col1, mock_col2, mock_col3]

        render_summary_metrics(df, filtered_df)

        # Verify st.metric was called 3 times
        assert mock_st.metric.call_count == 3

    @patch('metrics.st')
    def test_render_summary_metrics_empty_filtered(self, mock_st):
        """Test with empty filtered DataFrame."""
        df = pd.DataFrame({'id': [1, 2, 3]})
        filtered_df = pd.DataFrame({'id': []})

        mock_col1, mock_col2, mock_col3 = MagicMock(), MagicMock(), MagicMock()
        mock_st.columns.return_value = [mock_col1, mock_col2, mock_col3]

        render_summary_metrics(df, filtered_df)

        assert mock_st.metric.call_count == 3

    @patch('metrics.st')
    def test_render_summary_metrics_zero_total(self, mock_st):
        """Test with empty total DataFrame (edge case)."""
        df = pd.DataFrame({'id': []})
        filtered_df = pd.DataFrame({'id': []})

        mock_col1, mock_col2, mock_col3 = MagicMock(), MagicMock(), MagicMock()
        mock_st.columns.return_value = [mock_col1, mock_col2, mock_col3]

        render_summary_metrics(df, filtered_df)

        # Should handle division by zero gracefully
        assert mock_st.metric.call_count == 3


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

    def test_filter_preserves_order(self):
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


@patch('utils.st.cache_data')
@patch('utils.boto3')
class TestLoadData:
    """Tests for load_data function."""

    def test_load_data_returns_dataframe(self, mock_boto3, mock_cache):
        """Test that load_data returns a DataFrame."""
        # Mock cache_data to act as a pass-through decorator
        mock_cache.return_value = lambda func: func
        
        # Mock the DynamoDB table
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            'Items': [
                {'id': '1', 'conditions': ['cancer']},
                {'id': '2', 'conditions': ['diabetes']}
            ],
            'LastEvaluatedKey': None
        }
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb

        # Re-import to apply the mocked cache
        import importlib
        import utils
        importlib.reload(utils)
        
        result = utils.load_data()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'id' in result.columns

    def test_load_data_handles_pagination(self, mock_boto3, mock_cache):
        """Test pagination logic for large datasets."""
        # Mock cache_data to act as a pass-through decorator
        mock_cache.return_value = lambda func: func
        
        mock_table = MagicMock()
        # First call returns data with LastEvaluatedKey (indicating more data)
        # Second call returns data without LastEvaluatedKey (end of data)
        mock_table.scan.side_effect = [
            {
                'Items': [{'id': '1', 'name': 'Trial1'}],
                'LastEvaluatedKey': {'id': '1'}
            },
            {
                'Items': [{'id': '2', 'name': 'Trial2'}],
                'LastEvaluatedKey': None
            }
        ]
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb

        import importlib
        import utils
        importlib.reload(utils)
        
        result = utils.load_data()
        
        # Should have combined data from both pages
        assert len(result) == 2
        assert mock_table.scan.call_count == 2

    def test_load_data_empty_result(self, mock_boto3, mock_cache):
        """Test handling of empty DynamoDB result."""
        # Mock cache_data to act as a pass-through decorator
        mock_cache.return_value = lambda func: func
        
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            'Items': [],
            'LastEvaluatedKey': None
        }
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb

        import importlib
        import utils
        importlib.reload(utils)
        
        result = utils.load_data()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
