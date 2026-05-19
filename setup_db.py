"""This script sets up the DynamoDB table for storing trial data.
It creates a table named "TrialsTable" with a primary key "trial_id". If the table already exists,
it logs that information instead of throwing an error."""

import logging
import boto3

logger = logging.getLogger(__name__)
logging.basicConfig(filename="setup_db.log",
                    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

dynamodb = boto3.client("dynamodb")

TABLE_NAME = "TrialsTable"

try:
    response = dynamodb.create_table(
        TableName=TABLE_NAME,

        KeySchema=[
            {
                "AttributeName": "trial_id",
                "KeyType": "HASH"
            }
        ],

        AttributeDefinitions=[
            {
                "AttributeName": "trial_id",
                "AttributeType": "S"
            }
        ],

        BillingMode="PAY_PER_REQUEST"
    )

    logger.info("Creating table: %s", TABLE_NAME)

except dynamodb.exceptions.ResourceInUseException:
    logger.info("Table already exists: %s", TABLE_NAME)
