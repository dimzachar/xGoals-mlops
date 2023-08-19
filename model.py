import os
import json
import base64
import logging
import datetime

import boto3
import mlflow
import pandas as pd
import psycopg2
from evidently import ColumnMapping
from mlflow.tracking import MlflowClient
from evidently.report import Report
from evidently.metrics import (
    ColumnDriftMetric,
    DatasetDriftMetric,
    ColumnQuantileMetric,
    DatasetMissingValuesMetric,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUFFER_THRESHOLD = 10  # Adjust based on your preference

create_table_statement = """
CREATE TABLE IF NOT EXISTS opt_metrics(
    timestamp TIMESTAMP,
    prediction_drift FLOAT,
    num_drifted_columns INTEGER,
    share_missing_values FLOAT,
    distance_to_goal_quantile float
)
"""


column_mapping = ColumnMapping(
    prediction='prediction',
    numerical_features=['distance_to_goal', 'angle_to_goal'],
    categorical_features=[],
    target=None,
)
report = Report(
    metrics=[
        ColumnDriftMetric(column_name='prediction'),
        DatasetDriftMetric(),
        DatasetMissingValuesMetric(),
        ColumnQuantileMetric(column_name='distance_to_goal', quantile=0.5),
    ]
)


def prep_db():
    logger.debug('Preparing the database...')

    # Connect to the default 'postgres' database to check if 'test' exists
    with psycopg2.connect(
        "host=db port=5432 dbname=postgres user=postgres password=example"
    ) as conn:
        conn.autocommit = (
            True  # Enable autocommit mode to execute the CREATE DATABASE command
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname='test'")
            if cur.fetchone() is None:
                cur.execute("CREATE DATABASE test;")

    # Now, connect to the 'test' database and create the table
    with psycopg2.connect(
        "host=db port=5432 dbname=test user=postgres password=example"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_statement)


def get_production_run_id(model_name="xgboost"):
    logger.debug('Fetching production run ID...')
    TRACKING_SERVER_HOST = os.environ.get("MLFLOW_TRACKING_SERVER_HOST")
    if not TRACKING_SERVER_HOST:
        raise ValueError("MLFLOW_TRACKING_SERVER_HOST environment variable is not set!")

    mlflow.set_tracking_uri(f"http://{TRACKING_SERVER_HOST}:5000")

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


def load_model_and_reference_data(run_id):
    logger.debug('Loading model and reference data for run ID: %s', run_id)
    model_path = get_model_location(run_id)
    logger.info("Loading model from: %s", model_path)
    model = mlflow.pyfunc.load_model(model_path)

    reference_data_path = os.path.join(model_path, 'reference_data.parquet')
    logger.info("Loading reference data from: %s", reference_data_path)
    reference_data = pd.read_parquet(reference_data_path)

    return model, reference_data


def base64_decode(encoded_data):
    decoded_data = base64.b64decode(encoded_data).decode('utf-8')
    shot_event = json.loads(decoded_data)
    return shot_event


class ModelService:
    def __init__(self, model, reference_data, model_version=None, callbacks=None):
        self.model = model
        self.reference_data = reference_data
        self.model_version = model_version
        self.callbacks = callbacks or []
        self.data_buffer = []

    def prepare_features(self, shot):
        logger.info("Preparing features for shot")
        features = {}
        features['distance_to_goal'] = shot['distance_to_goal']
        features['angle_to_goal'] = shot['angle_to_goal']
        return features

    def predict(self, features):
        df = pd.DataFrame([features])
        pred = self.model.predict(df)
        logger.info("Prediction: %s", pred[0])
        return float(pred[0])

    def monitor_drift(self):
        logger.debug('Buffer threshold reached. Starting drift monitoring...')
        logger.info("Monitoring drift")
        current_data = pd.DataFrame(self.data_buffer)

        logger.info("Running report for drift check")

        report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=column_mapping,
        )

        result = report.as_dict()

        prediction_drift = result['metrics'][0]['result']['drift_share']
        num_drifted_columns = result['metrics'][1]['result'][
            'number_of_drifted_columns'
        ]
        share_missing_values = result['metrics'][2]['result']['current'][
            'share_of_missing_values'
        ]
        distance_to_goal_quantile = result['metrics'][3]['result']['current']['value']
        print(result)
        print(
            "Quantile value for distance_to_goal column (quantile=0.5):",
            distance_to_goal_quantile,
        )
        logger.info("Prediction drift: %s", prediction_drift)
        logger.info("Number of drifted columns: %s", num_drifted_columns)
        logger.info("Share of missing values: %s", share_missing_values)
        logger.info("Distance to goal 50th percentile: %s", distance_to_goal_quantile)

        # insert_query = (
        #     "INSERT INTO opt_metrics ("
        #     "    timestamp, prediction_drift, num_drifted_columns, "
        #     "    share_missing_values, distance_to_goal_quantile"
        #     ") VALUES (%s, %s, %s, %s, %s)"
        # )

        logger.debug('Inserting drift metrics into database...')
        with psycopg2.connect(
            "host=db port=5432 dbname=test user=postgres password=example",  # autocommit=True
        ) as conn:
            with conn.cursor() as cur:
                insert_statement = """
                INSERT INTO opt_metrics (
                    timestamp, 
                    prediction_drift, 
                    num_drifted_columns, 
                    share_missing_values, 
                    distance_to_goal_quantile
                )
                VALUES (%s, %s, %s, %s, %s)
                """
                cur.execute(
                    insert_statement,
                    (
                        datetime.datetime.utcnow(),
                        prediction_drift,
                        num_drifted_columns,
                        share_missing_values,
                        distance_to_goal_quantile,
                    ),
                )
        logger.info("Saved drift metrics to database")

    def lambda_handler(self, event):
        try:
            predictions_events = []

            for record in event['Records']:
                encoded_data = record['kinesis']['data']
                shot_event = base64_decode(encoded_data)
                shot = shot_event['shot']
                shot_id = shot_event['shot_id']

                features = self.prepare_features(shot)
                prediction = self.predict(features)

                self.data_buffer.append(
                    {
                        'distance_to_goal': shot['distance_to_goal'],
                        'angle_to_goal': shot['angle_to_goal'],
                        'prediction': prediction,
                    }
                )
                logger.debug(
                    'Adding prediction to data buffer. Buffer size: %s',
                    len(self.data_buffer) + 1,
                )

                prediction_event = {
                    'model': 'xgoals_prediction_model',
                    'version': self.model_version,
                    'prediction': {'shot_xgoals': prediction, 'shot_id': shot_id},
                }

                for callback in self.callbacks:
                    callback(prediction_event)

                predictions_events.append(prediction_event)

            if len(self.data_buffer) >= BUFFER_THRESHOLD:
                self.monitor_drift()
                self.data_buffer = []  # Clear the buffer

            return {'predictions': predictions_events}
        except Exception as e:
            logger.error("Error processing event: %s", e)
            return {"error": f"Failed to process event. Error: {e}"}


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
    logger.debug('Model Service initialization started...')
    # setup_database()
    prep_db()  # Initialize the database
    run_id = get_production_run_id()
    model, reference_data = load_model_and_reference_data(run_id)

    callbacks = []
    if not test_run:
        kinesis_client = create_kinesis_client()
        kinesis_callback = KinesisCallback(kinesis_client, prediction_stream_name)
        callbacks.append(kinesis_callback.put_record)

    model_service = ModelService(
        model=model,
        reference_data=reference_data,
        model_version=run_id,
        callbacks=callbacks,
    )
    logger.debug('Model Service initialization completed.')
    logger.info("Initialized ModelService with model version: %s", run_id)
    return model_service