from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SystemForge AI API"
    app_env: str = "development"
    api_prefix: str = "/api"
    api_version: str = "v1"
    api_deprecation_policy_url: str = "https://semver.org/"
    api_deprecated_after: str = ""
    api_sunset_at: str = ""
    cors_origins: str = "http://localhost:3000"
    # Public share links point to the frontend (e.g. https://app.example.com/share/<token>).
    public_app_url: str = "http://localhost:3000"

    # PDF: optional Mermaid → PNG via Kroki (POST JSON to kroki_url). Disable for air-gapped CI.
    mermaid_pdf_render_enabled: bool = True
    kroki_url: str = "https://kroki.io"
    kroki_timeout_seconds: float = 20.0

    database_url: str = "postgresql+psycopg://systemforge:systemforge@localhost:5432/systemforge"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60 * 12
    refresh_exp_days: int = 14
    auth_cookie_name: str = "sf_access_token"
    refresh_cookie_name: str = "sf_refresh_token"
    csrf_cookie_name: str = "sf_csrf_token"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    # OpenAI-compatible Chat Completions base URL (no trailing /chat). Examples:
    # https://api.openai.com/v1 | https://api.groq.com/openai/v1 | http://host.docker.internal:11434/v1 (Ollama)
    openai_base_url: str = "https://api.openai.com/v1"
    generation_timeout_seconds: int = 90
    max_generation_payload_bytes: int = 65536

    rate_limit_per_minute: int = 30
    sentry_dsn: str = ""
    auto_create_tables: bool = False
    outbox_relay_batch_size: int = 200
    outbox_relay_poll_ms: int = 500
    outbox_relay_processing_timeout_seconds: int = 60
    outbox_relay_max_backoff_seconds: int = 300
    outbox_stream_prefix: str = "sf:rt:v1:stream"
    delivery_consumer_group: str = "delivery-workers"
    delivery_consumer_name: str = "delivery-worker-1"
    delivery_poll_block_ms: int = 2000
    delivery_batch_size: int = 100
    notification_consumer_group: str = "notification-workers"
    notification_consumer_name: str = "notification-worker-1"
    notification_poll_block_ms: int = 2000
    notification_batch_size: int = 100
    generation_consumer_group: str = "generation-workers"
    generation_consumer_name: str = "generation-worker-1"
    generation_poll_block_ms: int = 2000
    generation_batch_size: int = 10
    export_consumer_group: str = "export-workers"
    export_consumer_name: str = "export-worker-1"
    export_poll_block_ms: int = 2000
    export_batch_size: int = 20
    notification_max_attempts: int = 5
    notification_retry_base_seconds: int = 2
    notification_allow_mock_tokens: bool = False
    notification_provider_mode: str = "mock"
    notification_provider_timeout_seconds: int = 5
    notification_fcm_webhook_url: str = ""
    notification_apns_webhook_url: str = ""
    stream_maxlen_approx: int = 200000
    notification_pending_idle_ms: int = 30000
    delivery_pending_idle_ms: int = 30000
    delivery_recipient_dedupe_ttl_seconds: int = 86400
    prompt_abuse_policy_mode: str = "log-only"  # block | challenge | log-only
    prompt_abuse_score_block_threshold: int = 80
    prompt_abuse_score_challenge_threshold: int = 50

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
