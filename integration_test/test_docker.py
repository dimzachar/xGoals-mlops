# pylint: disable=duplicate-code
import os
import json

import requests
from deepdiff import DeepDiff

with open('event.json', 'rt', encoding='utf-8') as f_in:
    event = json.load(f_in)


url = 'http://localhost:8080/2015-03-31/functions/function/invocations'
actual_response = requests.post(url, json=event, timeout=5).json()
print('actual response:')

print(json.dumps(actual_response, indent=2))

expected_response = {
    'predictions': [
        {
            'model': 'xgoals_prediction_model',
            "version": os.getenv('RUN_ID'),
            'prediction': {
                'shot_xgoals': 0.25,
                'shot_id': 123,
            },
        }
    ]
}


diff = DeepDiff(actual_response, expected_response, significant_digits=2)
print(f'diff={diff}')

assert 'type_changes' not in diff
assert 'values_changed' not in diff


url = 'http://localhost:8080/2015-03-31/functions/function/invocations'
response = requests.post(url, json=event, timeout=5)
print(response.json())

# try:
#     response = requests.post(url, json=event).json()
# except json.JSONDecodeError:
#     print(f"Failed to decode JSON. Response: {response.text}")

# print("Status Code:", response.status_code)
# print("Response Body:", response.text)

# try:
#     print("JSON Response:", response.json())
# except ValueError:
#     print("Cannot decode JSON response")


# try:
#     print("JSON Response:", response.json())
# except ValueError:
#     print("Cannot decode JSON response. Here is the raw response:")
#     print(response.text)
