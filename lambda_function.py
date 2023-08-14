import os
import logging

import model

logger = logging.getLogger()
logger.setLevel(logging.INFO)


PREDICTIONS_STREAM_NAME = os.getenv('PREDICTIONS_STREAM_NAME', 'shot_predictions')
# RUN_ID = os.getenv('RUN_ID')
TEST_RUN = os.getenv('TEST_RUN', 'False') == 'True'


model_service = model.init(
    prediction_stream_name=PREDICTIONS_STREAM_NAME,
    # run_id=RUN_ID,
    test_run=TEST_RUN,
)


def lambda_handler(event, context):
    # pylint: disable=unused-argument
    logging.info('Lambda function has been triggered.')
    result = model_service.lambda_handler(event)
    logging.info('Model service returned: %s', result)
    return result
