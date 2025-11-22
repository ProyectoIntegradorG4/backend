import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from app.routes.clientes import (
    get_tipos_institucion,
    get_mis_clientes,
    get_gerente_nits,
    get_gerente_cliente_ids,
    get_cliente_detail
)
from app.models.cliente import ClienteListResponse, TiposInstitucionResponse, ClienteResponse


class TestRoutesUnit:
    """Tests unitarios para funciones de routes sin TestClient"""

    @pytest.mark.asyncio
    async def test_get_tipos_institucion_success(self):
        """Test: get_tipos_institucion retorna correctamente"""
        mock_db = Mock()
        mock_service = Mock()
        mock_service.get_tipos_institucion.return_value = TiposInstitucionResponse(
            tipos=["Hospital", "Clínica", "IPS"]
        )
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            result = await get_tipos_institucion(db=mock_db)
        
        assert result.tipos == ["Hospital", "Clínica", "IPS"]
        mock_service.get_tipos_institucion.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tipos_institucion_error(self):
        """Test: get_tipos_institucion maneja errores"""
        mock_db = Mock()
        mock_service = Mock()
        mock_service.get_tipos_institucion.side_effect = Exception("Error")
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_tipos_institucion(db=mock_db)
        
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_mis_clientes_sin_gerente_id(self):
        """Test: get_mis_clientes sin gerente_id usa get_clientes_simple"""
        mock_db = Mock()
        mock_service = Mock()
        mock_service.get_clientes_simple.return_value = ClienteListResponse(
            total=0,
            page=1,
            limit=50,
            clientes=[]
        )
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            result = await get_mis_clientes(
                gerente_id=None,
                pais=None,
                tipo_institucion=None,
                search=None,
                page=1,
                limit=50,
                activo=True,
                db=mock_db
            )
        
        mock_service.get_clientes_simple.assert_called_once()
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_get_mis_clientes_con_gerente_id(self):
        """Test: get_mis_clientes con gerente_id usa get_clientes_asignados_a_gerente"""
        mock_db = Mock()
        mock_service = Mock()
        mock_service.get_gerente_pais.return_value = "Colombia"
        mock_service.get_clientes_asignados_a_gerente.return_value = ClienteListResponse(
            total=1,
            page=1,
            limit=50,
            clientes=[]
        )
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            result = await get_mis_clientes(
                gerente_id=1,
                pais=None,
                tipo_institucion=None,
                search=None,
                page=1,
                limit=50,
                activo=True,
                db=mock_db
            )
        
        mock_service.get_gerente_pais.assert_called_once_with(1)
        mock_service.get_clientes_asignados_a_gerente.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_mis_clientes_gerente_no_encontrado(self):
        """Test: get_mis_clientes con gerente_id sin país retorna 404"""
        mock_db = Mock()
        mock_service = Mock()
        mock_service.get_gerente_pais.return_value = None
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_mis_clientes(
                    gerente_id=999,
                    pais=None,
                    tipo_institucion=None,
                    search=None,
                    page=1,
                    limit=50,
                    activo=True,
                    db=mock_db
                )
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_mis_clientes_error(self):
        """Test: get_mis_clientes maneja errores"""
        mock_db = Mock()
        mock_service = Mock()
        mock_service.get_clientes_simple.side_effect = Exception("Error")
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_mis_clientes(
                    gerente_id=None,
                    pais=None,
                    tipo_institucion=None,
                    search=None,
                    page=1,
                    limit=50,
                    activo=True,
                    db=mock_db
                )
        
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_gerente_nits_success(self):
        """Test: get_gerente_nits retorna correctamente"""
        mock_db = Mock()
        mock_service = Mock()
        mock_service.get_gerente_nits.return_value = ["800111111-1", "800222222-2"]
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            result = await get_gerente_nits(gerente_id=1, db=mock_db)
        
        assert result["gerente_id"] == 1
        assert len(result["nits"]) == 2
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_get_gerente_nits_error(self):
        """Test: get_gerente_nits maneja errores"""
        mock_db = Mock()
        mock_service = Mock()
        mock_service.get_gerente_nits.side_effect = Exception("Error")
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_gerente_nits(gerente_id=1, db=mock_db)
        
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_gerente_cliente_ids_success(self):
        """Test: get_gerente_cliente_ids retorna correctamente"""
        mock_db = Mock()
        mock_service = Mock()
        mock_service.get_gerente_cliente_ids.return_value = [1, 2, 3]
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            result = await get_gerente_cliente_ids(gerente_id=1, db=mock_db)
        
        assert result["gerente_id"] == 1
        assert len(result["cliente_ids"]) == 3
        assert result["total"] == 3

    @pytest.mark.asyncio
    async def test_get_gerente_cliente_ids_error(self):
        """Test: get_gerente_cliente_ids maneja errores"""
        mock_db = Mock()
        mock_service = Mock()
        mock_service.get_gerente_cliente_ids.side_effect = Exception("Error")
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_gerente_cliente_ids(gerente_id=1, db=mock_db)
        
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_cliente_detail_success(self):
        """Test: get_cliente_detail retorna correctamente"""
        mock_db = Mock()
        mock_service = Mock()
        mock_cliente = Mock()
        mock_cliente.cliente_id = 1
        mock_cliente.nombre_comercial = "Test"
        mock_service.get_cliente_detail_simple.return_value = mock_cliente
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            result = await get_cliente_detail(cliente_id=1, db=mock_db)
        
        assert result.cliente_id == 1

    @pytest.mark.asyncio
    async def test_get_cliente_detail_error(self):
        """Test: get_cliente_detail maneja errores"""
        mock_db = Mock()
        mock_service = Mock()
        mock_service.get_cliente_detail_simple.side_effect = Exception("Error")
        
        with patch('app.routes.clientes.ClienteService', return_value=mock_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_cliente_detail(cliente_id=1, db=mock_db)
        
        assert exc_info.value.status_code == 500

