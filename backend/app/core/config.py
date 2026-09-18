from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = "development"
    database_url: str

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Comma-separated list of origins allowed to call this API from a
    # browser. Defaults cover the dev API-tester page and the eventual
    # local React dev server. Tighten this to the real frontend's origin
    # before any production deployment (see CAREMATE_MASTER_SPEC.md section 32).
    cors_origins: str = "http://127.0.0.1:8080,http://localhost:8080,http://127.0.0.1:5173,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # Deployment-tunable; the allowed content types themselves are a fixed
    # business rule, not something that varies by environment, so that
    # whitelist lives as a constant in app/api/routes/documents.py instead.
    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB


settings = Settings()
