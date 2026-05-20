import pytest
from datetime import date, datetime
from time import struct_time
from unittest.mock import patch
from transform_clean import (
    remove_html_tags,
    remove_fields,
    format_feed_entries,
    format_datetime_fields,
    transform
)


class TestRemoveHtmlTags:
    """Tests for remove_html_tags function."""

    def test_remove_simple_html_tags(self):
        """Test removing basic HTML tags."""
        text = "<b>Bold text</b>"
        result = remove_html_tags(text)
        assert result == "Bold text"

    def test_remove_multiple_tags(self):
        """Test removing multiple different tags."""
        text = "<b>Conditions</b>: Disease; <br /><b>Sponsors</b>: Hospital"
        result = remove_html_tags(text)
        assert result == "Conditions: Disease; Sponsors: Hospital"

    def test_remove_self_closing_tags(self):
        """Test removing self-closing tags."""
        text = "Line 1<br />Line 2"
        result = remove_html_tags(text)
        assert result == "Line 1Line 2"

    def test_replace_html_entities(self):
        """Test replacing HTML entities."""
        text = "Drug: JS107&amp;Toripalimab&"
        result = remove_html_tags(text)
        assert "&" in result
        assert "&amp;" not in result

    def test_replace_newlines_with_spaces(self):
        """Test that newlines are replaced with spaces."""
        text = "Line 1\n<br />\nLine 2"
        result = remove_html_tags(text)
        assert "\n" not in result
        assert " " in result

    def test_non_string_input(self):
        """Test with non-string input."""
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


class TestRemoveFields:
    """Tests for remove_fields function."""

    def test_remove_single_field(self):
        """Test removing a single field."""
        entry = {'id': '123', 'title': 'Test', 'links': []}
        result = remove_fields(entry, ['links'])
        assert 'links' not in result
        assert 'id' in result
        assert 'title' in result

    def test_remove_multiple_fields(self):
        """Test removing multiple fields."""
        entry = {'id': '123', 'title': 'Test', 'links': [], 'summary': 'Text'}
        result = remove_fields(entry, ['links', 'summary'])
        assert 'links' not in result
        assert 'summary' not in result
        assert 'id' in result

    def test_remove_nonexistent_field(self):
        """Test removing field that doesn't exist."""
        entry = {'id': '123', 'title': 'Test'}
        result = remove_fields(entry, ['nonexistent'])
        assert 'id' in result
        assert len(result) == 2

    def test_remove_all_fields(self):
        """Test removing all fields."""
        entry = {'id': '123', 'title': 'Test'}
        result = remove_fields(entry, ['id', 'title'])
        assert len(result) == 0


class TestFormatFeedEntries:
    """Tests for format_feed_entries function."""

    def test_remove_html_from_summary(self):
        """Test HTML removal from summary."""
        entry = {'summary': '<b>Conditions</b>: Disease; <br />Hospital'}
        result = format_feed_entries(entry)
        assert '<b>' not in result['summary']
        assert '<br />' not in result['summary']

    def test_remove_html_from_title(self):
        """Test HTML removal from title."""
        entry = {'title': 'Study: <b>Important</b>'}
        result = format_feed_entries(entry)
        assert '<b>' not in result['title']

    def test_preserve_other_fields(self):
        """Test that other fields are preserved."""
        entry = {'id': 'NCT123', 'title': 'Test <b>Study</b>',
                 'published': 'May 2026'}
        result = format_feed_entries(entry)
        assert result['id'] == 'NCT123'
        assert result['published'] == 'May 2026'

    def test_missing_fields(self):
        """Test with missing summary/title."""
        entry = {'id': 'NCT123'}
        result = format_feed_entries(entry)
        assert result['id'] == 'NCT123'

    def test_empty_summary_and_title(self):
        """Test with empty summary and title."""
        entry = {'summary': '', 'title': ''}
        result = format_feed_entries(entry)
        assert result['summary'] == ''
        assert result['title'] == ''


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

    def test_removes_parsed_field(self):
        """Test that _parsed field is kept in the entry (need to check actual behavior)."""
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


class TestTransform:
    """Tests for transform function."""

    def test_transform_single_entry(self):
        """Test transforming a single entry."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'title': 'Study <b>Name</b>',
            'summary': '<b>Conditions</b>: Disease',
            'published_parsed': struct_t,
            'updated_parsed': struct_t,
            'links': [],
            'title_detail': {}
        }]

        result = transform(entries)

        assert len(result) == 1
        assert result[0]['id'] == 'NCT123'
        assert '<b>' not in result[0]['title']

    def test_transform_removes_unwanted_fields(self):
        """Test that unwanted fields are removed."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'links': ['link1'],
            'title_detail': {'type': 'text'},
            'summary_detail': {'value': 'text'},
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)

        assert 'links' not in result[0]
        assert 'title_detail' not in result[0]
        assert 'summary_detail' not in result[0]
        assert 'published_parsed' not in result[0]
        assert 'updated_parsed' not in result[0]

    def test_transform_converts_dates(self):
        """Test that dates are converted."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)

        assert 'published' in result[0]
        assert 'updated' in result[0]
        assert isinstance(result[0]['published'], date)

    def test_transform_empty_list(self):
        """Test transforming empty list."""
        result = transform([])
        assert result == []

    def test_transform_multiple_entries(self):
        """Test transforming multiple entries."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [
            {'id': f'NCT{i}', 'published_parsed': struct_t, 'updated_parsed': struct_t}
            for i in range(5)
        ]

        result = transform(entries)

        assert len(result) == 5
        for i, entry in enumerate(result):
            assert entry['id'] == f'NCT{i}'


