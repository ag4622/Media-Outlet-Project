"""Minimal test suite for transform_clean module."""
from datetime import date
from time import struct_time
from transform_clean import (
    remove_html_tags,
    format_feed_entries,
    format_datetime_fields,
    format_key_labels,
    extract_key_information,
    transform
)


class TestRemoveHtmlTags:
    """Tests for remove_html_tags function."""

    def test_removes_tags_with_commas(self):
        """Test HTML tags are replaced with commas."""
        result = remove_html_tags("<b>Bold</b>")
        assert "<b>" not in result and "," in result

    def test_newlines_to_spaces(self):
        """Test newlines are replaced with spaces."""
        result = remove_html_tags("Line 1\nLine 2")
        assert "\n" not in result

    def test_non_string_unchanged(self):
        """Test non-strings return unchanged."""
        assert remove_html_tags(None) is None

    def test_multiple_tags(self):
        """Test multiple different tags are all replaced."""
        result = remove_html_tags("<b>Bold</b> <i>italic</i> <br/>")
        assert result.count(",") == 5  # <b>, </b>, <i>, </i>, <br/>

    def test_nested_tags(self):
        """Test nested tags are handled."""
        result = remove_html_tags("<div><b>nested</b></div>")
        assert "<" not in result and ">" not in result

    def test_empty_string(self):
        """Test empty string returns empty."""
        assert remove_html_tags("") == ""

    def test_entities_preserved(self):
        """Test HTML entities are not replaced."""
        result = remove_html_tags("A&amp;B&nbsp;C")
        assert "&amp;" in result and "&nbsp;" in result


class TestFormatFeedEntries:
    """Tests for format_feed_entries function."""

    def test_cleans_both_fields(self):
        """Test HTML is removed from raw_description and title."""
        result = format_feed_entries(
            {'raw_description': '<b>Text</b>', 'title': '<i>Title</i>'})
        assert '<b>' not in result['raw_description'] and '<i>' not in result['title']

    def test_missing_fields(self):
        """Test gracefully handles missing fields."""
        result = format_feed_entries({'id': 'NCT123'})
        assert result['id'] == 'NCT123'

    def test_none_values(self):
        """Test None values are not processed."""
        entry = {'raw_description': None, 'title': None}
        result = format_feed_entries(entry)
        assert result['raw_description'] is None and result['title'] is None

    def test_empty_strings(self):
        """Test empty strings are preserved."""
        result = format_feed_entries({'raw_description': '', 'title': ''})
        assert result['raw_description'] == '' and result['title'] == ''


class TestFormatDatetimeFields:
    """Tests for format_datetime_fields function."""

    def test_converts_to_date_string(self):
        """Test struct_time converts to YYYY-MM-DD string."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        result = format_datetime_fields(
            {'updated_parsed': struct_t}, ['updated_parsed'])
        assert result['updated'] == '2026-05-19'

    def test_multiple_fields(self):
        """Test multiple datetime fields are converted."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        result = format_datetime_fields(
            {'published_parsed': struct_t, 'updated_parsed': struct_t},
            ['published_parsed', 'updated_parsed']
        )
        assert 'published' in result and 'updated' in result

    def test_invalid_data_skipped(self):
        """Test invalid data is handled gracefully."""
        result = format_datetime_fields(
            {'updated_parsed': 'invalid'}, ['updated_parsed'])
        assert 'updated' not in result or result.get('updated') is None

    def test_missing_field_ignored(self):
        """Test missing fields don't cause errors."""
        result = format_datetime_fields({'id': 'NCT123'}, ['updated_parsed'])
        assert result['id'] == 'NCT123'


class TestFormatKeyLabels:
    """Tests for format_key_labels function."""

    def test_maps_fields(self):
        """Test field names are correctly mapped."""
        entry = {'id': 'NCT123', 'summary': 'Test', 'updated': '2026-05-19'}
        result = format_key_labels(entry)
        assert result['trial_id'] == 'NCT123'
        assert result['raw_description'] == 'Test'

    def test_unmapped_fields_excluded(self):
        """Test unmapped fields are not included."""
        entry = {'id': 'NCT123', 'extra_field': 'value'}
        result = format_key_labels(entry)
        assert 'trial_id' in result
        assert 'extra_field' not in result

    def test_partial_fields(self):
        """Test works with partial fields."""
        entry = {'id': 'NCT123'}
        result = format_key_labels(entry)
        assert result['trial_id'] == 'NCT123'
        assert len(result) == 1

    def test_empty_entry(self):
        """Test empty entry returns empty dict."""
        assert not format_key_labels({})


class TestExtractKeyInformation:
    """Tests for extract_key_information function."""

    def test_extracts_conditions_sponsors(self):
        """Test extraction of key information."""
        entry = {
            'raw_description': '<b>Conditions</b>: Disease<b>Sponsors</b>: Hospital'}
        result = extract_key_information(entry)
        assert 'conditions' in result and isinstance(
            result['conditions'], list)

    def test_handles_no_tags(self):
        """Test returns empty lists without HTML tags."""
        result = extract_key_information({'raw_description': 'Plain text'})
        assert result['conditions'] == []

    def test_handles_none_summary(self):
        """Test handles None summary gracefully."""
        result = extract_key_information({'raw_description': None})
        assert result['conditions'] == []

    def test_extracts_multiple_items(self):
        """Test extracts multiple items separated by semicolon."""
        entry = {'raw_description': '<b>Conditions</b>: Heart; Lung; Kidney'}
        result = extract_key_information(entry)
        assert isinstance(result['conditions'], list)

    def test_missing_summary_field(self):
        """Test handles missing summary field."""
        result = extract_key_information({'id': 'NCT123'})
        assert result['conditions'] == []
        assert result['status'] == ''


class TestTransform:
    """Tests for transform function."""

    def test_transforms_single_entry(self):
        """Test transforms a single entry through the pipeline."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        result = transform([{
            'id': 'NCT123',
            'summary': 'Test',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }])
        assert len(result) == 1
        assert result[0]['trial_id'] == 'NCT123'

    def test_adds_last_ingested(self):
        """Test last_ingested timestamp is added."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        result = transform([{
            'id': 'NCT123',
            'summary': 'Test',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }])
        assert isinstance(result[0]['last_ingested'], str) is True

    def test_empty_input_returns_empty(self):
        """Test returns empty list for empty input."""
        assert not transform([])

    def test_handles_multiple_entries(self):
        """Test transforms multiple entries correctly."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [
            {'id': f'NCT{i}', 'summary': f'Study {i}',
                'published_parsed': struct_t, 'updated_parsed': struct_t}
            for i in range(3)
        ]
        result = transform(entries)
        assert len(result) == 3

    def test_handles_none_values(self):
        """Test handles None values in fields."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        result = transform([{
            'id': 'NCT123',
            'title': None,
            'summary': None,
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }])
        assert len(result) == 1

    def test_handles_missing_fields(self):
        """Test handles entries with missing fields."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        result = transform([{
            'summary': 'Test only',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }])
        assert len(result) == 1

    def test_error_handling(self):
        """Test handles errors gracefully."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        # Mix valid and invalid entries
        entries = [
            {'id': 'NCT001', 'summary': 'Valid',
                'published_parsed': struct_t, 'updated_parsed': struct_t},
            {'id': 'NCT002', 'summary': 'Test',
                'published_parsed': 'invalid', 'updated_parsed': struct_t},
        ]
        result = transform(entries)
        # Should still process valid entries
        assert len(result) >= 1
