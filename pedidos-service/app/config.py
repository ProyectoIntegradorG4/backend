"""
Configuración centralizada del servicio usando Pydantic Settings.

Cumple con el Factor III de 12-Factor App: Config
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from enum import Enum
import os


class Environment(str, Enum):
    """Ambientes disponibles"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Configuración del servicio pedidos-service.
    
    Todas las configuraciones se pueden sobrescribir mediante variables de entorno.
    Las variables de entorno deben usar el prefijo PEDIDOS_ o el nombre exacto del campo.
    """
    
    # ====================
    # Ambiente
    # ====================
    environment: Environment = Environment.DEVELOPMENT
    
    # ====================
    # Base de Datos
    # ====================
    pedidos_db_name: str = "pedidos_db"
    pedidos_db_user: str = "pedidos_service"
    pedidos_db_password: str = "pedidos_password"
    postgres_host: str = "postgres-db"
    postgres_port: str = "5432"
    pedidos_database_url: Optional[str] = None
    
    # Pool de conexiones
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600  # 1 hora
    
    # ====================
    # Servicio
    # ====================
    pedidos_service_port: int = 8007
    pedidos_service_host: str = "0.0.0.0"
    workers: Optional[int] = None  # None = calcular automáticamente
    
    # ====================
    # Servicios Externos
    # ====================
    product_service_url: str = "http://product-service:8005"
    cliente_service_url: str = "http://cliente-service:8003"
    nit_validation_service_url: str = "http://nit-validation-service:8002"
    
    # Timeouts
    request_timeout: float = 10.0
    health_check_timeout: float = 5.0
    
    # ====================
    # Logging
    # ====================
    log_level: str = "INFO"
    log_format: str = "json"  # "json" o "text"
    
    # ====================
    # CORS
    # ====================
    cors_origins: List[str] = ["*"]  # En producción, especificar dominios exactos
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    cors_allow_headers: List[str] = ["*"]
    cors_max_age: int = 3600
    
    # ====================
    # Seguridad
    # ====================
    # Rate limiting (requests por minuto)
    rate_limit_per_minute: int = 60
    
    # ====================
    # Features Flags
    # ====================
    enable_retry_logic: bool = True
    enable_circuit_breaker: bool = False  # Requiere implementación adicional
    enable_metrics: bool = False  # Requiere implementación adicional
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Permitir variables de entorno con prefijo PEDIDOS_
        env_prefix = "PEDIDOS_"
    
    @property
    def database_url(self) -> str:
        """
        Construye la URL de la base de datos si no está definida.
        
        Prioridad:
        1. PEDIDOS_DATABASE_URL
        2. DATABASE_URL
        3. Construida desde componentes individuales
        """
        if self.pedidos_database_url:
            return self.pedidos_database_url
        
        # Intentar obtener de DATABASE_URL (sin prefijo)
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url
        
        # Construir desde componentes
        return (
            f"postgresql+psycopg://{self.pedidos_db_user}:"
            f"{self.pedidos_db_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.pedidos_db_name}"
        )
    
    @property
    def is_production(self) -> bool:
        """Verifica si está en ambiente de producción"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Verifica si está en ambiente de desarrollo"""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_staging(self) -> bool:
        """Verifica si está en ambiente de staging"""
        return self.environment == Environment.STAGING
    
    def get_cors_origins(self) -> List[str]:
        """
        Retorna los orígenes CORS permitidos.
        En producción, si es ["*"], debería lanzar un warning.
        """
        if self.is_production and "*" in self.cors_origins:
            import warnings
            warnings.warn(
                "CORS configurado con '*' en producción. "
                "Esto es un riesgo de seguridad. Especifique dominios exactos.",
                UserWarning
            )
        return self.cors_origins


# Instancia global de configuración
settings = Settings()

