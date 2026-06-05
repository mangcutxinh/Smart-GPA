"""
SmartGPA – Application Configuration
Load settings từ biến môi trường hoặc file .env
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # JWT
    SECRET_KEY: str = "smartgpa-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Databricks (optional – để trống khi dùng fake_db)
    DATABRICKS_HOST: str = ""
    DATABRICKS_SERVER_HOSTNAME: str = ""
    DATABRICKS_HTTP_PATH: str = ""
    DATABRICKS_TOKEN: str = ""
    DATABRICKS_CATALOG: str = "workspace"
    DATABRICKS_SCHEMA: str = "smartgpa_db"
    DATABRICKS_GOLD_TABLE: str = "gold_du_bao_diem_cuoi_ky"
    DATABRICKS_JOB_ID: str = ""
    DATABRICKS_UPLOAD_DIR: str = "/Shared/smartgpa_uploads"
    DATABRICKS_JOB_TIMEOUT_SECONDS: int = 300

    # Databricks MLflow (optional – để trống khi dùng fake_db)
    DATABRICKS_ML_SERVER_HOSTNAME: str = ""
    DATABRICKS_ML_HTTP_PATH: str = ""
    DATABRICKS_ML_TOKEN: str = ""
    DATABRICKS_ML_ENDPOINT_NAME: str = "subject_warning_endpoint"

    # Email SMTP (required for real OTP delivery)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "SmartGPA"
    SMTP_USE_TLS: bool = True

    # App
    APP_NAME: str = "SmartGPA API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    class Config:
        env_file = (".env", "backend/.env")
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
