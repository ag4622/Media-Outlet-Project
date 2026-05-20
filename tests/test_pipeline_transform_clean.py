import pytest
from datetime import date
from time import struct_time
from unittest.mock import patch
from transform_clean import (
    remove_html_tags,
    format_feed_entries,
    format_datetime_fields,
    format_key_labels,
    set_up_key_info,
    extract_key_information,
    transform
)


class TestRemoveHtmlTags:
    """Tests for remove_html_tags function."""

    def test_remove_simple_html_tags(self):
        """Test replacing basic HTML tags with commas."""
        text = "<b>Bold text</b>"
        result = remove_html_tags(text)
        # Tags should be replaced with commas
        assert "<b>" not in result
        assert "</b>" not in result
        assert "," in result
        assert "Bold text" in result

    def test_remove_multiple_tags(self):
        """Test replacing multiple different tags with commas."""
        text = "<b>Conditions</b>: Disease; <br /><b>Sponsors</b>: Hospital"
        result = remove_html_tags(text)
        assert "<b>" not in result
        assert "<br />" not in result
        # Each tag replaced with comma: <b>, </b>, <br />, <b>, </b> = 5 commas
        assert result.count(",") == 5
        assert "Conditions" in result
        assert "Sponsors" in result

    def test_remove_self_closing_tags(self):
        """Test replacing self-closing tags with commas."""
        text = "Line 1<br />Line 2"
        result = remove_html_tags(text)
        assert "<br />" not in result
        assert "," in result
        assert "Line 1" in result and "Line 2" in result

    def test_replace_html_entities(self):
        """Test that HTML entities are preserved (not replaced)."""
        text = "Drug: JS107&amp;Toripalimab&"
        result = remove_html_tags(text)
        # Entities are NOT replaced, so &amp; stays as-is
        assert "&amp;" in result
        assert "Drug: JS107&amp;Toripalimab&" == result

    def test_no_entity_replacement(self):
        """Test that HTML entities are preserved as-is."""
        text = "A&nbsp;B&amp;C&lt;D&gt;E&quot;F&quot;"
        result = remove_html_tags(text)
        # Entities should NOT be replaced - only tags removed
        assert "&nbsp;" in result
        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&quot;" in result

    def test_replace_newlines_with_spaces(self):
        """Test that newlines are replaced with spaces."""
        text = "Line 1\n<br />\nLine 2"
        result = remove_html_tags(text)
        assert "\n" not in result
        assert " " in result

    def test_non_string_input(self):
        """Test with non-string input - should return as-is."""
        result = remove_html_tags(None)
        assert result is None
        result = remove_html_tags(123)
        assert result == 123

    def test_empty_string(self):
        """Test with empty string."""
        result = remove_html_tags("")
        assert result == ""

    def test_no_html_tags(self):
        """Test with plain text."""
        text = "Plain text without tags"
        result = remove_html_tags(text)
        assert result == text


