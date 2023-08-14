# pylint: disable=duplicate-code
import os
import json

import requests
from deepdiff import DeepDiff


def invoke_lambda(url, event):
    """Invoke the lambda function and return the response."""
    response = requests.post(url, json=event, timeout=5)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()


def main():
    # Load the event data
    with open('event.json', 'rt', encoding='utf-8') as f_in:
        event = json.load(f_in)

    # Define the URL for lambda invocation
    url = 'http://localhost:8080/2015-03-31/functions/function/invocations'

    # Invoke the lambda function and get the actual response
    actual_response = invoke_lambda(url, event)
    print('Actual response:')
    print(json.dumps(actual_response, indent=2))

    # Define the expected response
    expected_response = {
        'predictions': [
            {
                'model': 'xgoals_prediction_model',
                "version": os.getenv('RUN_ID'),
                'prediction': {
                    'shot_xgoals': 0.26,
                    'shot_id': 123,
                },
            }
        ]
    }

    # Compare the actual and expected responses
    diff = DeepDiff(actual_response, expected_response, significant_digits=2)
    print(f'diff={diff}')

    # Assert that there are no type changes or value changes in the diff
    assert 'type_changes' not in diff
    assert 'values_changed' not in diff


if __name__ == "__main__":
    main()
