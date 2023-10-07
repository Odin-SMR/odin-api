from io import BytesIO
from typing import BinaryIO, TypedDict
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError
from flask import current_app

s3 = boto3.client("s3")


class ObjectLocator(TypedDict):
    bucket: str
    object_key: str


def parse_bucket_uri(s3_uri: str):
    parsed_uri = urlparse(s3_uri)
    bucket_name = parsed_uri.netloc
    object_key = parsed_uri.path.lstrip("/")
    return ObjectLocator(bucket=bucket_name, object_key=object_key)


def s3_stat(uri: str):
    logger = current_app.logger.getChild("odin_aws.s3")
    logger.debug(f"Checking if {uri} exists")
    object_locator = parse_bucket_uri(uri)
    try:
        s3.head_object(
            Bucket=object_locator["bucket"], Key=object_locator["object_key"]
        )
    except s3.exceptions.NoSuchBucket as err:
        logger.warning(f"Can't access bucket {uri}: {err}")
        return False
    except s3.exceptions.NoSuchKey as err:
        logger.warning(f"Can't access object in {uri}: {err}")
        return False
    except ClientError as err:
        logger.warning(f"Unknown error while accessing {uri}: {err}")
        return False
    return True


def s3_fileobject(uri: str) -> BinaryIO | None:
    logger = current_app.logger.getChild("odin_aws.s3")
    logger.debug(f"Trying to read {uri}")
    object_locator = parse_bucket_uri(uri)
    file_object = BytesIO()
    try:
        s3.download_fileobj(
            Bucket=object_locator["bucket"],
            Key=object_locator["object_key"],
            Fileobj=file_object,
        )
    except ClientError as err:
        logger.warning(f"Error while accessing {uri}: {err}")
        return None
    file_object.seek(0)
    return file_object
