"""AWS module for the AWS S3 bucket."""

import json
import os

import boto3

from dotenv import load_dotenv

load_dotenv()


AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")


class AWS:
    """Class to work with AWS S3 bucket."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION_NAME,
        )

    def upload_file(self, file_name: str, data):
        """Upload a file to an S3 bucket."""
        self.client.put_object(
            Bucket=AWS_STORAGE_BUCKET_NAME, Key=file_name, Body=json.dumps(data)
        )

    def download_file(self, file_name: str):
        """Download a file from an S3 bucket."""
        response = self.client.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=file_name)
        content = response["Body"].read().decode("utf-8")
        return content

    def get_file_list(self, file_extension: str = ".json") -> list:
        """Get a list of files from an S3 bucket."""
        response = self.client.list_objects_v2(Bucket=AWS_STORAGE_BUCKET_NAME)
        json_file_names = []
        for obj in response.get("Contents", []):
            key = obj["Key"]
            if key.endswith(file_extension):
                json_file_names.append(key)
        return json_file_names
