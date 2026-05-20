"""Python module for loading data into the DynamoDB table."""

import logging
import boto3

TABLE_NAME = "c23-clinical-trials"


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

    logging.info(f"Loading {len(data)} items into DynamoDB table {TABLE_NAME}")

    db = boto3.resource('dynamodb').Table(TABLE_NAME)
    for item in data:
        logging.debug(f"Loading item: {item}")
        try:
            db.put_item(Item=item,
                        ConditionExpression="attribute_not_exists(updated_at)")
            logging.info(
                "Inserted trial_id=%s updated_at=%s",
                item["trial_id"],
                item["updated_at"],
            )
        except Exception as e:
            logging.error(f"Error loading item: {item}. Error: {e}")
    logging.info("Data loading completed.")
