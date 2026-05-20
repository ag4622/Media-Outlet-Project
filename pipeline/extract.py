import logging
import feedparser


def setup_logging(logging_level=logging.INFO):
    """Sets up logging configuration."""
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def fetch_clinical_trials_rss(url: str = "https://clinicaltrials.gov/api/rss?dateField=LastUpdatePostDate") -> feedparser.FeedParserDict:
    """Fetches the clinical trials RSS feed from the specified URL."""
    logging.info(f"Fetching clinical trials RSS feed from {url}")
    try:
        feed = feedparser.parse(url)
        logging.info("Successfully fetched clinical trials RSS feed")
        return feed
    except Exception as e:
        logging.error(f"Error fetching clinical trials RSS feed: {e}")
        return None


def extract(url: str = "https://clinicaltrials.gov/api/rss?dateField=LastUpdatePostDate") -> list[dict]:
    """Extracts the clinical trials RSS feed data."""
    feed = fetch_clinical_trials_rss(url)
    if feed is None:
        logging.error("Failed to fetch clinical trials RSS feed.")
        return []
    logging.info(f"The keys in the feed are: {list(feed.keys())}")
    entries = feed.get('entries')
    if entries:
        logging.info(f"Extracted {len(entries)} entries")
    else:
        logging.warning("No entries extracted from the feed.")
    return entries


if __name__ == "__main__":
    setup_logging()
    entries = extract()
