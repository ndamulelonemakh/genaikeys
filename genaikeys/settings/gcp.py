from pydantic_settings import BaseSettings, SettingsConfigDict


class GCPSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    google_cloud_project: str
