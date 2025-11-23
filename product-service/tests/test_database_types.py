"""
Tests para app/database/types.py
Cubre el tipo GUID portable para UUID
"""
import pytest
import uuid
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import declarative_base, Session
from app.database.types import GUID


Base = declarative_base()


class ModeloTest(Base):
    """Modelo de prueba con campo GUID"""
    __tablename__ = "test_guid"
    
    id = Column(GUID, primary_key=True)
    nombre = Column(String(100))


class TestGUIDType:
    """Tests para el tipo GUID"""
    
    @pytest.fixture
    def sqlite_engine(self):
        """Engine SQLite para tests"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine
    
    def test_guid_proceso_bind_param_uuid(self, sqlite_engine):
        """Convertir UUID a string al guardar"""
        guid_type = GUID()
        test_uuid = uuid.uuid4()
        
        # Simular bind_param
        result = guid_type.process_bind_param(test_uuid, sqlite_engine.dialect)
        
        assert isinstance(result, str)
        assert result == str(test_uuid)
    
    def test_guid_proceso_bind_param_string(self, sqlite_engine):
        """Convertir string a UUID normalizado al guardar"""
        guid_type = GUID()
        test_uuid_str = str(uuid.uuid4())
        
        result = guid_type.process_bind_param(test_uuid_str, sqlite_engine.dialect)
        
        assert isinstance(result, str)
        # Debe normalizar el formato
        assert uuid.UUID(result)  # Válido como UUID
    
    def test_guid_proceso_bind_param_none(self, sqlite_engine):
        """Manejar None correctamente"""
        guid_type = GUID()
        
        result = guid_type.process_bind_param(None, sqlite_engine.dialect)
        
        assert result is None
    
    def test_guid_proceso_result_value_string(self, sqlite_engine):
        """Convertir string de DB a UUID al leer"""
        guid_type = GUID()
        test_uuid = uuid.uuid4()
        test_uuid_str = str(test_uuid)
        
        result = guid_type.process_result_value(test_uuid_str, sqlite_engine.dialect)
        
        assert isinstance(result, uuid.UUID)
        assert result == test_uuid
    
    def test_guid_proceso_result_value_none(self, sqlite_engine):
        """Manejar None al leer"""
        guid_type = GUID()
        
        result = guid_type.process_result_value(None, sqlite_engine.dialect)
        
        assert result is None
    
    def test_guid_load_dialect_impl_sqlite(self, sqlite_engine):
        """Verificar que en SQLite usa CHAR(36)"""
        guid_type = GUID()
        
        impl = guid_type.load_dialect_impl(sqlite_engine.dialect)
        
        assert impl.length == 36
    
    def test_guid_integracion_insert_select(self, sqlite_engine):
        """Test de integración: insertar y leer con GUID"""
        session = Session(sqlite_engine)
        
        # Insertar registro con UUID
        test_uuid = uuid.uuid4()
        registro = ModeloTest(id=test_uuid, nombre="Test")
        session.add(registro)
        session.commit()
        
        # Leer registro
        resultado = session.query(ModeloTest).filter_by(id=test_uuid).first()
        
        assert resultado is not None
        assert isinstance(resultado.id, uuid.UUID)
        assert resultado.id == test_uuid
        assert resultado.nombre == "Test"
        
        session.close()
    
    def test_guid_integracion_insert_string(self, sqlite_engine):
        """Insertar con string UUID"""
        session = Session(sqlite_engine)
        
        test_uuid = uuid.uuid4()
        test_uuid_str = str(test_uuid)
        
        # Insertar con string
        registro = ModeloTest(id=test_uuid_str, nombre="Test String")
        session.add(registro)
        session.commit()
        
        # Leer
        resultado = session.query(ModeloTest).filter_by(id=test_uuid).first()
        
        assert resultado is not None
        assert isinstance(resultado.id, uuid.UUID)
        assert resultado.id == test_uuid
        
        session.close()
    
    def test_guid_cache_ok(self):
        """Verificar que cache_ok está habilitado"""
        guid_type = GUID()
        assert guid_type.cache_ok is True
    
    def test_guid_multiples_registros(self, sqlite_engine):
        """Insertar y consultar múltiples registros con GUID"""
        session = Session(sqlite_engine)
        
        # Crear varios registros
        uuids = [uuid.uuid4() for _ in range(5)]
        for i, test_uuid in enumerate(uuids):
            registro = ModeloTest(id=test_uuid, nombre=f"Test {i}")
            session.add(registro)
        
        session.commit()
        
        # Consultar todos
        resultados = session.query(ModeloTest).all()
        
        assert len(resultados) == 5
        assert all(isinstance(r.id, uuid.UUID) for r in resultados)
        assert set(r.id for r in resultados) == set(uuids)
        
        session.close()
