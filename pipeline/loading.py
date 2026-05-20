"""Python module for loading data into the DynamoDB table."""

import logging
import boto3

TABLE_NAME = "c23-ClinicalTrialTracker"


def setup_logging(logging_level=logging.INFO) -> None:
    """Sets up logging configuration."""
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def load(data: list[dict]) -> None:
    """
    Load transformed clinical trial data into DynamoDB.

    Expected DynamoDB schema:
        PK = trial_id
        SK = updated_at
    """

    logging.info("Loading %s items into DynamoDB table %s", len(data), TABLE_NAME)

    db = boto3.resource('dynamodb').Table(TABLE_NAME)
    for item in data:
        logging.debug("Loading item: %s", item)
        try:
            db.put_item(Item=item,
                        ConditionExpression="attribute_not_exists(updated_at)")
            logging.info(
                "Inserted trial_id=%s updated_at=%s",
                item["trial_id"],
                item["updated_at"],
            )
        except Exception as e:
            logging.error("Error loading item: %s. Error: %s", item, e)
    logging.info("Data loading completed.")
