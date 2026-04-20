import functools

import boto3

from ._settings import AWSSettings
from .types import SecretManagerPlugin


class AWSSecretsManagerPlugin(SecretManagerPlugin):
    def __init__(self, region_name: str | None = None, profile_name: str | None = None):
        overrides = {}
        if region_name is not None:
            overrides["aws_default_region"] = region_name
        if profile_name is not None:
            overrides["aws_profile"] = profile_name
        cfg = AWSSettings(**overrides)
        # Use a Session so that profile_name (SSO / IAM Identity Center) is applied.
        # All other keyless mechanisms (EC2 instance profile, ECS task role, Lambda
        # execution role, IRSA/EKS web identity) are picked up automatically by boto3's
        # credential chain and require no additional configuration.
        session = boto3.Session(
            profile_name=cfg.aws_profile,
            region_name=cfg.aws_default_region,
        )
        self.client = session.client("secretsmanager")

    def get_secret(self, secret_name: str) -> str:
        response = self.client.get_secret_value(SecretId=secret_name)
        return str(response["SecretString"])

    @functools.lru_cache(1, typed=True)  # noqa: B019
    def list_secrets(self, max_results: int = 100) -> list[str]:
        response = self.client.list_secrets(MaxResults=max_results)
        return [secret["Name"] for secret in response["SecretList"]]

    def exists(self, secret_name: str, **kwargs) -> bool:
        return secret_name in self.list_secrets()
