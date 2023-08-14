import os
import json
import base64
import logging

import boto3
import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient

# Only import xgboost if it's being used in your code
# import xgboost as xgb

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_production_run_id(model_name="xgboost"):
    """
    Get the run_id of the model that's in the "Production" stage.

    Parameters:
    - model_name: The name of the registered model.

    Returns:
    - run_id: The ID of the MLflow run that produced the "Production" model.
    """
    mlflow.set_tracking_uri("http://ec2-54-172-188-75.compute-1.amazonaws.com:5000")
    client = MlflowClient()
    production_version = client.get_latest_versions(model_name, stages=["Production"])[
        0
    ]
    return production_version.run_id


def get_model_location(run_id):
    model_location = os.getenv('MODEL_LOCATION')

    if model_location is not None:
        return model_location

    model_bucket = os.getenv('MODEL_BUCKET', 'xgoals-test-exp')
    experiment_id = os.getenv('MLFLOW_EXPERIMENT_ID', '1')

    model_location = f's3://{model_bucket}/{experiment_id}/{run_id}/artifacts/model'
    return model_location


def load_model(run_id):
    model_path = get_model_location(run_id)
    model = mlflow.pyfunc.load_model(model_path)
    return model


def base64_decode(encoded_data):
    decoded_data = base64.b64decode(encoded_data).decode('utf-8')
    shot_event = json.loads(decoded_data)
    return shot_event


class ModelService:
    def __init__(self, model, model_version=None, callbacks=None):
        self.model = model
        self.model_version = model_version
        self.callbacks = callbacks or []

    def prepare_features(self, shot):
        features = {}
        features['distance_to_goal'] = shot['distance_to_goal']
        features['angle_to_goal'] = shot['angle_to_goal']
        return features

    def predict(self, features):
        df = pd.DataFrame([features])
        pred = self.model.predict(df)
        logger.info("Prediction: %s", pred[0])
        return float(pred[0])

    def lambda_handler(self, event):
        # print(json.dumps(event))

        predictions_events = []

        for record in event['Records']:
            encoded_data = record['kinesis']['data']
            shot_event = base64_decode(encoded_data)

            # print(shot_event)
            shot = shot_event['shot']
            shot_id = shot_event['shot_id']

            features = self.prepare_features(shot)
            prediction = self.predict(features)

            prediction_event = {
                'model': 'xgoals_prediction_model',
                'version': self.model_version,
                'prediction': {'shot_xgoals': prediction, 'shot_id': shot_id},
            }

            for callback in self.callbacks:
                callback(prediction_event)

            predictions_events.append(prediction_event)

        return {'predictions': predictions_events}


class KinesisCallback:
    def __init__(self, kinesis_client, prediction_stream_name):
        self.kinesis_client = kinesis_client
        self.prediction_stream_name = prediction_stream_name

    def put_record(self, prediction_event):
        shot_id = prediction_event['prediction']['shot_id']

        self.kinesis_client.put_record(
            StreamName=self.prediction_stream_name,
            Data=json.dumps(prediction_event),
            PartitionKey=str(shot_id),
        )


def create_kinesis_client():
    endpoint_url = os.getenv('KINESIS_ENDPOINT_URL')

    if endpoint_url is None:
        return boto3.client('kinesis')

    return boto3.client('kinesis', endpoint_url=endpoint_url)


def init(prediction_stream_name: str, test_run: bool):
    run_id = get_production_run_id()
    model = load_model(run_id)

    callbacks = []

    if not test_run:
        kinesis_client = create_kinesis_client()
        kinesis_callback = KinesisCallback(kinesis_client, prediction_stream_name)
        callbacks.append(kinesis_callback.put_record)

    model_service = ModelService(model=model, model_version=run_id, callbacks=callbacks)

    return model_service
