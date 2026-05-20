import logging
import re
from datetime import datetime
from time import mktime
from extract import extract, setup_logging


def remove_html_tags(text: str) -> str:
    """Remove HTML tags from text using regex pattern."""
    if not isinstance(text, str):
        return text
    # Remove all HTML tags
    clean_text = re.sub(r'<[^>]*>', '', text)
    # Replace common HTML entities
    clean_text = clean_text.replace('&nbsp;', ' ')
    clean_text = clean_text.replace('&amp;', '&')
    clean_text = clean_text.replace('&lt;', '<')
    clean_text = clean_text.replace('&gt;', '>')
    clean_text = clean_text.replace('&quot;', '"')
    # Replace newlines with spaces
    clean_text = clean_text.replace('\n', ' ')
    return clean_text


def format_feed_entries(entry: dict) -> dict:
    """Format the entry data to remove HTML tags like <b>, </b>, <br /> from feed entries."""
    # Remove HTML tags from summary fields
    if 'summary' in entry:
        entry['summary'] = remove_html_tags(entry['summary'])
    # Remove HTML tags from title fields if needed
    if 'title' in entry:
        entry['title'] = remove_html_tags(entry['title'])
    return entry


def format_datetime_fields(entry: dict, datetime_fields: list) -> dict:
    """Format time.struct_time fields to date format (without time)."""
    for field in datetime_fields:
        try:
            field_name = field[:field.index('_')]
            entry[field_name] = datetime.fromtimestamp(
                mktime(entry[field])).date()
        except:
            logging.warning(
                f"Could not convert field '{field}' to date for entry ID: {entry.get('id', 'N/A')}")
    return entry


def format_key_labels(entry: dict) -> dict:
    """Format key labels to be more human-readable."""
    key_mapping = {
        'id': 'trial_id',
        'summary': 'raw_description',
        'title': 'title',
        'updated': 'last_updated',
        'published': 'published_date',
        'link': 'source_link'
    }
    formatted_entry = {}
    for key, value in entry.items():
        new_key = key_mapping.get(key)
        if new_key:
            formatted_entry[new_key] = value
    return formatted_entry


def transform(entries: list) -> list[dict]:
    """Transforms and cleans feed entries by removing HTML tags."""
    if not entries:
        logging.warning("No entries provided for transformation.")
        return []
    cleaned_entries = []
    last_ingested = datetime.now().date()
    for entry in entries:
        entry = format_feed_entries(entry)
        entry = format_datetime_fields(
            entry, ['updated_parsed', 'published_parsed'])
        entry = format_key_labels(entry)
        entry = extract_key_information(entry)
        entry['last_ingested'] = last_ingested
        cleaned_entries.append(entry)
    return cleaned_entries


if __name__ == "__main__":
    setup_logging()
    entries = extract()
    if entries:
        cleaned_entries = transform(entries)
        print(f"Transformed {len(cleaned_entries)} entries")
        if cleaned_entries:
            print(
                f"First cleaned entry: {cleaned_entries[0]}")
            print(f"First cleaned entry keys: {cleaned_entries[0].keys()}")
