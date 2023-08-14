import mlflow
from prefect import flow
from prefect_aws import S3Bucket
from data_ingestion import read_data, load_data_from_s3
from model_registry import register_model_in_mlflow
from model_training import hyperopt_train
from data_preprocessing import (
    split_data,
    preprocess_data,
    filter_and_transform_shot_data,
)


@flow
def main_flow_s3():
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
    # Set up MLflow tracking using a local SQLite database.
    # mlflow.set_tracking_uri("sqlite:///mlflow.db")
    # mlflow.set_experiment("xgoals-experiment")

    # Uncomment the following lines if you want to set up MLflow tracking using a remote server.
    TRACKING_SERVER_HOST = "ec2-54-172-188-75.compute-1.amazonaws.com"
    mlflow.set_tracking_uri(f"http://{TRACKING_SERVER_HOST}:5000")
    mlflow.set_experiment("xgoals-experiment")
    print(f"tracking URI: '{mlflow.get_tracking_uri()}'")

    print("Loading data configuration from S3 bucket...")
    # Load data configuration from an S3 bucket.
    s3_bucket = S3Bucket.load("s3-bucket-config2")
    data_path = "data/raw/"

    # Download data from the S3 bucket.
    print("Downloading data from S3 bucket...")
    data_path = load_data_from_s3(s3_bucket, data_path)

    # Read the raw data from the downloaded path.
    print("Reading raw data...")
    raw_data = read_data(data_path)

    # Filter and transform the raw data to retain only shot events.
    print("Filtering and transforming raw data...")
    shot_data = filter_and_transform_shot_data(raw_data)

    # Split the data into training, validation, and test sets.
    print("Splitting data into training, validation, and test sets...")
    df_train, df_val, df_test = split_data(shot_data)

    # Preprocess the data and convert it into DMatrix format for XGBoost.
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
    main_flow_s3()
