"""Tests for extract.py."""

from unittest.mock import patch
from extract import fetch_clinical_trials_rss, extract


class TestFetchClinicalTrialsRSS:
    """Tests for fetch_clinical_trials_rss function."""

    @patch('extract.feedparser.parse')
    def test_fetch_clinical_trials_rss_success(self, mock_parse):
        """Test successful RSS feed fetch."""
        mock_feed = {
            'entries': [{'id': 'NCT12345', 'title': 'Test Study'}],
            'feed': {'title': 'Clinical Trials'}
        }
        mock_parse.return_value = mock_feed

        result = fetch_clinical_trials_rss()

        assert result == mock_feed
        mock_parse.assert_called_once()

    @patch('extract.feedparser.parse')
    def test_fetch_clinical_trials_rss_custom_url(self, mock_parse):
        """Test fetch with custom URL."""
        custom_url = "https://example.com/rss"
        mock_parse.return_value = {'entries': []}

        fetch_clinical_trials_rss(custom_url)

        mock_parse.assert_called_once_with(custom_url)

    @patch('extract.feedparser.parse')
    def test_fetch_clinical_trials_rss_exception(self, mock_parse):
        """Test exception handling in fetch."""
        mock_parse.side_effect = OSError("Network error")

        result = fetch_clinical_trials_rss()

        assert result is None


class TestExtract:
    """Tests for extract function."""

    @patch('extract.fetch_clinical_trials_rss')
    def test_extract_success(self, mock_fetch):
        """Test successful extraction of entries."""
        mock_entries = [
            {'id': 'NCT12345', 'title': 'Study 1'},
            {'id': 'NCT67890', 'title': 'Study 2'}
        ]
        mock_fetch.return_value = {'entries': mock_entries}

        result = extract()

        assert len(result) == 2
        assert result == mock_entries

    @patch('extract.fetch_clinical_trials_rss')
    def test_extract_no_entries(self, mock_fetch):
        """Test extraction when feed has no entries."""
        mock_fetch.return_value = {'entries': None}

        result = extract()

        assert result is None

    @patch('extract.fetch_clinical_trials_rss')
    def test_extract_fetch_failure(self, mock_fetch):
        """Test extraction when fetch returns None."""
        mock_fetch.return_value = None

        result = extract()

        assert result == []

    @patch('extract.fetch_clinical_trials_rss')
    def test_extract_custom_url(self, mock_fetch):
        """Test extraction with custom URL."""
        mock_fetch.return_value = {'entries': []}
        custom_url = "https://example.com/rss"

        extract(custom_url)

        mock_fetch.assert_called_once_with(custom_url)

    @patch('extract.fetch_clinical_trials_rss')
    def test_extract_returns_list(self, mock_fetch):
        """Test that extract returns a list."""
        mock_entries = [{'id': 'NCT12345'}]
        mock_fetch.return_value = {'entries': mock_entries}

        result = extract()

        assert isinstance(result, list)
        assert len(result) == 1


class TestExtractEdgeCases:
    """Edge case tests for extract function."""

    @patch('extract.fetch_clinical_trials_rss')
    def test_extract_empty_feed_dict(self, mock_fetch):
        """Test extraction with empty feed dictionary."""
        mock_fetch.return_value = {}

        result = extract()

        assert result is None

    @patch('extract.fetch_clinical_trials_rss')
    def test_extract_entries_none(self, mock_fetch):
        """Test extraction when entries value is None."""
        mock_fetch.return_value = {'entries': None}

        result = extract()

        assert result is None

    @patch('extract.fetch_clinical_trials_rss')
    def test_extract_entries_not_list(self, mock_fetch):
        """Test extraction when entries is not a list."""
        mock_fetch.return_value = {'entries': 'not a list'}

        result = extract()

        assert result == 'not a list'

    @patch('extract.fetch_clinical_trials_rss')
    def test_extract_large_number_of_entries(self, mock_fetch):
        """Test extraction with many entries."""
        mock_entries = [{'id': f'NCT{i:05d}'} for i in range(1000)]
        mock_fetch.return_value = {'entries': mock_entries}

        result = extract()

        assert len(result) == 1000
        assert result[0]['id'] == 'NCT00000'
        assert result[999]['id'] == 'NCT00999'

    @patch('extract.fetch_clinical_trials_rss')
    def test_extract_entries_with_missing_fields(self, mock_fetch):
        """Test extraction with incomplete entry objects."""
        mock_entries = [
            {},  # Empty entry
            {'id': 'NCT123'},  # Only ID
            {'id': 'NCT456', 'title': 'Study'},  # Partial
        ]
        mock_fetch.return_value = {'entries': mock_entries}

        result = extract()

        assert len(result) == 3
        assert result[0] == {}
        assert result[1] == {'id': 'NCT123'}
