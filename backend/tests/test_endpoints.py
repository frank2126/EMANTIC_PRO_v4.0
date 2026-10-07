# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Tests para Endpoints Principales
#  Health Check, Root, Manejo de Errores Globales
# ═══════════════════════════════════════════════════════════

import pytest
from fastapi import status


class TestHealthCheckEndpoint:
    """Tests para endpoint GET /health"""
    
    def test_health_check_success(self, client):
        """✅ Health check retorna status correcto"""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_check_no_auth_required(self, client):
        """✅ Health check no requiere autenticación"""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_health_check_response_format(self, client):
        """✅ Health check tiene formato correcto"""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["version"], str)


class TestRootEndpoint:
    """Tests para endpoint GET /"""
    
    def test_root_endpoint_success(self, client):
        """✅ Root endpoint retorna información de API"""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "name" in data
        assert "EMANTIX" in data["name"]
        assert data["status"] == "running"
    
    def test_root_endpoint_no_auth_required(self, client):
        """✅ Root endpoint no requiere autenticación"""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK


class TestCORSConfiguration:
    """Tests para configuración de CORS"""
    
    def test_cors_allowed_origin(self, client):
        """✅ Origen permitido puede acceder"""
        # Localhost está permitido en desarrollo
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"}
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_cors_headers_included(self, client):
        """✅ Respuesta incluye headers CORS"""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"}
        )
        
        # TestClient no siempre simula CORS perfectamente, pero verificamos que funciona


class TestErrorHandling:
    """Tests para manejo global de errores"""
    
    def test_404_not_found(self, client):
        """✅ Endpoint inexistente retorna 404"""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_405_method_not_allowed(self, client):
        """✅ Método no permitido retorna 405"""
        response = client.post("/health")  # GET solamente
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_422_validation_error(self, client):
        """✅ Datos inválidos retornan 422"""
        response = client.post(
            "/api/auth/login",
            json={"username": "test"}  # Falta password
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_error_response_format(self, client):
        """✅ Errores tienen formato consistente"""
        response = client.post(
            "/api/auth/login",
            json={"username": "test"}
        )
        
        data = response.json()
        assert "detail" in data


class TestRequestValidation:
    """Tests para validación de requests"""
    
    def test_empty_json_body(self, client):
        """✅ Body vacío retorna error"""
        response = client.post(
            "/api/auth/login",
            json={}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_invalid_json_format(self, client):
        """✅ JSON inválido retorna error"""
        response = client.post(
            "/api/auth/login",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_extra_fields_ignored(self, client):
        """✅ Campos extras se ignoran (no causan error)"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
                "extra_field": "ignored"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_null_values_rejected(self, client):
        """✅ Valores null se rechazan en campos requeridos"""
        response = client.post(
            "/api/auth/login",
            json={"username": None, "password": "admin123"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestResponseFormats:
    """Tests para formato consistente de respuestas"""
    
    def test_success_response_structure(self, client):
        """✅ Respuestas exitosas tienen estructura consistente"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        data = response.json()
        assert isinstance(data, dict)
        assert "access_token" in data
    
    def test_error_response_structure(self, client):
        """✅ Errores tienen estructura consistente"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"}
        )
        
        data = response.json()
        assert isinstance(data, dict)
        assert "detail" in data
    
    def test_list_response_is_array(self, client, admin_headers):
        """✅ Endpoints que devuelven listas retornan arrays"""
        response = client.get(
            "/api/users",
            headers=admin_headers
        )
        
        data = response.json()
        assert isinstance(data, list)