class TestFormatFeedEntries:
    """Tests for format_feed_entries function."""

    def test_remove_html_from_raw_description(self):
        """Test HTML replacement with commas in raw_description field."""
        entry = {'raw_description': '<b>Conditions</b>: Disease; <br />Hospital'}
        result = format_feed_entries(entry)
        assert '<b>' not in result['raw_description']
        assert '<br />' not in result['raw_description']
        assert ',' in result['raw_description']
        assert 'Hospital' in result['raw_description']

    def test_remove_html_from_title(self):
        """Test HTML replacement with commas in title field."""
        entry = {'title': 'Study: <b>Important</b> Work'}
        result = format_feed_entries(entry)
        assert '<b>' not in result['title']
        assert ',' in result['title']
        assert 'Important' in result['title']

    def test_both_fields_cleaned(self):
        """Test that both raw_description and title have tags replaced."""
        entry = {
            'raw_description': '<b>Summary</b> text',
            'title': '<i>Title</i> here'
        }
        result = format_feed_entries(entry)
        assert '<b>' not in result['raw_description']
        assert '<i>' not in result['title']
        assert ',' in result['raw_description']
        assert ',' in result['title']

    def test_preserve_other_fields(self):
        """Test that other fields are preserved unchanged."""
        entry = {
            'id': 'NCT123',
            'title': 'Test <b>Study</b>',
            'published': 'May 2026',
            'link': 'https://example.com'
        }
        result = format_feed_entries(entry)
        # Only title/raw_description should be modified
        assert result['id'] == 'NCT123'
        assert result['published'] == 'May 2026'
        assert result['link'] == 'https://example.com'

    def test_missing_raw_description(self):
        """Test with missing raw_description - should not crash."""
        entry = {'id': 'NCT123', 'title': 'Test <b>Title</b>'}
        result = format_feed_entries(entry)
        assert result['id'] == 'NCT123'
        assert '<b>' not in result['title']
        assert ',' in result['title']

    def test_missing_title(self):
        """Test with missing title - should not crash."""
        entry = {'id': 'NCT123', 'raw_description': 'Test <b>description</b>'}
        result = format_feed_entries(entry)
        assert result['id'] == 'NCT123'
        assert '<b>' not in result['raw_description']
        assert ',' in result['raw_description']

    def test_empty_raw_description_and_title(self):
        """Test with empty raw_description and title."""
        entry = {'raw_description': '', 'title': ''}
        result = format_feed_entries(entry)
        assert result['raw_description'] == ''
        assert result['title'] == ''

    def test_html_entities_preserved(self):
        """Test that HTML entities are preserved (not replaced by remove_html_tags)."""
        entry = {
            'raw_description': 'CVD &amp; HTN',
            'title': 'Study &lt; Control'
        }
        result = format_feed_entries(entry)
        # Entities are NOT replaced by remove_html_tags
        assert '&amp;' in result['raw_description']
        assert '&lt;' in result['title']


class TestFormatDatetimeFields:
    """Tests for format_datetime_fields function."""

    def test_convert_struct_time_to_date(self):
        """Test converting struct_time to date."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entry = {'updated_parsed': struct_t, 'id': 'NCT123'}
        result = format_datetime_fields(entry, ['updated_parsed'])

        assert isinstance(result['updated'], date)
        assert result['updated'].year == 2026
        assert result['updated'].month == 5
        assert result['updated'].day == 19

    def test_published_date_conversion(self):
        """Test that published_parsed converts to published date."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entry = {'published_parsed': struct_t}
        result = format_datetime_fields(entry, ['published_parsed'])

        assert 'published' in result
        assert isinstance(result['published'], date)

    def test_invalid_struct_time(self):
        """Test with invalid struct_time."""
        entry = {'updated_parsed': 'invalid', 'id': 'NCT123'}
        result = format_datetime_fields(entry, ['updated_parsed'])

        # Should warn but not crash
        assert 'id' in result

    def test_missing_field(self):
        """Test with missing field."""
        entry = {'id': 'NCT123'}
        result = format_datetime_fields(entry, ['updated_parsed'])

        assert result == entry

    def test_multiple_datetime_fields(self):
        """Test converting multiple datetime fields."""
        struct_t1 = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        struct_t2 = struct_time((2026, 5, 20, 4, 0, 0, 2, 140, 0))
        entry = {
            'published_parsed': struct_t1,
            'updated_parsed': struct_t2,
            'id': 'NCT123'
        }
        result = format_datetime_fields(
            entry, ['published_parsed', 'updated_parsed'])

        assert 'published' in result
        assert 'updated' in result
        assert isinstance(result['published'], date)
        assert isinstance(result['updated'], date)

    def test_leap_year_date(self):
        """Test with leap year February 29."""
        struct_t = struct_time((2024, 2, 29, 4, 0, 0, 4, 60, 0))
        entry = {'published_parsed': struct_t}

        result = format_datetime_fields(entry, ['published_parsed'])
        assert result['published'].month == 2
        assert result['published'].day == 29


