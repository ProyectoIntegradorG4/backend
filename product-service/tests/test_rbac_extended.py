"""
Tests extendidos para app/service/rbac.py
Cubre validación JWT, extracción de roles y control de acceso
"""
import pytest
from fastapi import HTTPException, Request, Header
from unittest.mock import Mock, MagicMock, patch
from app.service.rbac import (
    decode_jwt_token,
    require_auth_token,
    require_role_admincompras_header,
    require_role_admincompras,
    require_role_admin_ventas,
    ALLOWED_ROLE,
    ALLOWED_ROLE_VENTAS
)


class TestDecodeJwtToken:
    """Tests para decode_jwt_token"""
    
    def test_decode_token_modo_desarrollo(self):
        """En modo desarrollo retorna payload simulado"""
        payload = decode_jwt_token("cualquier-token")
        
        assert "sub" in payload
        assert "email" in payload
        assert "roles" in payload
        assert ALLOWED_ROLE in payload["roles"]
        assert ALLOWED_ROLE_VENTAS in payload["roles"]


class TestRequireAuthToken:
    """Tests para require_auth_token"""
    
    def test_require_auth_token_presente(self):
        """Token presente en header"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer test-token"
        
        # No debe lanzar excepción
        result = require_auth_token(mock_request)
        assert result is None
    
    def test_require_auth_token_ausente(self):
        """Token ausente lanza 401"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            require_auth_token(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Authorization" in exc_info.value.detail
    
    def test_require_auth_token_formato_invalido(self):
        """Token sin Bearer lanza 401"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "InvalidFormat token"
        
        with pytest.raises(HTTPException) as exc_info:
            require_auth_token(mock_request)
        
        assert exc_info.value.status_code == 401


class TestRequireRoleAdminComprasHeader:
    """Tests para require_role_admincompras_header"""
    
    def test_auth_header_valido_con_rol(self):
        """Header válido con rol correcto"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid-token"
        
        result = require_role_admincompras_header(
            mock_request, 
            x_user_role=ALLOWED_ROLE
        )
        
        assert "roles" in result
        assert ALLOWED_ROLE in result["roles"]
        assert "user_id" in result
        assert "email" in result
    
    def test_auth_header_sin_authorization(self):
        """Sin Authorization header lanza 401"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            require_role_admincompras_header(mock_request, x_user_role=ALLOWED_ROLE)
        
        assert exc_info.value.status_code == 401
        assert "Authorization" in exc_info.value.detail
    
    def test_auth_header_formato_invalido(self):
        """Authorization con formato inválido lanza 401"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "InvalidFormat"
        
        with pytest.raises(HTTPException) as exc_info:
            require_role_admincompras_header(mock_request, x_user_role=ALLOWED_ROLE)
        
        assert exc_info.value.status_code == 401
        assert "inválido" in exc_info.value.detail.lower()
    
    def test_auth_header_rol_invalido(self):
        """Token válido pero rol incorrecto lanza 403"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid-token"
        
        # Mock decode_jwt_token para retornar roles sin el permitido
        with patch('app.service.rbac.decode_jwt_token') as mock_decode:
            mock_decode.return_value = {
                "sub": "user-123",
                "email": "user@example.com",
                "roles": ["Rol Incorrecto"]
            }
            
            with pytest.raises(HTTPException) as exc_info:
                require_role_admincompras_header(mock_request, x_user_role="Rol Incorrecto")
            
            assert exc_info.value.status_code == 403
            assert "No autorizado" in exc_info.value.detail


class TestRequireRoleAdminCompras:
    """Tests para require_role_admincompras"""
    
    def test_admincompras_con_request_valido(self):
        """Request válido con rol correcto"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid-token"
        
        result = require_role_admincompras(mock_request, x_user_role=None)
        
        assert "roles" in result
        assert ALLOWED_ROLE in result["roles"]
    
    def test_admincompras_sin_request_con_header_valido(self):
        """Sin request pero con x_user_role válido (fallback para tests)"""
        result = require_role_admincompras(
            request=None, 
            x_user_role=ALLOWED_ROLE
        )
        
        assert "roles" in result
        assert ALLOWED_ROLE in result["roles"]
    
    def test_admincompras_sin_request_rol_invalido(self):
        """Sin request y x_user_role inválido lanza 403"""
        with pytest.raises(HTTPException) as exc_info:
            require_role_admincompras(request=None, x_user_role="Rol Incorrecto")
        
        assert exc_info.value.status_code == 403
        assert "Acceso denegado" in exc_info.value.detail
    
    def test_admincompras_sin_authorization_header(self):
        """Request sin Authorization lanza 401"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            require_role_admincompras(mock_request, x_user_role=None)
        
        assert exc_info.value.status_code == 401
    
    def test_admincompras_token_sin_bearer(self):
        """Token sin Bearer lanza 401"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "TokenSinBearer"
        
        with pytest.raises(HTTPException) as exc_info:
            require_role_admincompras(mock_request, x_user_role=None)
        
        assert exc_info.value.status_code == 401
    
    def test_admincompras_rol_no_permitido(self):
        """Token válido pero rol no permitido lanza 403"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid-token"
        
        with patch('app.service.rbac.decode_jwt_token') as mock_decode:
            mock_decode.return_value = {
                "sub": "user-123",
                "email": "user@example.com",
                "roles": ["Usuario Normal"]
            }
            
            with pytest.raises(HTTPException) as exc_info:
                require_role_admincompras(mock_request, x_user_role=None)
            
            assert exc_info.value.status_code == 403


class TestRequireRoleAdminVentas:
    """Tests para require_role_admin_ventas"""
    
    def test_admin_ventas_con_rol_valido(self):
        """Request válido con rol de ventas"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid-token"
        
        result = require_role_admin_ventas(mock_request, x_user_role=None)
        
        assert "roles" in result
        assert ALLOWED_ROLE_VENTAS in result["roles"]
    
    def test_admin_ventas_sin_request_header_valido(self):
        """Sin request pero con x_user_role de ventas"""
        result = require_role_admin_ventas(
            request=None,
            x_user_role=ALLOWED_ROLE_VENTAS
        )
        
        assert "roles" in result
        assert ALLOWED_ROLE_VENTAS in result["roles"]
    
    def test_admin_ventas_sin_request_rol_invalido(self):
        """Sin request y rol incorrecto lanza 403"""
        with pytest.raises(HTTPException) as exc_info:
            require_role_admin_ventas(request=None, x_user_role="Rol Incorrecto")
        
        assert exc_info.value.status_code == 403
        assert "Administrador de Ventas" in exc_info.value.detail
    
    def test_admin_ventas_sin_authorization(self):
        """Request sin Authorization lanza 401"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            require_role_admin_ventas(mock_request, x_user_role=None)
        
        assert exc_info.value.status_code == 401
    
    def test_admin_ventas_token_invalido(self):
        """Token sin formato Bearer lanza 401"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Invalid token"
        
        with pytest.raises(HTTPException) as exc_info:
            require_role_admin_ventas(mock_request, x_user_role=None)
        
        assert exc_info.value.status_code == 401
    
    def test_admin_ventas_rol_no_permitido(self):
        """Token válido pero sin rol de ventas lanza 403"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid-token"
        
        with patch('app.service.rbac.decode_jwt_token') as mock_decode:
            mock_decode.return_value = {
                "sub": "user-123",
                "email": "user@example.com",
                "roles": ["Administrador de Compras"]  # Rol incorrecto
            }
            
            with pytest.raises(HTTPException) as exc_info:
                require_role_admin_ventas(mock_request, x_user_role=None)
            
            assert exc_info.value.status_code == 403
            assert "Administrador de Ventas" in exc_info.value.detail
    
    def test_admin_ventas_extraccion_datos_usuario(self):
        """Verificar extracción correcta de datos del usuario"""
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid-token"
        
        with patch('app.service.rbac.decode_jwt_token') as mock_decode:
            mock_decode.return_value = {
                "sub": "user-456",
                "email": "ventas@example.com",
                "roles": [ALLOWED_ROLE_VENTAS]
            }
            
            result = require_role_admin_ventas(mock_request, x_user_role=None)
            
            assert result["user_id"] == "user-456"
            assert result["email"] == "ventas@example.com"
            assert ALLOWED_ROLE_VENTAS in result["roles"]
