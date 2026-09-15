"""Application settings — loaded from environment at startup."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str = "http://localhost:54321"
    supabase_key: str = "placeholder-key"
    supabase_service_role_key: str | None = None

    # Auth / JWT
    # The JWT secret used by Supabase Auth to sign tokens.
    # In production this is the "JWT Secret" from the Supabase dashboard → Settings → API.
    # It is NOT the service-role key — it is a separate HMAC secret shared with GoTrue.
    auth_jwt_secret: str = "placeholder-jwt-secret"
    auth_jwt_algorithm: str = "HS256"
    # Expected audience claim. Supabase sets this to the project reference URL by default,
    # but for local dev it may be "authenticated" or the supabase_url.
    auth_jwt_audience: str = "authenticated"

    # Storage
    supabase_storage_bucket: str = "documents"

    # App
    app_name: str = "SIH 26130 Gujarat MVP"
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()