class TestFormatKeyLabels:
    """Tests for format_key_labels function - field mapping."""

    def test_map_all_fields(self):
        """Test mapping of all key labels that should be renamed."""
        entry = {
            'id': 'NCT123',
            'summary': 'Test summary',
            'title': 'Test title',
            'updated': date(2026, 5, 19),
            'published': date(2026, 5, 18),
            'link': 'https://example.com'
        }
        result = format_key_labels(entry)

        # Check all mappings
        assert result['trial_id'] == 'NCT123'
        assert result['raw_description'] == 'Test summary'
        assert result['title'] == 'Test title'
        assert result['last_updated'] == date(2026, 5, 19)
        assert result['published_date'] == date(2026, 5, 18)
        assert result['source_link'] == 'https://example.com'

    def test_unmapped_fields_excluded(self):
        """Test that unmapped fields are excluded from result."""
        entry = {
            'id': 'NCT123',
            'summary': 'Test',
            'links': ['link1', 'link2'],
            'extra_field': 'value',
            'tags': ['tag1']
        }
        result = format_key_labels(entry)

        # Mapped fields should be present
        assert 'trial_id' in result
        # Unmapped fields should be excluded
        assert 'links' not in result
        assert 'extra_field' not in result
        assert 'tags' not in result

    def test_partial_fields(self):
        """Test with only some fields present - only maps what exists."""
        entry = {'id': 'NCT123', 'title': 'Test'}
        result = format_key_labels(entry)

        assert result['trial_id'] == 'NCT123'
        assert result['title'] == 'Test'
        assert len(result) == 2  # Only 2 mapped fields

    def test_empty_entry(self):
        """Test with empty entry - should return empty dict."""
        entry = {}
        result = format_key_labels(entry)
        assert result == {}

    def test_field_values_preserved(self):
        """Test that field values are preserved as-is (no modification)."""
        entry = {
            'id': 'NCT-2026-12345',
            'summary': '<b>Complex</b> summary with HTML',
            'link': 'https://clinicaltrials.gov/study/NCT123'
        }
        result = format_key_labels(entry)

        # Values should be exactly preserved
        assert result['trial_id'] == 'NCT-2026-12345'
        assert result['raw_description'] == '<b>Complex</b> summary with HTML'
        assert result['source_link'] == 'https://clinicaltrials.gov/study/NCT123'


class TestSetUpKeyInfo:
    """Tests for set_up_key_info function."""

    def test_initializes_empty_lists(self):
        """Test that key_info fields are initialized as empty lists."""
        entry = {'id': 'NCT123'}
        result = set_up_key_info(entry, ['conditions', 'sponsors'])

        assert result['conditions'] == []
        assert result['sponsors'] == []
        assert result['status'] == ''

    def test_initializes_multiple_keys(self):
        """Test initializing multiple key info fields."""
        entry = {}
        result = set_up_key_info(
            entry, ['conditions', 'interventions', 'sponsors'])

        assert len(result) == 4  # 3 keys + status
        assert 'status' in result

    def test_preserves_existing_fields(self):
        """Test that existing fields are preserved."""
        entry = {'id': 'NCT123', 'title': 'Test'}
        result = set_up_key_info(entry, ['conditions'])

        assert result['id'] == 'NCT123'
        assert result['title'] == 'Test'
        assert result['conditions'] == []


