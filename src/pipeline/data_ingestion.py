import os

import pandas as pd
from prefect import task


@task
def load_data_from_s3(bucket, data_path):
    """
    Load data from the S3 bucket and save it to the local path.
    """
    print(f"Attempting to download data from S3 bucket to {data_path}...")
    try:
        bucket.download_folder_to_path(from_folder=data_path, to_folder=data_path)
        print(f"Data successfully downloaded to {data_path}.")
        return data_path
    except Exception as e:
        print(f"Failed to download data from S3. Error: {e}")
        raise ValueError(f"Failed to download data from S3. Error: {e}") from e


@task
def read_data(directory):
    """
    Read data from the directory.
    """
    print(f"Reading data from directory: {directory}...")
    data = pd.DataFrame()
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            print(f"Reading file: {filename}...")
            data_temp = pd.read_json(filepath)
            data = pd.concat([data, data_temp], ignore_index=True)
    print(f"Finished reading data from directory: {directory}.")
    return data
