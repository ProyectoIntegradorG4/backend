"""
Tests para app/config.py
Cubre la configuración usando Pydantic Settings
"""

import pytest
import os
from unittest.mock import patch
import warnings

from app.config import Settings, Environment


class TestEnvironmentEnum:
    """Tests para el enum Environment"""
    
    def test_environment_values(self):
        """Test que los valores del enum están correctos"""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"
    
    def test_environment_membership(self):
        """Test que se pueden comparar environments"""
        env = Environment.DEVELOPMENT
        assert env == Environment.DEVELOPMENT
        assert env != Environment.PRODUCTION


class TestSettingsDefaults:
    """Tests para valores por defecto de Settings"""
    
    def test_default_environment(self):
        """Test ambiente por defecto es development"""
        settings = Settings()
        assert settings.environment == Environment.DEVELOPMENT
    
    def test_default_database_config(self):
        """Test configuración de BD por defecto"""
        settings = Settings()
        assert settings.pedidos_db_name == "pedidos_db"
        assert settings.pedidos_db_user == "pedidos_service"
        assert settings.pedidos_db_password == "pedidos_password"
        assert settings.postgres_host == "postgres-db"
        assert settings.postgres_port == "5432"
    
    def test_default_pool_config(self):
        """Test configuración de pool de conexiones"""
        settings = Settings()
        assert settings.db_pool_size == 10
        assert settings.db_max_overflow == 20
        assert settings.db_pool_recycle == 3600
    
    def test_default_service_config(self):
        """Test configuración del servicio"""
        settings = Settings()
        assert settings.pedidos_service_port == 8007
        assert settings.pedidos_service_host == "0.0.0.0"
        assert settings.workers is None
    
    def test_default_external_services(self):
        """Test URLs de servicios externos"""
        settings = Settings()
        assert settings.product_service_url == "http://product-service:8005"
        assert settings.cliente_service_url == "http://cliente-service:8003"
        assert settings.nit_validation_service_url == "http://nit-validation-service:8002"
    
    def test_default_timeouts(self):
        """Test timeouts por defecto"""
        settings = Settings()
        assert settings.request_timeout == 10.0
        assert settings.health_check_timeout == 5.0
    
    def test_default_logging(self):
        """Test configuración de logging"""
        settings = Settings()
        assert settings.log_level == "INFO"
        assert settings.log_format == "json"
    
    def test_default_cors(self):
        """Test configuración de CORS"""
        settings = Settings()
        assert settings.cors_origins == ["*"]
        assert settings.cors_allow_credentials is True
        assert settings.cors_allow_methods == ["GET", "POST", "PUT", "DELETE", "PATCH"]
        assert settings.cors_allow_headers == ["*"]
        assert settings.cors_max_age == 3600
    
    def test_default_security(self):
        """Test configuración de seguridad"""
        settings = Settings()
        assert settings.rate_limit_per_minute == 60
    
    def test_default_feature_flags(self):
        """Test feature flags"""
        settings = Settings()
        assert settings.enable_retry_logic is True
        assert settings.enable_circuit_breaker is False
        assert settings.enable_metrics is False


class TestSettingsDatabaseUrl:
    """Tests para la propiedad database_url"""
    
    def test_database_url_from_pedidos_database_url(self):
        """Test que usa PEDIDOS_DATABASE_URL si está definida"""
        custom_url = "postgresql://custom:password@custom-host:5432/custom_db"
        settings = Settings(pedidos_database_url=custom_url)
        assert settings.database_url == custom_url
    
    def test_database_url_from_env_database_url(self):
        """Test que usa DATABASE_URL si PEDIDOS_DATABASE_URL no está"""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://env:pass@envhost:5432/envdb"}):
            settings = Settings()
            assert settings.database_url == "postgresql://env:pass@envhost:5432/envdb"
    
    def test_database_url_constructed(self):
        """Test que construye URL desde componentes"""
        settings = Settings(
            pedidos_db_user="test_user",
            pedidos_db_password="test_pass",
            postgres_host="test-host",
            postgres_port="5433",
            pedidos_db_name="test_db"
        )
        
        with patch.dict(os.environ, {}, clear=True):
            expected = "postgresql+psycopg://test_user:test_pass@test-host:5433/test_db"
            assert settings.database_url == expected
    
    def test_database_url_default_construction(self):
        """Test construcción con valores por defecto"""
        settings = Settings()
        with patch.dict(os.environ, {}, clear=True):
            url = settings.database_url
            assert "postgresql+psycopg://" in url
            assert "pedidos_service" in url
            assert "pedidos_password" in url
            assert "postgres-db" in url
            assert "5432" in url
            assert "pedidos_db" in url


class TestSettingsEnvironmentProperties:
    """Tests para propiedades de ambiente"""
    
    def test_is_production_true(self):
        """Test is_production cuando environment es PRODUCTION"""
        settings = Settings(environment=Environment.PRODUCTION)
        assert settings.is_production is True
        assert settings.is_development is False
        assert settings.is_staging is False
    
    def test_is_development_true(self):
        """Test is_development cuando environment es DEVELOPMENT"""
        settings = Settings(environment=Environment.DEVELOPMENT)
        assert settings.is_development is True
        assert settings.is_production is False
        assert settings.is_staging is False
    
    def test_is_staging_true(self):
        """Test is_staging cuando environment es STAGING"""
        settings = Settings(environment=Environment.STAGING)
        assert settings.is_staging is True
        assert settings.is_production is False
        assert settings.is_development is False


