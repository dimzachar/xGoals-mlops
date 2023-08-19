from pathlib import Path

import model


def read_text(file):
    test_directory = Path(__file__).parent

    with open(test_directory / file, 'rt', encoding='utf-8') as f_in:
        return f_in.read().strip()


def test_base64_decode():
    base64_input = read_text('data.b64')

    actual_result = model.base64_decode(base64_input)
    expected_result = {
        "shot": {"angle_to_goal": 1.2, "distance_to_goal": 5.1},
        "shot_id": 123,
    }

    assert actual_result == expected_result


def test_prepare_features():
    dummy_reference_data = None  # Dummy value
    model_service = model.ModelService(None, dummy_reference_data)

    shot = {"angle_to_goal": 1.2, "distance_to_goal": 5.1}

    actual_features = model_service.prepare_features(shot)

    expected_fetures = {"angle_to_goal": 1.2, "distance_to_goal": 5.1}

    assert actual_features == expected_fetures


class ModelMock:
    def __init__(self, value):
        self.value = value

    def predict(self, X):
        n = len(X)
        return [self.value] * n


def test_predict():
    model_mock = ModelMock(10.0)
    dummy_reference_data = None  # Dummy value
    model_service = model.ModelService(model_mock, dummy_reference_data)

    features = {"angle_to_goal": 1.2, "distance_to_goal": 5.1}

    actual_prediction = model_service.predict(features)
    expected_prediction = 10.0

    assert actual_prediction == expected_prediction


def test_lambda_handler():
    model_mock = ModelMock(10.0)
    model_version = 'Test223'
    dummy_reference_data = None  # Dummy value
    model_service = model.ModelService(model_mock, dummy_reference_data, model_version)

    base64_input = read_text('data.b64')

    event = {
        "Records": [
            {
                "kinesis": {
                    "data": base64_input,
                },
            }
        ]
    }

    actual_predictions = model_service.lambda_handler(event)
    expected_predictions = {
        'predictions': [
            {
                'model': 'xgoals_prediction_model',
                'version': model_version,
                'prediction': {
                    'shot_xgoals': 10.0,
                    'shot_id': 123,
                },
            }
        ]
    }

    assert actual_predictions == expected_predictions
