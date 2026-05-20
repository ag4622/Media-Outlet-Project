"""Extract module for fetching and parsing clinical trials RSS feed data.

Provides functions to fetch raw RSS feed data from clinicaltrials.gov API
and extract entry information.
"""
import logging
import feedparser


def setup_logging(logging_level=logging.INFO):
    """Sets up logging configuration."""
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def fetch_clinical_trials_rss(
        url: str = "https://clinicaltrials.gov/api/rss?dateField=LastUpdatePostDate"
) -> feedparser.FeedParserDict:
    """Fetch the clinical trials RSS feed from the specified URL."""
    logging.info("Fetching clinical trials RSS feed from %s", url)
    try:
        feed = feedparser.parse(url)
        logging.info("Successfully fetched clinical trials RSS feed")
        return feed
    except (OSError, ValueError) as e:
        logging.error("Error fetching clinical trials RSS feed: %s", e)
        return None


def extract(
        url: str = "https://clinicaltrials.gov/api/rss?dateField=LastUpdatePostDate"
) -> list[dict]:
    """Extract the clinical trials RSS feed data entries."""
    feed = fetch_clinical_trials_rss(url)
    if feed is None:
        logging.error("Failed to fetch clinical trials RSS feed.")
        return []
    logging.info("The keys in the feed are: %s", list(feed.keys()))
    feed_entries = feed.get('entries')
    if feed_entries:
        logging.info("Extracted %d entries", len(feed_entries))
    else:
        logging.warning("No entries extracted from the feed.")
    return feed_entries


if __name__ == "__main__":
    setup_logging()
    result_entries = extract()
