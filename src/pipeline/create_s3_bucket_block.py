import os
from time import sleep

from prefect_aws import S3Bucket, AwsCredentials


def create_aws_creds_block():
    """
    Create and save AWS credentials using environment variables.
    """
    print("Creating AWS credentials block...")

    # Fetch AWS credentials from environment variables
    my_aws_creds_obj = AwsCredentials(
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )

    # Save the AWS credentials
    my_aws_creds_obj.save(name="my-aws-creds2", overwrite=True)

    print("AWS credentials block created and saved successfully.")


def create_s3_bucket_block():
    """
    Load AWS credentials and create an S3 bucket configuration.
    """
    print("Creating S3 bucket configuration block...")

    # Load the previously saved AWS credentials
    aws_creds = AwsCredentials.load("my-aws-creds2")

    # Create an S3 bucket configuration using the loaded credentials
    my_s3_bucket_obj = S3Bucket(
        bucket_name="events-football-data", credentials=aws_creds
    )

    # Save the S3 bucket configuration
    my_s3_bucket_obj.save(name="s3-bucket-config2", overwrite=True)

    print("S3 bucket configuration block created and saved successfully.")


if __name__ == "__main__":
    create_aws_creds_block()

    # Wait for a short duration before proceeding to the next step
    print("Waiting for 5 seconds...")
    sleep(5)

    create_s3_bucket_block()
