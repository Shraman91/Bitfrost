import os
from typing import Optional

def _load_env_file():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env_file()

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore
    from pydantic import Field  # type: ignore

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

        bifrost_url: str = Field(default="http://localhost:8080")
        bifrost_setup_token: Optional[str] = Field(default="agentarena-setup-token-secret")
        bifrost_encryption_key: Optional[str] = Field(default="bifrost-secret-encryption-key-32")
        arena_api_url: str = Field(default="http://localhost:8000")
        openai_api_key: Optional[str] = Field(default=None)
        anthropic_api_key: Optional[str] = Field(default=None)
        gemini_api_key: Optional[str] = Field(default=None)
        groq_api_key: Optional[str] = Field(default=None)
        firebase_project_id: str = Field(default="agentarena-benchmark")
        firebase_service_account_json: Optional[str] = Field(default=None)
        firebase_service_account_path: Optional[str] = Field(default=None)
        firestore_emulator_host: Optional[str] = Field(default=None)
        benchmark_concurrency: int = Field(default=3)
        default_run_timeout_seconds: int = Field(default=30)
        max_calls_per_run: int = Field(default=15)
        max_tokens_per_run: int = Field(default=60000)

    settings = Settings()

except ImportError:
    # Pure Python zero-dependency fallback for bare environments
    class FallbackSettings:
        def __init__(self):
            self.bifrost_url = os.environ.get("BIFROST_URL", "http://localhost:8080")
            self.arena_api_url = os.environ.get("ARENA_API_URL", "http://localhost:8000")
            self.openai_api_key = os.environ.get("OPENAI_API_KEY")
            self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
            self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
            self.groq_api_key = os.environ.get("GROQ_API_KEY")
            self.firebase_project_id = os.environ.get("FIREBASE_PROJECT_ID", "agentarena-benchmark")
            self.firebase_service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
            self.firebase_service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
            self.firestore_emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
            self.benchmark_concurrency = int(os.environ.get("BENCHMARK_CONCURRENCY", 3))
            self.default_run_timeout_seconds = int(os.environ.get("DEFAULT_RUN_TIMEOUT_SECONDS", 30))
            self.max_calls_per_run = int(os.environ.get("MAX_CALLS_PER_RUN", 15))
            self.max_tokens_per_run = int(os.environ.get("MAX_TOKENS_PER_RUN", 60000))

    settings = FallbackSettings()
