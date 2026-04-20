from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    aws_default_region: str
    aws_profile: str | None = None