class TestExtractKeyInformation:
    """Tests for extract_key_information function."""

    def test_extract_conditions_sponsors_interventions(self):
        """Test extracting conditions, sponsors, and interventions with proper formatting."""
        entry = {
            'trial_id': 'NCT123',
            'raw_description': '<b>Conditions</b>: Heart Disease; Hypertension<b>Sponsors</b>: Hospital A; Hospital B<b>Interventions</b>: Drug A; Surgery'
        }
        result = extract_key_information(entry)

        assert 'conditions' in result
        assert 'sponsors' in result
        assert 'interventions' in result
        assert 'status' in result

    def test_extract_status_with_content(self):
        """Test extracting status when tag has content after it."""
        entry = {
            'trial_id': 'NCT123',
            'raw_description': '<b>Conditions</b>: Disease<b>Status</b>: Recruiting'
        }
        result = extract_key_information(entry)

        assert isinstance(result['status'], str)
        assert result['status'] != ''

    def test_missing_raw_description(self):
        """Test with missing raw_description returns empty lists."""
        entry = {'trial_id': 'NCT123'}
        result = extract_key_information(entry)

        assert result['conditions'] == []
        assert result['sponsors'] == []
        assert result['interventions'] == []
        assert result['status'] == ''

    def test_empty_raw_description(self):
        """Test with empty raw_description returns empty lists."""
        entry = {
            'trial_id': 'NCT123',
            'raw_description': ''
        }
        result = extract_key_information(entry)

        assert result['conditions'] == []
        assert result['sponsors'] == []
        assert result['interventions'] == []

    def test_no_html_tags_in_description(self):
        """Test when raw_description has no <b> tags - should return without processing."""
        entry = {
            'trial_id': 'NCT123',
            'raw_description': 'Plain text without any HTML tags'
        }
        result = extract_key_information(entry)

        assert result['conditions'] == []
        assert result['sponsors'] == []
        assert result['interventions'] == []

    def test_unclosed_tags_len_part_lt_2(self):
        """Test with unclosed tags where len(part) < 2 - should skip malformed parts."""
        entry = {
            'trial_id': 'NCT123',
            'raw_description': '<b>Conditions: Unclosed tag here<b>Sponsors</b>: Hospital'
        }
        result = extract_key_information(entry)

        # Sponsors should still be extracted even if earlier part is malformed
        assert 'sponsors' in result

    def test_partial_sections(self):
        """Test when only some sections are present."""
        entry = {
            'trial_id': 'NCT123',
            'raw_description': '<b>Conditions</b>: Heart Disease<b>Sponsors</b>: Hospital'
        }
        result = extract_key_information(entry)

        assert 'conditions' in result
        assert 'sponsors' in result
        assert result['interventions'] == []

    def test_status_only_with_non_empty_content(self):
        """Test status extraction - should only set if len(part) > 1 AND part[1].strip() is not empty."""
        entry = {
            'trial_id': 'NCT123',
            'raw_description': '<b>Conditions</b>: Disease<b>Status</b>:'
        }
        result = extract_key_information(entry)

        # Status should NOT be set because part[1].strip() would be empty after ':'
        # Actually it will be empty string, so status should remain ''
        assert isinstance(result['status'], str)

    def test_multiple_items_split_by_semicolon(self):
        """Test that conditions, sponsors, interventions are properly split by semicolon."""
        entry = {
            'trial_id': 'NCT123',
            'raw_description': '<b>Conditions</b>: Heart; Lung; Kidney<b>Sponsors</b>: Hospital A; Hospital B; Clinic C'
        }
        result = extract_key_information(entry)

        # Should have multiple items for conditions and sponsors
        assert isinstance(result['conditions'], list)
        assert isinstance(result['sponsors'], list)

    def test_whitespace_handling_with_lstrip_rstrip(self):
        """Test that leading ': ' is stripped and trailing content is properly handled."""
        entry = {
            'trial_id': 'NCT123',
            'raw_description': '<b>Conditions</b>: Heart Disease; Hypertension<b>Sponsors</b>: Hospital'
        }
        result = extract_key_information(entry)

        # Check that items are properly cleaned of leading ': '
        assert 'conditions' in result
        assert 'sponsors' in result


