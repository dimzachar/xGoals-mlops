import os
import json
import argparse

import mlflow

# import psycopg
from prefect import flow

# from prefect_aws import S3Bucket
from data_ingestion import read_data, download_from_url_to_path  # load_data_from_s3
from model_registry import register_model_in_mlflow
from model_training import hyperopt_train

# from model_monitoring import prep_db, calculate_metrics_postgresql
from data_preprocessing import (
    split_data,
    preprocess_data,
    filter_and_transform_shot_data,
)


@flow
def main_flow_s3(config_path):
    """
    Main Prefect flow for orchestrating the training pipeline.

    This flow:
    1. Sets up MLflow tracking.
    2. Loads data from an S3 bucket.
    3. Reads and preprocesses the data.
    4. Splits the data into training, validation, and test sets.
    5. Trains a model using hyperparameter optimization.
    """

    print("Setting up MLflow tracking...")

    TRACKING_SERVER_HOST = os.environ.get("MLFLOW_TRACKING_SERVER_HOST")
    if not TRACKING_SERVER_HOST:
        raise ValueError("MLFLOW_TRACKING_SERVER_HOST environment variable is not set!")

    mlflow.set_tracking_uri(f"http://{TRACKING_SERVER_HOST}:5000")
    MLFLOW_EXPERIMENT_NAME = os.environ.get("MLFLOW_EXPERIMENT_NAME")
    if not MLFLOW_EXPERIMENT_NAME:
        raise ValueError("MLFLOW_EXPERIMENT_NAME environment variable is not set!")
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    print(f"tracking URI: '{mlflow.get_tracking_uri()}'")

    print("Loading data configuration from S3 bucket...")
    # Load data configuration from an S3 bucket.
    # s3_bucket = S3Bucket.load("s3-bucket-config2")
    data_path = "data/raw/"

    # url = os.environ.get("S3_PRESIGNED_URL")
    # if not url:
    #     raise ValueError("S3_PRESIGNED_URL environment variable is not set!")
    # download_from_url_to_path(url)

    # Load URLs from the JSON config file
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    urls = config.get('S3_PRESIGNED_URLS', [])
    if not urls:
        raise ValueError("S3_PRESIGNED_URLS are not provided in the config!")

    # Loop through the URLs and download each one
    for url in urls:
        download_from_url_to_path(url)

    # Download data from the S3 bucket.
    # print("Downloading data from S3 bucket...")
    # data_path = load_data_from_s3(s3_bucket, data_path)

    # Read the raw data from the downloaded path.
    print("Reading raw data...")
    raw_data = read_data(data_path)

    # Filter and transform the raw data to retain only shot events.
    print("Filtering and transforming raw data...")
    shot_data = filter_and_transform_shot_data(raw_data)

    # Split the data into training, validation, and test sets.
    print("Splitting data into training, validation, and test sets...")
    df_train, df_val, df_test = split_data(shot_data)

    # print("df_train after splitting:", df_train.head())
    # print("df_val after splitting:", df_val.head())

    print("Preprocessing data for XGBoost...")
    dtrain, dval, _ = preprocess_data(df_train, df_val, df_test)

    # Train the model using hyperparameter optimization with Hyperopt.
    print("Training model using hyperparameter optimization...")
    _, best_run_id = hyperopt_train(dtrain, dval)

    # Register the best model in MLflow Model Registry.
    print("Registering the best model in MLflow Model Registry....")
    register_model_in_mlflow(best_run_id)

    print("Training pipeline completed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orchestrate the pipeline")
    parser.add_argument(
        '--config', required=True, help="Path to the configuration file"
    )

    args = parser.parse_args()
    main_flow_s3(args.config)
