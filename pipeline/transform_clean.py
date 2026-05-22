"""Transform stage of ETL pipeline for transforming clinical trials RSS feed data.

Provides functions for formatting, cleaning, and extracting structured
information from raw RSS feed entries.
"""
import logging
import re
from datetime import datetime
from time import mktime
from extract import extract, setup_logging


def format_datetime_fields(entry: dict, datetime_fields: list) -> dict:
    """Format time.struct_time fields to date format (without time)."""
    for field in datetime_fields:
        try:
            field_name = field[:field.index('_')]
            entry[field_name] = datetime.fromtimestamp(
                mktime(entry[field])).date().strftime('%Y-%m-%d')
        except (KeyError, ValueError, OSError, OverflowError, TypeError):
            logging.warning(
                "Could not convert field '%s' to date for entry ID: %s",
                field, entry.get('trial_id', 'N/A'))
    return entry


def format_key_labels(entry: dict) -> dict:
    """Format key labels to be more human-readable."""
    key_mapping = {
        'id': 'trial_id',
        'summary': 'raw_description',
        'title': 'title',
        'published': 'published_date',
        'link': 'source_link'
    }
    formatted_entry = {}
    for key, value in entry.items():
        new_key = key_mapping.get(key)
        if new_key:
            formatted_entry[new_key] = value
    return formatted_entry


def set_up_key_info(entry: dict, key_info: list) -> dict:
    """Set up key information in entry for easier access."""
    for key in key_info:
        entry[key] = []
    entry['status'] = ''
    return entry


def extract_key_information(entry: dict) -> dict:
    """Extract key information from the summary in entry."""
    summary = entry.get('raw_description', '')
    # Handle None values gracefully
    if summary is None:
        summary = ''
    key_info = ['conditions', 'interventions', 'sponsors']
    entry = set_up_key_info(entry, key_info)

    # If no HTML tags present, return with empty lists
    if '<b>' not in summary or '</b>' not in summary:
        return entry

    summary = summary.lstrip('<b>')
    split_summary = summary.split('<b>')
    split_summary = [part.split('</b>') for part in split_summary]

    for index, part in enumerate(split_summary):
        if len(part) < 2:
            continue
        split_summary[index][1] = part[1].lstrip(
            ': ').rstrip('\n<br />').split('; ')
        if part[0].lower() in key_info:
            entry[part[0].lower()] = split_summary[index][1]
        else:
            # For status, check if part[0] (the label) has content
            if part[0].strip():
                entry['status'] = part[0]
    return entry


def remove_html_tags(text: str) -> str:
    """Remove HTML tags from text using regex pattern."""
    if not isinstance(text, str):
        return text
    # Replace all HTML tags with commas
    clean_text = re.sub(r'<[^>]*>', ',', text)
    # Replace newlines with spaces
    clean_text = clean_text.replace('\n', ' ')
    return clean_text


def format_feed_entries(entry: dict) -> dict:
    """Format the entry data to remove HTML tags from feed entries."""
    if 'raw_description' in entry and entry['raw_description'] is not None:
        entry['raw_description'] = remove_html_tags(entry['raw_description'])
    if 'title' in entry and entry['title'] is not None:
        entry['title'] = remove_html_tags(entry['title'])
    return entry


def transform(entries: list) -> list[dict]:
    """Transform and clean feed entries through formatting pipeline."""
    if not entries:
        logging.warning("No entries provided for transformation.")
        return []
    logging.info("Starting transformation of %d entries", len(entries))
    result = []
    last_ingested = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for entry in entries:
        try:
            entry = format_datetime_fields(
                entry, ['updated_parsed', 'published_parsed'])
            entry = format_key_labels(entry)
            entry = extract_key_information(entry)
            entry = format_feed_entries(entry)
            entry['last_ingested'] = last_ingested
            result.append(entry)
        except (KeyError, ValueError, AttributeError, TypeError) as e:
            trial_id = entry.get('id', 'N/A')
            logging.warning("Failed to transform entry %s: %s", trial_id, e)
    logging.info("Successfully transformed %d entries", len(result))
    return result


if __name__ == "__main__":
    setup_logging()
    feed_entries = extract()
    transformed_result = transform(feed_entries)
