from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AlloyForge"
    api_prefix: str = "/api/v1"
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    artifact_dir: Path = Path("runtime/artifacts")
    default_candidates: int = 32
    max_candidates: int = 128
    ppo_learning_rate: float = 3e-4
    ppo_clip: float = 0.2
    random_seed: int = 42
    model_config = SettingsConfigDict(env_prefix="ALLOY_", env_file=".env", extra="ignore")


settings = Settings()

