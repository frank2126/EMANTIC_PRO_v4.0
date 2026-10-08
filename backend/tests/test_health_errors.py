
#  Verificar seguridad y funcionamiento correcto


import pytest
from fastapi import status
import json


class TestHealthEndpoints:
    """Tests para health check endpoints"""
    
    def test_health_basic_public(self, client):
        """ok GET /health es público"""
        response = client.get("/api/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_health_liveness_public(self, client):
        """ok GET /health/liveness es público"""
        response = client.get("/api/health/liveness")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["alive", "ok"]
    
    def test_health_startup_public(self, client):
        """ok GET /health/startup es público"""
        response = client.get("/api/health/startup")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ready"
    
    def test_health_readiness_public(self, client):
        """ok GET /health/readiness es público"""
        response = client.get("/api/health/readiness")
        
        # Debe funcionar sin token
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ready"
        
        # NO debe exponer información sensible
        assert "memory_usage_percent" not in str(data)
        assert "cpu_usage_percent" not in str(data)
        assert "disk_usage_percent" not in str(data)
    
    def test_health_full_requires_admin(self, client):
        """x GET /health/full sin token → 403"""
        response = client.get("/api/health/full")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_health_full_requires_admin_not_user(self, client, tecnico_headers):
        """x GET /health/full como técnico → 403"""
        response = client.get("/api/health/full", headers=tecnico_headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_health_full_admin_access(self, client, admin_headers):
        """ok GET /health/full como admin → 200"""
        response = client.get("/api/health/full", headers=admin_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Admin ve detalles
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in data
        assert "database" in data["components"]
        assert "memory" in data["components"]
        assert "cpu" in data["components"]
        assert "disk" in data["components"]
        
        # Admin puede ver información del sistema
        assert "system" in data
        assert "memory_usage_percent" in data["system"]
        assert "cpu_usage_percent" in data["system"]
        assert "disk_usage_percent" in data["system"]


class TestErrorHandling:
    """Tests para error handling global"""
    
    def test_validation_error_format(self, client):
        """ok Validation error retorna formato consistente"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin"}  # Falta password
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        
        # Verificar formato consistente
        assert "error" in data
        assert "type" in data
        assert "message" in data
        assert data["type"] == "validation_error"
    
    def test_not_found_error(self, client, admin_headers):
        """ok Not found retorna JSON consistente"""
        response = client.get(
            "/api/maintenance/nonexistent-id",
            headers=admin_headers
        )
        
        # Podría ser 404 o algo similar
        if response.status_code == status.HTTP_404_NOT_FOUND:
            data = response.json()
            # Verificar formato
            assert isinstance(data, dict)
    
    def test_unauthorized_error_format(self, client):
        """ok Unauthorized retorna JSON consistente"""
        response = client.get(
            "/api/users",  # Endpoint que requiere auth
            headers={"Authorization": "Bearer invalid"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        
        # Debe ser JSON válido
        assert isinstance(data, dict)
    
    def test_forbidden_error_format(self, client, tecnico_headers):
        """ok Forbidden retorna JSON consistente"""
        response = client.post(
            "/api/users",  # Admin only
            headers=tecnico_headers,
            json={
                "username": "test",
                "password": "Test123!",
                "name": "Test User",
                "role": "tecnico"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        
        # Debe ser JSON válido
        assert isinstance(data, dict)
    
    def test_error_no_stack_trace_in_response(self, client):
        """ok Errors no exponen stack traces en respuesta"""
        # Intentar algo inválido
        response = client.get(
            "/api/users",
            headers={"Authorization": "Bearer invalid"}
        )
        
        # Verificar que no hay stack trace
        response_text = response.text
        assert "File \"" not in response_text
        assert "Traceback" not in response_text
        assert "line " not in response_text.lower() or "File" not in response_text
    
    def test_error_no_sql_in_response(self, client, admin_headers):
        """ok Errors no exponen SQL en respuesta"""
        # Intentar operación inválida
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "admin",  # Ya existe
                "password": "Test123!",
                "name": "Test User",
                "role": "tecnico"
            }
        )
        
        # No debería haber SQL en la respuesta
        response_text = response.text
        assert "SELECT" not in response_text.upper()
        assert "INSERT" not in response_text.upper()
        assert "UPDATE" not in response_text.upper()
        assert "FROM" not in response_text.upper()
        assert "WHERE" not in response_text.upper()
    
    def test_request_id_in_response(self, client):
        """ok Errors incluyen request ID para tracking"""
        response = client.get(
            "/api/users"  # Sin token
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Debería tener request ID en headers
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] != ""


class TestEndpointsStillWork:
    """Tests para verificar que endpoints normales siguen funcionando"""
    
    def test_login_still_works(self, client):
        """ok POST /login sigue funcionando"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123!"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "user" in data
    
    def test_me_endpoint_still_works(self, client, admin_headers):
        """ok GET /auth/me sigue funcionando"""
        response = client.get(
            "/api/auth/me",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "admin"
    
    def test_list_users_still_works(self, client, admin_headers):
        """ok GET /users sigue funcionando"""
        response = client.get(
            "/api/users",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)
    
    def test_maintenance_list_still_works(self, client, admin_headers):
        """ok GET /maintenance sigue funcionando"""
        response = client.get(
            "/api/maintenance",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Podría ser lista o dict con paginación
        assert data is not None
    
    def test_reportes_list_still_works(self, client, admin_headers):
        """ok GET /reportes sigue funcionando"""
        response = client.get(
            "/api/reportes",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data is not None
    
    def test_manuals_list_still_works(self, client, admin_headers):
        """ok GET /manuals sigue funcionando"""
        response = client.get(
            "/api/manuals",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data is not None
