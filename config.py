"""
Configuration settings for TrueFACE Backend
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_TITLE: str = "TrueFACE API"
    API_DESCRIPTION: str = "Real-time deepfake detection and authenticity scoring"
    API_VERSION: str = "1.0.0"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    RELOAD: bool = False
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = ["https://yourdomain.com"]  # Change for production
    ALLOWED_METHODS: List[str] = ["GET", "POST", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["Content-Type", "Authorization"]
    
    # Model Settings
    MODEL_DEVICE: str = "auto"  # "auto", "cpu", "cuda"
    VIDEO_MODEL_PATH: str = ""
    AUDIO_MODEL_PATH: str = ""
    
    # Processing Settings
    MAX_FRAME_SIZE: int = 1024 * 1024 * 5  # 5MB
    MAX_AUDIO_SIZE: int = 1024 * 1024 * 10  # 10MB
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_SESSIONS: int = 100
    
    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_MAX_CONNECTIONS: int = 50
    
    # Scoring Settings
    VIDEO_WEIGHT: float = 0.6
    AUDIO_WEIGHT: float = 0.4
    TEMPORAL_SMOOTHING_ALPHA: float = 0.3
    CONFIDENCE_THRESHOLD: float = 0.7
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security Settings
    API_KEY: str = ""
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    ENABLE_API_KEY_AUTH: bool = True
    MAX_CONNECTIONS_PER_IP: int = 3
    SECURE_HEADERS: bool = True
    
    # Cloud Deployment Settings
    CLOUD_PROVIDER: str = "render"  # "render", "railway", "gcp"
    DATABASE_URL: str = ""
    REDIS_URL: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Model configuration
MODEL_CONFIG = {
    "video": {
        "input_size": (224, 224),
        "channels": 3,
        "batch_size": 1,
        "confidence_threshold": 0.5
    },
    "audio": {
        "sample_rate": 16000,
        "n_mfcc": 13,
        "hop_length": 512,
        "n_fft": 2048,
        "confidence_threshold": 0.5
    }
}

# API Response templates
API_RESPONSES = {
    "analysis_success": {
        "session_id": "string",
        "timestamp": "string",
        "video_score": "float",
        "audio_score": "float", 
        "authenticity": "float",
        "confidence": "float"
    },
    "error": {
        "error": "string",
        "message": "string",
        "timestamp": "string"
    }
}

# WebSocket message types
WS_MESSAGE_TYPES = {
    "FRAME_DATA": "frame_data",
    "AUDIO_DATA": "audio_data", 
    "GET_SCORE": "get_score",
    "PING": "ping",
    "PONG": "pong",
    "ANALYSIS_RESULT": "analysis_result",
    "AUTH_SCORE": "auth_score",
    "ERROR": "error",
    "PERIODIC_UPDATE": "periodic_update"
}
