import os
import boto3
from botocore.exceptions import NoCredentialsError

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')
bucket_name = os.getenv('BUCKET_NAME')

s3 = boto3.client('s3',
                  aws_access_key_id=aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key,
                  region_name=aws_region)

def upload_file_to_s3(file_path, object_key):
    try:
        s3.upload_file(file_path, bucket_name, object_key)
        return object_key
    except FileNotFoundError:
        print("File Not Found Error")
        return False
    except NoCredentialsError:
        print("NoCredentialsError")
        return False
    
def get_presigned_url(bucket_name, object_key, expiration=3600):
    try:
        url = s3.generate_presigned_url('get_object',
                                        Params={'Bucket': bucket_name, 'Key': object_key},
                                        ExpiresIn=expiration)
        return url
    except Exception as e:
        return str(e)