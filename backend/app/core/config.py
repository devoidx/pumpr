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
    mastodon_instance: str = "https://mastodon.social"
    dvla_api_key: str = ""
    mastodon_access_token: str = ""
    bsky_app_password: str = ""
    threads_access_token: str = ""
    threads_user_id: str = ""
    resend_api_key: str = ""
    anthropic_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@pumpr.co.uk"
    app_base_url: str = "https://pumpr.co.uk"
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_monthly: str = ""
    stripe_price_annual: str = ""

    class Config:
        env_file = ".env"

settings = Settings()  # type: ignore[call-arg]
