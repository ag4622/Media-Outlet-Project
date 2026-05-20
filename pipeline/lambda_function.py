"""Lambda handler that processes clinical trial data, 
cleans it, generates embeddings, and stores results in DynamoDB."""

import logging
from extract import extract
from transform_clean import transform
from vector_embedding import embedding_pipeline
from loading import load

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context) -> dict:
    """Main Lambda function to orchestrate the ETL pipeline."""
    logger.info("Request ID: %s", context.aws_request_id)
    logger.info("Remaining time: %d ms",
                context.get_remaining_time_in_millis())

    try:
        logger.info("Starting ETL pipeline")
        logger.info("Event: %s", event)

        # Step 1: Extract data
        logger.info("Extracting data...")
        raw_data = extract()
        logger.info("Extracted %d records", len(raw_data))

        # Step 2: Transform and clean data
        logger.info("Transforming and cleaning data...")
        cleaned_data = transform(raw_data)
        logger.info("Cleaned %d records", len(cleaned_data))

        # Step 3: Generate embeddings and append to data
        logger.info("Generating embeddings...")
        data_with_embeddings = embedding_pipeline(cleaned_data)
        logger.info("Generated embeddings for %d records",
                    len(data_with_embeddings))

        # Step 4: Load data into DynamoDB
        logger.info("Loading data to DynamoDB...")
        load(data_with_embeddings)
        logger.info("Successfully loaded data to DynamoDB")

        return {
            'statusCode': 200,
            'body': 'Data processed and loaded successfully.'
        }

    except Exception as e:
        logger.error("Error processing data: %s", str(e), exc_info=True)
        return {
            'statusCode': 500,
            'body': f'Error processing data: {str(e)}'
        }
