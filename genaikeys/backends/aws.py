import logging

import boto3

from ..plugins.base import SecretManagerPlugin
from ..settings.aws import AWSSettings

logger = logging.getLogger(__name__)


class AWSSecretsManagerPlugin(SecretManagerPlugin):
    def __init__(self, region_name: str | None = None, profile_name: str | None = None):
        overrides = {}
        if region_name is not None:
            overrides["aws_default_region"] = region_name
        if profile_name is not None:
            overrides["aws_profile"] = profile_name
        cfg = AWSSettings(**overrides)
        session = boto3.Session(
            profile_name=cfg.aws_profile,
            region_name=cfg.aws_default_region,
        )
        self.client = session.client("secretsmanager")
        self._list_secrets_cache: dict[int, list[str]] = {}
        logger.debug(
            "AWS Secrets Manager client initialized (region=%s, profile=%s)",
            cfg.aws_default_region,
            cfg.aws_profile,
        )

    def get_secret(self, secret_name: str) -> str:
        logger.debug("AWS get_secret_value SecretId=%r", secret_name)
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
        except Exception as exc:
            logger.error("AWS get_secret_value failed for %r: %s", secret_name, type(exc).__name__)
            raise
        return str(response["SecretString"])

    def list_secrets(self, max_results: int = 100) -> list[str]:
        if max_results in self._list_secrets_cache:
            return self._list_secrets_cache[max_results]
        response = self.client.list_secrets(MaxResults=max_results)
        result = [secret["Name"] for secret in response["SecretList"]]
        self._list_secrets_cache[max_results] = result
        return result

    def exists(self, secret_name: str, **kwargs) -> bool:
        return secret_name in self.list_secrets()
