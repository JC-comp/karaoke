import json
import io

try:
    from urllib3.response import BaseHTTPResponse
except ImportError:
    from urllib3.response import HTTPResponse as BaseHTTPResponse

from enum import Enum
from minio import Minio
from minio.helpers import ObjectWriteResult
from minio.datatypes import Object
from pathlib import Path
from typing import Tuple, Any
from ..config import config

class BucketType(Enum):
    ARG_BUCKET = 'task-args'
    STORAGE_BUCKET =  'task-storage'

class Storage:
    def __init__(self):
        self.client = Minio(
            config.storage.endpoint,
            config.storage.access_key,
            config.storage.secret_key,
            secure=config.storage.secure
        )
    
    def _split_path(self, path: str) -> Tuple[str, str]:
        """
        Parses a unified path string into bucket and object components.

        Args:
            path: A string in the format 'bucket-name/folder/object.ext'.

        Returns:
            A tuple containing (bucket_name, object_key).

        Raises:
            ValueError: If the path does not contain at least one slash.
        """
        parts = path.split('/', 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid storage path: '{path}'. "
                "Must be in 'bucket/object' format."
            )
        return parts[0], parts[1]

    def read_json(self, path: str) -> Any:
        """
        Fetches a JSON object from a specific path and parses it.

        Args:
            path: The 'bucket/key' string.

        Returns:
            The decoded JSON content as a dictionary or list.
        """
        bucket, key = self._split_path(path)
        
        with self.client.get_object(bucket, key) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)

    def download(self, path: str,  filepath: str) -> Object:
        """
        Downloads an object from Minio directly to the local filesystem.

        Args:
            path: String in 'bucket/object' format.
            filepath: The local path where the file should be saved.

        Returns:
            The Minio Stat object containing metadata about the downloaded file.
        """
        
        bucket, key = self._split_path(path)
        
        dest_path = Path(filepath)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        return self.client.fget_object(
            bucket,
            key,
            filepath
        )

    def upload_file(self, bucket_type: BucketType, key: str, filepath: str) -> ObjectWriteResult:
        """
        Uploads file to a specific path.
        
        Args:
            bucket: bucket string.
            key: key string
            filepath: file to upload.
        """
        return self.client.fput_object(
            bucket_type.value,
            key,
            filepath
        )
    
    def put_binary(self, bucket_type: BucketType, key: str, data: bytes, content_type: str = "application/octet-stream") -> ObjectWriteResult:
        """
        Uploads raw bytes to a specific path.
        
        Args:
            bucket: bucket string.
            key: key string
            data: Raw bytes to upload.
            content_type: MIME type of the file.
        """
        data_stream = io.BytesIO(data)
        
        return self.client.put_object(
            bucket_name=bucket_type.value,
            object_name=key,
            data=data_stream,
            length=len(data),
            content_type=content_type
        )

    def stat_object(self, path: str) -> Object:
        bucket, key = self._split_path(path)
        response = self.client.stat_object(bucket, key)
        return response

    def stream_binary(self, path: str, **kargs) -> BaseHTTPResponse:
        bucket, key = self._split_path(path)
        response = self.client.get_object(bucket, key, **kargs)
        return response