class TestSettingsGetCorsOrigins:
    """Tests para el método get_cors_origins"""
    
    def test_get_cors_origins_development(self):
        """Test CORS en development con wildcard"""
        settings = Settings(
            environment=Environment.DEVELOPMENT,
            cors_origins=["*"]
        )
        
        origins = settings.get_cors_origins()
        assert origins == ["*"]
    
    def test_get_cors_origins_production_with_specific_domains(self):
        """Test CORS en producción con dominios específicos"""
        settings = Settings(
            environment=Environment.PRODUCTION,
            cors_origins=["https://example.com", "https://app.example.com"]
        )
        
        origins = settings.get_cors_origins()
        assert origins == ["https://example.com", "https://app.example.com"]
    
    def test_get_cors_origins_production_with_wildcard_warning(self):
        """Test que lanza warning en producción con wildcard"""
        settings = Settings(
            environment=Environment.PRODUCTION,
            cors_origins=["*"]
        )
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            origins = settings.get_cors_origins()
            
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "CORS configurado con '*' en producción" in str(w[0].message)
            assert origins == ["*"]


class TestSettingsFromEnvironmentVariables:
    """Tests para cargar configuración desde variables de entorno"""
    
    def test_load_from_env_with_prefix(self):
        """Test cargar con prefijo PEDIDOS_"""
        with patch.dict(os.environ, {
            "PEDIDOS_ENVIRONMENT": "production",
            "PEDIDOS_PEDIDOS_SERVICE_PORT": "9000",
            "PEDIDOS_LOG_LEVEL": "DEBUG"
        }):
            settings = Settings()
            assert settings.environment == Environment.PRODUCTION
            assert settings.pedidos_service_port == 9000
            assert settings.log_level == "DEBUG"
    
    def test_load_database_config_from_env(self):
        """Test cargar configuración de BD desde env"""
        with patch.dict(os.environ, {
            "PEDIDOS_PEDIDOS_DB_NAME": "custom_db",
            "PEDIDOS_PEDIDOS_DB_USER": "custom_user",
            "PEDIDOS_POSTGRES_HOST": "custom-host"
        }):
            settings = Settings()
            assert settings.pedidos_db_name == "custom_db"
            assert settings.pedidos_db_user == "custom_user"
            assert settings.postgres_host == "custom-host"
    
    def test_load_service_urls_from_env(self):
        """Test cargar URLs de servicios desde env"""
        with patch.dict(os.environ, {
            "PEDIDOS_PRODUCT_SERVICE_URL": "http://custom-product:8080",
            "PEDIDOS_CLIENTE_SERVICE_URL": "http://custom-cliente:8080"
        }):
            settings = Settings()
            assert settings.product_service_url == "http://custom-product:8080"
            assert settings.cliente_service_url == "http://custom-cliente:8080"
    
    def test_load_feature_flags_from_env(self):
        """Test cargar feature flags desde env"""
        with patch.dict(os.environ, {
            "PEDIDOS_ENABLE_RETRY_LOGIC": "false",
            "PEDIDOS_ENABLE_CIRCUIT_BREAKER": "true",
            "PEDIDOS_ENABLE_METRICS": "true"
        }):
            settings = Settings()
            assert settings.enable_retry_logic is False
            assert settings.enable_circuit_breaker is True
            assert settings.enable_metrics is True


class TestSettingsValidation:
    """Tests para validación de configuración"""
    
    def test_invalid_environment_value(self):
        """Test que falla con environment inválido"""
        with pytest.raises(ValueError):
            Settings(environment="invalid_env")
    
    def test_port_as_string(self):
        """Test que convierte puerto string a int"""
        settings = Settings(pedidos_service_port="8080")
        assert settings.pedidos_service_port == 8080
        assert isinstance(settings.pedidos_service_port, int)
    
    def test_timeout_as_string(self):
        """Test que convierte timeout string a float"""
        settings = Settings(request_timeout="15.5")
        assert settings.request_timeout == 15.5
        assert isinstance(settings.request_timeout, float)
    
    def test_bool_from_string(self):
        """Test que convierte string a bool"""
        settings = Settings(enable_retry_logic="true")
        assert settings.enable_retry_logic is True
        
        settings = Settings(enable_retry_logic="false")
        assert settings.enable_retry_logic is False


class TestSettingsIntegration:
    """Tests de integración para configuración completa"""
    
    def test_production_configuration(self):
        """Test configuración completa para producción"""
        settings = Settings(
            environment=Environment.PRODUCTION,
            pedidos_service_port=8000,
            cors_origins=["https://api.example.com"],
            log_level="WARNING",
            enable_metrics=True,
            rate_limit_per_minute=100
        )
        
        assert settings.is_production is True
        assert settings.pedidos_service_port == 8000
        assert "*" not in settings.cors_origins
        assert settings.log_level == "WARNING"
        assert settings.enable_metrics is True
    
    def test_development_configuration(self):
        """Test configuración completa para desarrollo"""
        settings = Settings(
            environment=Environment.DEVELOPMENT,
            log_level="DEBUG",
            cors_origins=["*"],
            enable_retry_logic=False
        )
        
        assert settings.is_development is True
        assert settings.log_level == "DEBUG"
        assert settings.cors_origins == ["*"]
