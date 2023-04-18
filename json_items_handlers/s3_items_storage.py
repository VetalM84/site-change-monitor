"""Module to work with files on the AWS S3 bucket."""

import json
import os

import boto3
from dotenv import load_dotenv
from icecream import ic

from json_items_handlers.json_handler import JsonHandler

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")


class JsonItemsS3Storage(JsonHandler):
    """Class to work with json files contains items on AWS S3 bucket."""

    _file_dir: str = "../items_list_output"

    def __init__(self, file_name: str):
        super().__init__(file_name)
        self.bucket_name = AWS_STORAGE_BUCKET_NAME
        self.aws_access_key_id = AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = AWS_SECRET_ACCESS_KEY
        self.s3 = boto3.resource(
            service_name="s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        self.s3_object = self.s3.Object(
            bucket_name=self.bucket_name,
            key=self.set_full_path(),
        )

    def set_full_path(self) -> str:
        """Set full path to file on the S3 bucket."""
        return "/".join([self._file_dir, self._file_name])

    def read_json_file(self):
        """Read a json file from the S3 bucket."""
        try:
            content = json.loads(self.s3_object.get()["Body"].read().decode("utf-8"))
            return content
        except Exception as e:
            ic(e)
            return self.save_to_json_file({})

    def save_to_json_file(self, data) -> None:
        """Save a json file to the S3 bucket."""
        self.s3_object.put(
            Body=json.dumps(data, indent=4, ensure_ascii=False).encode("utf-8")
        )

    def append_to_json_file(self, data) -> None:
        """Append data to the existing json file on S3 bucket."""
        existing_data = self.read_json_file()
        existing_data.update(data)
        self.save_to_json_file(existing_data)
