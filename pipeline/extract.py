import logging
import feedparser
import re


def setup_logging(logging_level=logging.INFO):
    """Sets up logging configuration."""
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def fetch_clinical_trials_rss(url: str = "https://clinicaltrials.gov/api/rss?dateField=LastUpdatePostDate"):
    """Fetches the clinical trials RSS feed from the specified URL."""
    logging.info(f"Fetching clinical trials RSS feed from {url}")
    try:
        feed = feedparser.parse(url)
        logging.info("Successfully fetched clinical trials RSS feed")
        return feed
    except Exception as e:
        logging.error(f"Error fetching clinical trials RSS feed: {e}")
        return None

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
        if 'summary_detail' in entry and isinstance(entry['summary_detail'], dict):
            if 'value' in entry['summary_detail']:
                entry['summary_detail']['value'] = remove_html_tags(
                    entry['summary_detail']['value']
                )
        # Remove HTML tags from title fields if needed
        if 'title' in entry:
            entry['title'] = remove_html_tags(entry['title'])
        formatted_entries.append(entry)
    return formatted_entries


if __name__ == "__main__":
    setup_logging()
    feed = fetch_clinical_trials_rss()
    print(feed['entries'])  # Print the first entry to verify
    # Format entries to remove HTML tags
    cleaned_entries = format_feed_entries(feed['entries'])
    # Print the first cleaned entry to verify
    print("Cleaned first entry:")
    #print(cleaned_entries[0])
