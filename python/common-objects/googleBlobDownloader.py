# Imports the Google Cloud client library
from google.cloud import storage
from google.oauth2.service_account import Credentials


class googleBlobDownloader(object):

    # <Snippet_download_blob_file>
    def download_blob_to_file(self, storage_client: storage.Client, bucket_name:str, blob_flat_name:str, download_file_name:str):
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_flat_name)
        blob.download_to_filename(download_file_name)
     

