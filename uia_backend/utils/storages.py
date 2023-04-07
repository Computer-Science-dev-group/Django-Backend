from storages.backends.s3boto3 import S3Boto3Storage  # pragma: no cover


class StaticRootS3Boto3Storage(S3Boto3Storage):  # pragma: no cover
    location = "static"
    default_acl = "public-read"


class MediaRootS3Boto3Storage(S3Boto3Storage):  # pragma: no cover
    location = "media"
    file_overwrite = False
