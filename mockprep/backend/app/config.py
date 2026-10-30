import os

class Settings:
    PROJECT_NAME: str = "MockPrep - AI Mock Interview Platform"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "mockprep_super_secret_jwt_key_2026_ietlucknow")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database Settings
    # Defaults to local SQLite for instant out-of-the-box run, supports PostgreSQL via DATABASE_URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mockprep.db")
    
    # AI Keys (Optional - Intelligent fallback rubric is built-in)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
