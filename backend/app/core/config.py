"""Application settings — loaded from environment at startup."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database — local PostgreSQL (psycopg 3 + pool).
    # Example: postgresql://postgres:<password>@localhost:5432/gaia_dev
    # Credentials must come from the environment; never commit them.
    database_url: str = "postgresql://postgres:postgres@localhost:5432/gaia_dev"

    # Supabase Auth compatibility (JWT verification only — no Supabase
    # database, storage, or hosted-auth dependency remains).
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

    # Document storage — local filesystem adapter (see app/storage/).
    # Supabase Storage is not used. Keep uploaded files out of Git.
    local_storage_dir: str = "data/uploads"

    # App
    app_name: str = "SIH 26130 Gujarat MVP"
    debug: bool = False

    # CORS — explicit origin allowlist (comma-separated). No wildcard is
    # ever used together with credentials. Production deployments must set
    # this to the deployed frontend origin(s).
    cors_allow_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def parse_cors_origins(raw: str) -> list[str]:
    """Parse a comma-separated origin allowlist, dropping blanks."""
    return [part.strip() for part in raw.split(",") if part.strip()]


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()
