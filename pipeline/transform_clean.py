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
                mktime(entry[field])).date()
        except:
            logging.warning(
                f"Could not convert field '{field}' to date for entry ID: {entry.get('trial_id', 'N/A')}")
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


def set_up_key_info(entry: dict, key_info: list) -> dict:
    """Set up key information in entry for easier access."""
    for key in key_info:
        entry[key] = []
    entry['status'] = ''
    return entry


def extract_key_information(entry: dict) -> dict:
    """Extract key information from the summary in entry."""
    summary = entry.get('raw_description', '')
    key_info = ['conditions', 'interventions', 'sponsors']
    entry = set_up_key_info(entry, key_info)
    summary = summary.lstrip('<b>')
    split_summary = summary.split('<b>')
    split_summary = [part.split('</b>') for part in split_summary]
    for index, part in enumerate(split_summary):
        split_summary[index][1] = part[1].lstrip(
            ': ').rstrip('\n<br />').split('; ')
        if part[0].lower() in key_info:
            entry[part[0].lower()] = split_summary[index][1]
        else:
            if len(part) > 1:
                entry['status'] = part[0]
    return entry


def remove_html_tags(text: str) -> str:
    """Remove HTML tags from text using regex pattern."""
    if not isinstance(text, str):
        return text
    # Remove all HTML tags
    clean_text = re.sub(r'<[^>]*>', ',', text)
    # Replace newlines with spaces
    clean_text = clean_text.replace('\n', ' ')
    return clean_text


def format_feed_entries(entry: dict) -> dict:
    """Format the entry data to remove HTML tags like <b>, </b>, <br /> from feed entries."""
    # Remove HTML tags from summary fields
    if 'raw_description' in entry:
        entry['raw_description'] = remove_html_tags(entry['raw_description'])
    # Remove HTML tags from title fields if needed
    if 'title' in entry:
        entry['title'] = remove_html_tags(entry['title'])
    return entry


def transform(entries: list) -> list[dict]:
    """Transforms and cleans feed entries by removing HTML tags."""
    if not entries:
        logging.warning("No entries provided for transformation.")
        return []
    cleaned_entries = []
    last_ingested = datetime.now().date()
    for entry in entries:
        entry = format_datetime_fields(
            entry, ['updated_parsed', 'published_parsed'])
        entry = format_key_labels(entry)
        entry = extract_key_information(entry)
        entry = format_feed_entries(entry)
        entry['last_ingested'] = last_ingested
        cleaned_entries.append(entry)
    logging.info(f"Transformed {len(cleaned_entries)} entries")
    return cleaned_entries


if __name__ == "__main__":
    setup_logging()
    entries = extract()

    cleaned_entries = transform(entries)
    print(cleaned_entries[0])

    # print(extract_key_information(format_key_labels(entries[1])))
