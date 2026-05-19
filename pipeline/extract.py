import logging
import feedparser


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


if __name__ == "__main__":
    setup_logging()
    print(fetch_clinical_trials_rss()['entries'][0])
