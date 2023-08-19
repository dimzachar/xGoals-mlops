# pylint: disable=duplicate-code
import os
import json
import logging

import boto3
from deepdiff import DeepDiff

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


kinesis_endpoint = os.getenv('KINESIS_ENDPOINT_URL', "http://localhost:4566")
kinesis_client = boto3.client('kinesis', endpoint_url=kinesis_endpoint)

stream_name = os.getenv('PREDICTIONS_STREAM_NAME', 'shot_predictions')
shard_id = 'shardId-000000000000'

shard_iterator_response = kinesis_client.get_shard_iterator(
    StreamName=stream_name,
    ShardId=shard_id,
    ShardIteratorType='TRIM_HORIZON',
)

shard_iterator_id = shard_iterator_response['ShardIterator']

records_response = kinesis_client.get_records(
    ShardIterator=shard_iterator_id,
    Limit=1,
)

records = records_response['Records']

# Use logger.info instead of print
logger.info(records)

# # Print each record
# for record in records:
#     decoded_data = json.loads(record['Data'])
#     print(json.dumps(decoded_data, indent=2))

assert len(records) == 1

actual_record = json.loads(records[0]['Data'])

# Use logger.info instead of print
logger.info(actual_record)

# Print the actual record
# print(json.dumps(actual_record, indent=2))

expected_record = {
    'model': 'xgoals_prediction_model',
    "version": os.getenv('RUN_ID'),
    'prediction': {
        'shot_xgoals': actual_record['prediction']['shot_xgoals'],
        'shot_id': 123,
    },
}

diff = DeepDiff(actual_record, expected_record, significant_digits=2)

# Use logger.info instead of print
logger.info('diff=%s', diff)

# print(f'diff={diff}')

assert 'values_changed' not in diff
assert 'type_changes' not in diff

# Use logger.info instead of print
logger.info('all good')
# print('all good')
