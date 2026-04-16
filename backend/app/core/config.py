from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    fuel_finder_client_id: str
    fuel_finder_client_secret: str
    fuel_finder_token_url: str = "https://api.fuel-finder.service.gov.uk/oauth/token"
    fuel_finder_api_url: str = "https://api.fuel-finder.service.gov.uk"
    poll_interval_minutes: int = 30
    secret_key: str
    environment: str = "production"

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore[call-arg]
