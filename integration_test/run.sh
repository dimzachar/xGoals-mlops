#!/usr/bin/env bash

if [[ -z "${GITHUB_ACTIONS}" ]]; then
  cd "$(dirname "$0")"
fi

if [ "${LOCAL_IMAGE_NAME}" == "" ]; then
    LOCAL_TAG=`date +"%Y-%m-%d-%H-%M"`
    export LOCAL_IMAGE_NAME="xgoals_prediction_model:${LOCAL_TAG}"
    echo "LOCAL_IMAGE_NAME is not set, building a new image with tag ${LOCAL_IMAGE_NAME}"
    docker build -t ${LOCAL_IMAGE_NAME} ..
else
    echo "no need to build image ${LOCAL_IMAGE_NAME}"
fi

export PREDICTIONS_STREAM_NAME="shot_predictions"

docker-compose up -d

sleep 5

aws --endpoint-url=http://localhost:4566 \
    kinesis create-stream \
    --stream-name ${PREDICTIONS_STREAM_NAME} \
    --shard-count 1


# Fetch the run_id of the production model from MLflow
RUN_ID=$(python scripts/fetch_run_id.py)
echo "Fetched run_id: $RUN_ID"
export RUN_ID

# Download the model artifacts from S3
S3_BUCKET="xgoals-test-exp"
S3_PREFIX="9"
# Create the destination directory if it doesn't exist
DEST_DIR="model"

# Define the S3 path and copy model data from S3 to the destination directory
S3_PATH="s3://${S3_BUCKET}/${S3_PREFIX}/${RUN_ID}/artifacts/model/"
aws s3 cp --recursive $S3_PATH $DEST_DIR


pipenv run python test_docker.py

ERROR_CODE=$?

if [ ${ERROR_CODE} != 0 ]; then
    docker-compose logs
    docker-compose down
    exit ${ERROR_CODE}
fi


pipenv run python test_kinesis.py

ERROR_CODE=$?

if [ ${ERROR_CODE} != 0 ]; then
    docker-compose logs
    docker-compose down
    exit ${ERROR_CODE}
fi


docker-compose down
