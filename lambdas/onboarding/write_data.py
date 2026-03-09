"""
Module for writing league data to SQLite DB.
"""

import boto3
import botocore.exceptions
import duckdb
import pandas as pd

from utils.logging_config import logger

LOCAL_DB_PATH = "/tmp/client_assets.duckdb"
# # Uncomment for local testing
# LOCAL_DB_PATH = "database.duckdb"


def write_to_duckdb_table(data_to_write: list[tuple[str, pd.DataFrame]]) -> None:
    """
    Writes a list of view name and pandas dataframe mappings to a DuckDB database file.

    Args:
        data_to_write: A tuple mapping of view name and the corresponding pandas dataframe.
            The view name will be the name of the table in the DuckDB database.
    """
    con = duckdb.connect(LOCAL_DB_PATH)
    try:
        for view_name, dataframe in data_to_write:
            try:
                con.execute(
                    f"CREATE OR REPLACE TABLE {view_name} AS SELECT * FROM dataframe"
                )
                logger.info("Successfully created %s table", view_name)
            except Exception as e:
                logger.error("Failed to write %s table to database: %s", view_name, e)
                raise e
    finally:
        con.close()


def write_duckdb_file_to_s3(bucket_name: str, bucket_key: str):
    """
    Writes a DuckDB .duckdb file from Lambda's /tmp directory to S3.

    Args:
        bucket_name: The name of the S3 bucket to write to.
        bucket_key: The key of the file within the S3 bucket.
    """
    s3_client = boto3.client("s3")
    try:
        s3_client.upload_file(
            Filename=LOCAL_DB_PATH,
            Bucket=bucket_name,
            Key=bucket_key,
        )
    except botocore.exceptions.ClientError as e:
        logger.error("Failed to write .duckdb file to S3: %s", e)
        raise e
