"""Lambda handler that processes clinical trial data,
cleans it, generates embeddings, and stores results in DynamoDB."""

import logging
import traceback
from botocore.exceptions import ClientError
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
        try:
            logger.info("Extracting data from extract.py...")
            raw_data = extract()
            logger.info(
                "Successfully extracted %d records from extract.py", len(raw_data))
        except (IOError, ValueError, RuntimeError) as e:
            logger.error("ERROR in extract.py: %s", str(e), exc_info=True)
            return {
                'statusCode': 500,
                'body': f'Error in extract.py: {str(e)}',
                'errorFile': 'extract.py',
                'traceback': traceback.format_exc()
            }

        # Step 2: Transform and clean data
        try:
            logger.info(
                "Transforming and cleaning data with transform_clean.py...")
            cleaned_data = transform(raw_data)
            logger.info(
                "Successfully cleaned %d records from transform_clean.py", len(cleaned_data))
        except (ValueError, KeyError, TypeError) as e:
            logger.error("ERROR in transform_clean.py: %s",
                         str(e), exc_info=True)
            return {
                'statusCode': 500,
                'body': f'Error in transform_clean.py: {str(e)}',
                'errorFile': 'transform_clean.py',
                'traceback': traceback.format_exc()
            }

        # Step 3: Generate embeddings and append to data
        try:
            logger.info("Generating embeddings with vector_embedding.py...")
            data_with_embeddings = embedding_pipeline(cleaned_data)
            logger.info("Successfully generated embeddings for %d records from vector_embedding.py",
                        len(data_with_embeddings))
        except (ValueError, RuntimeError, IOError) as e:
            logger.error("ERROR in vector_embedding.py: %s",
                         str(e), exc_info=True)
            return {
                'statusCode': 500,
                'body': f'Error in vector_embedding.py: {str(e)}',
                'errorFile': 'vector_embedding.py',
                'traceback': traceback.format_exc()
            }

        # Step 4: Load data into DynamoDB
        try:
            logger.info("Loading data to DynamoDB with load.py...")
            load(data_with_embeddings)
            logger.info("Successfully loaded data to DynamoDB from load.py")
        except (ClientError, ValueError, KeyError) as e:
            logger.error("ERROR in load.py: %s", str(e), exc_info=True)
            return {
                'statusCode': 500,
                'body': f'Error in load.py: {str(e)}',
                'errorFile': 'load.py',
                'traceback': traceback.format_exc()
            }

        return {
            'statusCode': 200,
            'body': 'Data processed and loaded successfully.'
        }

    except (ValueError, KeyError, IOError, RuntimeError, ClientError) as e:
        logger.error("Unexpected error in lambda_function.py: %s",
                     str(e), exc_info=True)
        return {
            'statusCode': 500,
            'body': f'Unexpected error in lambda_function.py: {str(e)}',
            'errorFile': 'lambda_function.py',
            'traceback': traceback.format_exc()
        }
