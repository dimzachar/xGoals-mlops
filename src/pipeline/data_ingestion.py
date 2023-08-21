import os

import pandas as pd
import requests
from prefect import task


@task
def download_from_url_to_path(url, save_path="data/raw/"):
    """
    Download data from a given URL and save it to the specified directory.

    :param url: str, The URL from which data should be downloaded.
    :param save_path: str, The path to the directory where data should be saved.
    :return: str, Path to the downloaded file.
    """

    # Extract filename from the URL
    filename = url.split("/")[-1].split("?")[0]
    if ".json" in filename:
        filename = filename.split(".json")[0] + ".json"

    TIMEOUT_SECONDS = 10

    # Use requests to download the file
    with requests.get(url, stream=True, timeout=TIMEOUT_SECONDS) as r:
        r.raise_for_status()

        # Create a directory if it doesn't exist
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # Save the file to the directory
        with open(os.path.join(save_path, filename), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return os.path.join(save_path, filename)


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