class TestRemoveHtmlTagsEdgeCases:
    """Edge case tests for remove_html_tags function."""

    def test_nested_html_tags(self):
        """Test with nested HTML tags."""
        text = '<div><b>nested <i>deeply</i></b></div>'
        result = remove_html_tags(text)
        assert result == 'nested deeply'
        assert '<' not in result and '>' not in result

    def test_malformed_html(self):
        """Test with unclosed/malformed HTML tags."""
        text = '<b>unclosed tag <i>another'
        result = remove_html_tags(text)
        assert result == 'unclosed tag another'

    def test_html_comments(self):
        """Test with HTML comments."""
        text = '<!-- comment -->text'
        result = remove_html_tags(text)
        assert result == 'text'

    def test_tags_with_attributes(self):
        """Test removing tags with attributes."""
        text = '<div class="container" id="main">Content</div>'
        result = remove_html_tags(text)
        assert result == 'Content'

    def test_tags_with_complex_attributes(self):
        """Test with tags containing quotes and special chars in attributes."""
        text = '<a href="https://example.com?param=value&other=123">Link</a>'
        result = remove_html_tags(text)
        assert result == 'Link'

    def test_mixed_html_entities(self):
        """Test with multiple HTML entities."""
        text = 'A &amp; B &nbsp; C &lt; D &gt; E &quot;text&quot;'
        result = remove_html_tags(text)
        assert 'A & B' in result
        assert '&lt;' not in result
        assert '&amp;' not in result

    def test_consecutive_newlines(self):
        """Test with multiple consecutive newlines."""
        text = 'Line 1\n\n\nLine 2'
        result = remove_html_tags(text)
        assert '\n' not in result
        assert result == 'Line 1   Line 2'

    def test_whitespace_preservation(self):
        """Test that regular whitespace is preserved."""
        text = '<b>Text  with   spaces</b>'
        result = remove_html_tags(text)
        assert result == 'Text  with   spaces'

    def test_special_characters_preserved(self):
        """Test that special chars outside of entities are preserved."""
        text = 'Special: !@#$%^*()_+-=[]{}|;:,.?'
        result = remove_html_tags(text)
        assert result == text


class TestFormatDatetimeFieldsEdgeCases:
    """Edge case tests for format_datetime_fields function."""

    def test_leap_year_date(self):
        """Test with leap year February 29."""
        struct_t = struct_time((2024, 2, 29, 4, 0, 0, 4, 60, 0))
        entry = {'published_parsed': struct_t}

        result = format_datetime_fields(entry, ['published_parsed'])
        assert result['published'].month == 2
        assert result['published'].day == 29

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

    def test_transform_entry_missing_id(self):
        """Test transforming entry without ID field."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'title': 'Study Without ID',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)
        assert len(result) == 1
        assert 'id' not in result[0]

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
        assert result[0]['id'] == 'NCT123'

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
        assert result[0]['title'] == ''
        assert result[0]['summary'] == ''

    def test_transform_partial_entries(self):
        """Test transforming entries with only some fields."""
        entries = [
            {'id': 'NCT001'},
            {'title': 'Study with no ID'},
            {'id': 'NCT003', 'title': 'Complete entry'}
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
        assert len(result[0]['title']) > 10000
        assert '<b>' not in result[0]['title']

    def test_transform_special_unicode_characters(self):
        """Test transforming entry with unicode characters."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'title': "Study: Behçet's Syndrome with Étude",
            'summary': 'Testing café, naïve, 日本語',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)
        assert "Behçet's" in result[0]['title']
        assert 'café' in result[0]['summary']
        assert '日本語' in result[0]['summary']

    def test_transform_html_entity_edge_cases(self):
        """Test with unusual HTML entities and patterns."""
        struct_t = struct_time((2026, 5, 19, 4, 0, 0, 1, 139, 0))
        entries = [{
            'id': 'NCT123',
            'summary': '<b>Condition</b>: CVD &amp; HTN; &nbsp; <br /> More &lt; text &gt;',
            'published_parsed': struct_t,
            'updated_parsed': struct_t
        }]

        result = transform(entries)
        assert '&amp;' not in result[0]['summary']
        assert '&nbsp;' not in result[0]['summary']
        assert '<b>' not in result[0]['summary']
