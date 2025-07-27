from minio import Minio
from minio.error import S3Error
from app.config.settings import settings

class MinIOClient:
    def __init__(self):
        minio_config = settings["services"]["minio_s3"]
        self.client = Minio(
            minio_config["endpoint"],
            access_key=minio_config["access_key"],
            secret_key=minio_config["secret_key"],
            secure=False  # Use True for HTTPS
        )
        self.bucket_name = minio_config["bucket_name"]
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Bucket '{self.bucket_name}' created successfully.")
        except S3Error as e:
            print(f"Error checking/creating bucket: {e}")
            raise

    def upload_file(self, object_name: str, file_path: str):
        """Uploads a file to the MinIO bucket."""
        try:
            self.client.fput_object(self.bucket_name, object_name, file_path)
            print(f"'{file_path}' successfully uploaded as '{object_name}' to bucket '{self.bucket_name}'.")
        except S3Error as e:
            print(f"Error uploading file: {e}")
            raise

    def download_file(self, object_name: str, file_path: str):
        """Downloads a file from the MinIO bucket."""
        try:
            self.client.fget_object(self.bucket_name, object_name, file_path)
            print(f"'{object_name}' successfully downloaded to '{file_path}'.")
        except S3Error as e:
            print(f"Error downloading file: {e}")
            raise

# Instantiate the MinIOClient globally or as needed
minio_client = MinIOClient()
