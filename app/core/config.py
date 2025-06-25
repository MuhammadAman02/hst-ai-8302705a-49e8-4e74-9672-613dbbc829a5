"""Configuration management for the fraud detection system"""

import os
from typing import Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "Irish Banking Fraud Detection System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "sqlite:///./fraud_detection.db"
    
    # ML Models
    MODEL_PATH: str = "./models"
    FRAUD_THRESHOLD: float = 0.7
    
    # External APIs
    CENTRAL_BANK_API_URL: Optional[str] = None
    CENTRAL_BANK_API_KEY: Optional[str] = None
    
    # Notification
    EMAIL_ENABLED: bool = False
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Compliance
    GDPR_RETENTION_DAYS: int = 2555  # 7 years as per Irish banking regulations
    AUDIT_LOG_ENABLED: bool = True
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()