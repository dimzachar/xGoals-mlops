# pylint: disable=redefined-outer-name
import os

import mlflow


def get_production_run_id(model_name="xgboost"):
    # Connect to the MLflow server
    TRACKING_SERVER_HOST = os.environ.get("MLFLOW_TRACKING_SERVER_HOST")
    if not TRACKING_SERVER_HOST:
        raise ValueError("MLFLOW_TRACKING_SERVER_HOST environment variable is not set!")

    mlflow.set_tracking_uri(f"http://{TRACKING_SERVER_HOST}:5000")
    client = mlflow.tracking.MlflowClient()

    # Fetch the experiment ID
    MLFLOW_EXPERIMENT_NAME = os.environ.get("MLFLOW_EXPERIMENT_NAME")
    if not MLFLOW_EXPERIMENT_NAME:
        raise ValueError("MLFLOW_EXPERIMENT_NAME environment variable is not set!")
    experiment_id = client.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME).experiment_id

    # Fetch the latest version of the model in 'Production' stage
    latest_prod_model = client.get_latest_versions(
        name=model_name, stages=["Production"]
    )[0]

    # Print the type and the object itself for debugging
    # print(f"Type of latest_prod_model: {type(latest_prod_model)}")
    # print(f"latest_prod_model: {latest_prod_model}")

    run_id = latest_prod_model.run_id

    return run_id, experiment_id


if __name__ == "__main__":
    run_id, experiment_id = get_production_run_id()
    print(f"{run_id}")
    print(f"{experiment_id}")
