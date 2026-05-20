"""Python module for loading data into the DynamoDB table."""

import logging
import os
import boto3
from botocore.exceptions import ClientError

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

    logging.info("Loading %s items into DynamoDB table %s",
                 len(data), TABLE_NAME)

    db = boto3.resource(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'eu-west-2')
    ).Table(TABLE_NAME)
    for item in data:
        logging.debug("Loading item: %s", item)
        try:
            db.put_item(Item=item)
            logging.info(
                "Inserted trial_id=%s updated_at=%s",
                item["trial_id"],
                item["updated_at"],
            )
        except ClientError as e:

            logging.error("DynamoDB ClientError: %s", e)
    logging.info("Data loading completed.")
