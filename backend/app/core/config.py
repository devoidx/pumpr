from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    fuel_finder_client_id: str
    fuel_finder_client_secret: str
    fuel_finder_token_url: str = "https://www.fuel-finder.service.gov.uk/api/v1/oauth/generate_access_token"
    fuel_finder_api_url: str = "https://www.fuel-finder.service.gov.uk"
    poll_interval_minutes: int = 30
    secret_key: str
    environment: str = "production"
    ocm_api_key: str = ""
    ocm_api_url: str = "https://api.openchargemap.io/v3"
    bsky_handle: str = ""
    bsky_app_password: str = ""

    class Config:
        env_file = ".env"

settings = Settings()  # type: ignore[call-arg]
