import functools

import boto3

from ._settings import AWSSettings
from .types import SecretManagerPlugin


class AWSSecretsManagerPlugin(SecretManagerPlugin):
    def __init__(self, region_name: str | None = None):
        overrides = {}
        if region_name is not None:
            overrides["aws_default_region"] = region_name
        cfg = AWSSettings(**overrides)
        self.client = boto3.client('secretsmanager', region_name=cfg.aws_default_region)

    def get_secret(self, secret_name: str) -> str:
        response = self.client.get_secret_value(SecretId=secret_name)
        return response['SecretString']

    @functools.lru_cache(1, typed=True)
    def list_secrets(self, max_results: int = 100) -> list[str]:
        response = self.client.list_secrets(MaxResults=max_results)
        return [secret['Name'] for secret in response['SecretList']]

    def exists(self, secret_name: str, **kwargs) -> bool:
        return secret_name in self.list_secrets()
