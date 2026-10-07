# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Configuración de Aplicación
#  Variables de entorno desde .env
# ═══════════════════════════════════════════════════════════

import os
from typing import List
from dotenv import load_dotenv

# Cargar .env
load_dotenv()


class Settings:
    """Configuración de la aplicación"""
    
    # ── APP ────────────────────────────────────────────────
    app_name: str = os.getenv("APP_NAME", "Emantix Pro API")
    app_version: str = os.getenv("APP_VERSION", "4.0.0")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # ── SEGURIDAD ──────────────────────────────────────────
    secret_key: str = os.getenv("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # ── CORS ───────────────────────────────────────────────
    cors_origins_str: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    cors_origins: List[str] = cors_origins_str.split(",")
    
    # ── BASE DE DATOS ──────────────────────────────────────
    db_server: str = os.getenv("DB_SERVER", "localhost")
    db_name: str = os.getenv("DB_NAME", "EmantixDB")
    db_user: str = os.getenv("DB_USER", "sa")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_use_windows_auth: bool = os.getenv("DB_USE_WINDOWS_AUTH", "True").lower() == "true"
    
    # Pool de conexiones
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "50"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    db_pool_recycle: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # Reciclar cada 30 min
    db_echo: bool = os.getenv("DB_ECHO", "False").lower() == "true"
    
    # ── SMTP (EMAIL) ───────────────────────────────────────
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "noreply@emantix.com")
    
    # ── AUTENTICACIÓN ──────────────────────────────────────
    max_login_attempts: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    lockout_seconds: int = int(os.getenv("LOCKOUT_SECONDS", "300"))
    password_min_length: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    password_require_uppercase: bool = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "True").lower() == "true"
    password_require_number: bool = os.getenv("PASSWORD_REQUIRE_NUMBER", "True").lower() == "true"
    password_require_special: bool = os.getenv("PASSWORD_REQUIRE_SPECIAL", "False").lower() == "true"
    
    # ── ARCHIVOS ───────────────────────────────────────────
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    allowed_file_extensions: List[str] = os.getenv("ALLOWED_FILE_EXTENSIONS", "pdf,xlsx,xls,csv").split(",")
    
    # ── PAGINACIÓN ─────────────────────────────────────────
    default_page_size: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    max_page_size: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
    
    # ── LOGGING ────────────────────────────────────────────
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/emantix.log")
    
    @property
    def database_url(self) -> str:
        """Construir URL de conexión a SQL Server"""
        if self.db_use_windows_auth:
            return (
                f"mssql+pyodbc://@{self.db_server}/{self.db_name}"
                f"?driver=ODBC+Driver+17+for+SQL+Server"
                f"&trusted_connection=yes"
                f"&TrustServerCertificate=yes"
            )
        else:
            return (
                f"mssql+pyodbc://{self.db_user}:{self.db_password}@{self.db_server}/{self.db_name}"
                f"?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
            )
    
    def validate_settings(self) -> None:
        """Validar configuración crítica en startup"""
        if len(self.secret_key) < 32:
            raise ValueError("❌ SECRET_KEY debe tener al menos 32 caracteres")
        
        if self.debug and not os.getenv("ALLOW_DEBUG"):
            raise ValueError("❌ DEBUG=True en producción es peligroso. Usar ALLOW_DEBUG=true")
        
        if not self.smtp_user or not self.smtp_password:
            print("⚠️  SMTP_USER o SMTP_PASSWORD vacíos. Email deshabilitado.")
        
        print("✅ Configuración validada correctamente")


# Instancia global de settings
settings = Settings()
