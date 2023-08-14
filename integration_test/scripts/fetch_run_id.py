import os

import mlflow


def get_production_run_id(model_name="xgboost"):
    # Connect to the MLflow server
    TRACKING_SERVER_HOST = os.environ.get("MLFLOW_TRACKING_SERVER_HOST")
    if not TRACKING_SERVER_HOST:
        raise ValueError("MLFLOW_TRACKING_SERVER_HOST environment variable is not set!")

    mlflow.set_tracking_uri(f"http://{TRACKING_SERVER_HOST}:5000")
    client = mlflow.tracking.MlflowClient()

    # Fetch the latest version of the model in 'Production' stage
    latest_prod_model = client.get_latest_versions(
        name=model_name, stages=["Production"]
    )[0]

    return latest_prod_model.run_id


if __name__ == "__main__":
    run_id = get_production_run_id()
    print(run_id)
