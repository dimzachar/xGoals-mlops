import logging

import mlflow
from prefect import task
from mlflow.tracking import MlflowClient

logging.basicConfig(level=logging.INFO)


@task(log_prints=True)
def register_model_in_mlflow(run_id, model_name="xgboost"):
    """
    Register a model with MLflow's Model Registry.

    Parameters:
    - run_id: The ID of the MLflow run that produced the model.
    - model_name: The name to give to the registered model.
    """

    # Create an MLflow client
    client = MlflowClient()

    # Check if the model name already exists in the registry
    try:
        client.create_registered_model(model_name)
    except mlflow.exceptions.MlflowException as e:
        # Model name already exists, which is fine
        logging.info(
            "Encountered an exception while trying to create a registered model: %s", e
        )

    # Register the model with the Model Registry
    model_uri = f"runs:/{run_id}/model"
    registered_model_details = client.create_model_version(
        name=model_name, source=model_uri, run_id=run_id
    )

    # Transition the model version to 'Production' or other stages
    client.transition_model_version_stage(
        name=model_name, version=registered_model_details.version, stage="Production"
    )

    print(
        f"Registered model '{model_name}' as version {registered_model_details.version}"
    )
