import logging
import re
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


def format_feed_entries(entries: list) -> list:
    """Format the entry data to remove HTML tags like <b>, </b>, <br /> from feed entries."""
    formatted_entries = []
    for entry in entries:
        # Remove HTML tags from summary fields
        if 'summary' in entry:
            entry['summary'] = remove_html_tags(entry['summary'])
        # Remove HTML tags from title fields if needed
        if 'title' in entry:
            entry['title'] = remove_html_tags(entry['title'])
        entry.pop('title_detail', None)
        entry.pop('summary_detail', None)
        entry.pop('links', None)
        formatted_entries.append(entry)
    return formatted_entries


def transform(entries: list) -> list[dict]:
    """Transforms and cleans feed entries by removing HTML tags."""
    if not entries:
        logging.warning("No entries provided for transformation.")
        return []
    cleaned_entries = format_feed_entries(entries)
    return cleaned_entries


if __name__ == "__main__":
    setup_logging()
    entries = extract()
    if entries:
        cleaned_entries = transform(entries)
        print(f"Transformed {len(cleaned_entries)} entries")
        if cleaned_entries:
            print(
                f"First cleaned entry summary: {cleaned_entries[0]}")
