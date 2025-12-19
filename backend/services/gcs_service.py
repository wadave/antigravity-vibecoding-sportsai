# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from google.cloud import storage
from fastapi import UploadFile
import uuid

BUCKET_NAME = "dw-genai-dev-bucket"


class GCSService:
    def __init__(self):
        self.client = storage.Client()
        self.bucket = self.client.bucket(BUCKET_NAME)

    def upload_file(self, file_path: str, destination_blob_name: str):
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(file_path)
        return f"gs://{BUCKET_NAME}/{destination_blob_name}"

    def upload_bytes(self, data: bytes, destination_blob_name: str, content_type: str):
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_string(data, content_type=content_type)
        return f"gs://{BUCKET_NAME}/{destination_blob_name}"

    def download_file(self, blob_name: str, destination_file_path: str):
        blob = self.bucket.blob(blob_name)
        blob.download_to_filename(destination_file_path)

    def get_signed_url(self, blob_name: str):
        blob = self.bucket.blob(blob_name)
        return blob.generate_signed_url(version="v4", expiration=3600, method="GET")

    def parse_gs_uri(self, gs_uri: str):
        if not gs_uri.startswith("gs://"):
            raise ValueError("Invalid GS URI")
        parts = gs_uri[5:].split("/", 1)
        return parts[0], parts[1]
