import io
import os
import boto3
from boto3.s3.transfer import TransferConfig

class awsS3Downloader(object):

    def download_s3object_to_file(self, s3_client:boto3.client,s3_bucket_name:str,s3_object_name:str,download_file_name:str ):
        s3_client.download_file(s3_bucket_name,s3_object_name, download_file_name)