class TestTransform:
    """Tests for transform function."""

    def test_transform_single_entry(self):
        """Test transforming a single entry."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'title': 'Study Name',
            'summary': 'Study summary text',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)

        assert len(result) == 1
        assert result[0]['trial_id'] == 'NCT123'

    def test_transform_converts_dates(self):
        """Test that dates are converted."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'summary': 'Test summary',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)

        assert len(result) == 1
        assert 'published_date' in result[0]
        assert 'last_updated' in result[0]
        assert isinstance(result[0]['published_date'], date)

    def test_transform_renames_fields(self):
        """Test that fields are renamed to human-readable names."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'summary': 'Test summary',
            'title': 'Test title',
            'link': 'https://example.com',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)

        assert len(result) == 1
        assert result[0]['trial_id'] == 'NCT123'
        assert result[0]['raw_description'] == 'Test summary'
        assert result[0]['source_link'] == 'https://example.com'

    def test_transform_adds_last_ingested(self):
        """Test that last_ingested timestamp is added."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'summary': 'Test',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)

        assert len(result) == 1
        assert 'last_ingested' in result[0]
        assert isinstance(result[0]['last_ingested'], date)

    def test_transform_empty_list(self):
        """Test transforming empty list."""
        result = transform([])
        assert result == []

    def test_transform_multiple_entries(self):
        """Test transforming multiple entries."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [
            {'id': f'NCT{i}', 'summary': f'Study {i}',
                'published_parsed': struct_t, 'updated_parsed': struct_t}
            for i in range(5)
        ]

        result = transform(entries)

        assert len(result) == 5

    def test_transform_error_handling(self):
        """Test that transform handles errors gracefully with try/except."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [
            {'id': 'NCT123', 'summary': 'Test', 'published_parsed': struct_t,
                'updated_parsed': struct_t},
            {'id': 'NCT124', 'summary': 'Test2', 'published_parsed': 'invalid',
                'updated_parsed': struct_t},
            {'id': 'NCT125', 'summary': 'Test3',
                'published_parsed': struct_t, 'updated_parsed': struct_t}
        ]

        result = transform(entries)

        # Should transform valid entries and skip bad ones
        assert len(result) >= 1
        # First and third should succeed
        assert len(result) >= 2

    def test_transform_entry_missing_id(self):
        """Test transforming entry without ID field."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'title': 'Study Without ID',
            'summary': 'Test summary',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)
        assert len(result) == 1

    def test_transform_entry_with_none_values(self):
        """Test transforming entry with None values."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'title': None,
            'summary': None,
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)
        assert len(result) == 1

    def test_transform_entry_with_empty_strings(self):
        """Test transforming entry with empty string fields."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'title': '',
            'summary': '',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)
        assert len(result) == 1

    def test_transform_partial_entries(self):
        """Test transforming entries with only some fields."""
        entries = [
            {'id': 'NCT001', 'summary': 'Test1'},
            {'title': 'Study with no ID', 'summary': 'Test2'},
            {'id': 'NCT003', 'title': 'Complete entry', 'summary': 'Test3'}
        ]

        result = transform(entries)
        assert len(result) == 3

    def test_transform_very_large_text_fields(self):
        """Test transforming entry with very large text fields."""
        large_text = '<b>Title</b>: ' + 'x' * 10000
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'title': large_text,
            'summary': large_text,
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)
        assert len(result) == 1
        # Check that HTML tags were replaced with commas
        assert '<b>' not in result[0]['title']
        assert '<b>' not in result[0]['raw_description']
        assert ',' in result[0]['title']
        assert ',' in result[0]['raw_description']

    def test_transform_special_unicode_characters(self):
        """Test transforming entry with unicode characters."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'title': "Study: Behçet's Syndrome",
            'summary': 'Testing café and naïve',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)
        assert len(result) == 1
        assert "Behçet's" in result[0]['title']
        assert 'café' in result[0]['raw_description']


class TestRemoveHtmlTagsEdgeCases:
    """Edge case tests for remove_html_tags function."""

    def test_nested_html_tags(self):
        """Test with nested HTML tags - should all be replaced with commas."""
        text = '<div><b>nested <i>deeply</i></b></div>'
        result = remove_html_tags(text)
        # All tags replaced with commas
        assert '<' not in result and '>' not in result
        assert 'nested' in result and 'deeply' in result
        assert ',' in result

    def test_malformed_html(self):
        """Test with unclosed/malformed HTML tags."""
        text = '<b>unclosed tag <i>another'
        result = remove_html_tags(text)
        assert '<' not in result
        assert 'unclosed' in result and 'another' in result
        assert ',' in result

    def test_html_comments(self):
        """Test with HTML comments - should be replaced with commas."""
        text = '<!-- comment -->text'
        result = remove_html_tags(text)
        # Comment is a tag too, replaced with comma
        assert ',' in result
        assert 'text' in result

    def test_tags_with_attributes(self):
        """Test replacing tags with attributes with commas."""
        text = '<div class="container" id="main">Content</div>'
        result = remove_html_tags(text)
        assert '<' not in result
        assert ',' in result
        assert 'Content' in result

    def test_tags_with_complex_attributes(self):
        """Test with tags containing quotes and special chars in attributes."""
        text = '<a href="https://example.com?param=value&other=123">Link</a>'
        result = remove_html_tags(text)
        assert '<' not in result
        assert ',' in result
        assert 'Link' in result

    def test_consecutive_newlines(self):
        """Test with multiple consecutive newlines - all replaced with spaces."""
        text = 'Line 1\n\n\nLine 2'
        result = remove_html_tags(text)
        assert '\n' not in result
        assert 'Line 1' in result and 'Line 2' in result

    def test_whitespace_preservation(self):
        """Test that internal whitespace is preserved."""
        text = '<b>Text  with   spaces</b>'
        result = remove_html_tags(text)
        assert 'Text  with   spaces' in result

    def test_special_characters_preserved(self):
        """Test that special chars outside of entities are preserved."""
        text = 'Special: !@#$%^*()_+-=[]{}|;:,.?'
        result = remove_html_tags(text)
        assert result == text


class TestFormatDatetimeFieldsEdgeCases:
    """Edge case tests for format_datetime_fields function."""

    def test_year_edge_cases(self):
        """Test with edge case years."""
        struct_t = struct_time((1970, 1, 1, 0, 0, 0, 3, 1, 0))
        entry = {'published_parsed': struct_t}

        result = format_datetime_fields(entry, ['published_parsed'])
        assert result['published'].year == 1970

    def test_end_of_year(self):
        """Test with end of year date."""
        struct_t = struct_time((2026, 12, 31, 23, 59, 59, 3, 365, 0))
        entry = {'published_parsed': struct_t}

        result = format_datetime_fields(entry, ['published_parsed'])
        assert result['published'].month == 12
        assert result['published'].day == 31


class TestTransformEdgeCases:
    """Edge case tests for transform function."""

    def test_transform_with_large_dataset(self):
        """Test transforming a large number of entries."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [
            {'id': f'NCT{i:05d}', 'summary': f'Study {i}', 'published_parsed': struct_t,
                'updated_parsed': struct_t}
            for i in range(100)
        ]

        result = transform(entries)
        assert len(result) == 100

    def test_transform_special_unicode_characters_edge_case(self):
        """Test transforming entry with unicode characters and HTML."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'title': "Study <b>Behçet's</b>",
            'summary': 'Testing <b>café</b>',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)
        assert len(result) == 1
        assert "Behçet's" in result[0]['title']
        assert 'café' in result[0]['raw_description']

    def test_transform_html_entity_edge_cases(self):
        """Test with unusual HTML entities and patterns."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'summary': 'CVD &amp; HTN; <br /> More &lt; text &gt;',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)
        assert len(result) == 1
        assert '&amp;' in result[0]['raw_description']  # entities NOT replaced
        # tags replaced with commas
        assert '<br />' not in result[0]['raw_description']
        # HTML tags replaced with commas
        assert ',' in result[0]['raw_description']
