# ═══════════════════════════════════════════════════════════
#  TESTS DE AUTORIZACIÓN — EMANTIC PRO
#  Verificar que RBAC está implementado correctamente
# ═══════════════════════════════════════════════════════════

import pytest
from fastapi import status
from tests.conftest import client, admin_headers, tecnico_headers, db_session


class TestAuthenticationRequirement:
    """Tests para verificar que endpoints requieren autenticación"""
    
    def test_maintenance_list_requires_auth(self, client):
        """❌ GET /maintenance sin token debe fallar"""
        response = client.get("/api/maintenance")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_maintenance_get_requires_auth(self, client):
        """❌ GET /maintenance/{id} sin token debe fallar"""
        response = client.get("/api/maintenance/fake-id")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_reportes_list_requires_auth(self, client):
        """❌ GET /reportes sin token debe fallar"""
        response = client.get("/api/reportes")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_reportes_resumen_requires_auth(self, client):
        """❌ GET /reportes/resumen sin token debe fallar"""
        response = client.get("/api/reportes/resumen")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_manuals_list_requires_auth(self, client):
        """❌ GET /manuals sin token debe fallar"""
        response = client.get("/api/manuals")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_manuals_categories_requires_auth(self, client):
        """❌ GET /manuals/categories/list sin token debe fallar"""
        response = client.get("/api/manuals/categories/list")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAuthenticationAllows:
    """Tests para verificar que endpoints funcionan CON autenticación"""
    
    def test_maintenance_list_with_auth(self, client, admin_headers):
        """✅ GET /maintenance CON token funciona"""
        response = client.get("/api/maintenance", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
    
    def test_reportes_list_with_auth(self, client, admin_headers):
        """✅ GET /reportes CON token funciona"""
        response = client.get("/api/reportes", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
    
    def test_manuals_list_with_auth(self, client, admin_headers):
        """✅ GET /manuals CON token funciona"""
        response = client.get("/api/manuals", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK


class TestAdminOnlyEndpoints:
    """Tests para verificar que solo admin puede hacer cambios"""
    
    def test_create_user_requires_admin(self, client, tecnico_headers):
        """❌ POST /users como técnico debe fallar"""
        response = client.post(
            "/api/users",
            headers=tecnico_headers,
            json={
                "username": "newuser",
                "name": "New User",
                "password": "SecurePass123!",
                "role": "tecnico"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_user_as_admin(self, client, admin_headers):
        """✅ POST /users como admin funciona"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "rbactest",
                "name": "RBAC Test User",
                "password": "TestPass123!",
                "role": "tecnico"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_delete_user_requires_admin(self, client, tecnico_headers):
        """❌ DELETE /users/{username} como técnico debe fallar"""
        response = client.delete(
            "/api/users/testuser",
            headers=tecnico_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_toggle_user_requires_admin(self, client, tecnico_headers):
        """❌ PATCH /users/{username}/toggle como técnico debe fallar"""
        response = client.patch(
            "/api/users/testuser/toggle",
            headers=tecnico_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_change_role_requires_admin(self, client, tecnico_headers):
        """❌ PATCH /users/{username}/role como técnico debe fallar"""
        response = client.patch(
            "/api/users/testuser/role",
            headers=tecnico_headers,
            params={"new_role": "admin"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAdminProtection:
    """Tests para verificar que admin principal no puede ser modificado"""
    
    def test_cannot_delete_admin(self, client, admin_headers):
        """❌ No se puede eliminar al admin principal"""
        response = client.delete(
            "/api/users/admin",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_cannot_toggle_admin(self, client, admin_headers):
        """❌ No se puede bloquear al admin principal"""
        response = client.patch(
            "/api/users/admin/toggle",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_cannot_change_admin_role(self, client, admin_headers):
        """❌ No se puede cambiar rol del admin principal"""
        response = client.patch(
            "/api/users/admin/role",
            headers=admin_headers,
            params={"new_role": "tecnico"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAuditLog:
    """Tests para verificar auditoría de cambios"""
    
    def test_create_user_is_audited(self, client, admin_headers, db_session):
        """✅ Crear usuario registra en auditoría"""
        # Contar auditorías antes
        from database import RoleAuditDB
        before = db_session.query(RoleAuditDB).count()
        
        # Crear usuario
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "audituser",
                "name": "Audit Test User",
                "password": "AuditPass123!",
                "role": "tecnico"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Contar auditorías después
        after = db_session.query(RoleAuditDB).count()
        assert after > before, "No se registró auditoría de creación de usuario"
    
    def test_role_change_is_audited(self, client, admin_headers, db_session):
        """✅ Cambiar rol registra en auditoría"""
        from database import RoleAuditDB
        
        # Contar auditorías antes
        before = db_session.query(RoleAuditDB).count()
        
        # Crear usuario primero
        create_response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "changeuser",
                "name": "Change Test User",
                "password": "ChangePass123!",
                "role": "tecnico"
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        
        # Cambiar rol
        change_response = client.patch(
            "/api/users/changeuser/role",
            headers=admin_headers,
            params={"new_role": "admin"}
        )
        assert change_response.status_code == status.HTTP_200_OK
        
        # Verificar que hay auditorías
        after = db_session.query(RoleAuditDB).count()
        assert after > before, "No se registraron auditorías"
    
    def test_audit_log_visible_to_admin(self, client, admin_headers):
        """✅ Admin puede ver log de auditoría"""
        response = client.get(
            "/api/users/audit/log",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert "audits" in response.json()
    
    def test_audit_log_requires_admin(self, client, tecnico_headers):
        """❌ Técnico NO puede ver log de auditoría"""
        response = client.get(
            "/api/users/audit/log",
            headers=tecnico_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestInvalidTokens:
    """Tests para verificar rechazo de tokens inválidos"""
    
    def test_invalid_token_rejected(self, client):
        """❌ Token inválido rechazado"""
        response = client.get(
            "/api/maintenance",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_expired_token_rejected(self, client):
        """❌ Token expirado rechazado"""
        # Token que expiró hace días
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MjY5NDAwMDB9.invalid"
        response = client.get(
            "/api/maintenance",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_no_token_rejected(self, client):
        """❌ Sin token rechazado"""
        response = client.get("/api/maintenance")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRoleBasedAccess:
    """Tests para verificar control de acceso por rol"""
    
    def test_tecnico_can_read_maintenance(self, client, tecnico_headers):
        """✅ Técnico puede leer mantenimiento"""
        response = client.get(
            "/api/maintenance",
            headers=tecnico_headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_tecnico_cannot_create_maintenance(self, client, tecnico_headers):
        """❌ Técnico NO puede crear mantenimiento (es admin-only)"""
        response = client.post(
            "/api/maintenance",
            headers=tecnico_headers,
            json={
                "unidad": "Z99",
                "tipo": "Test",
                "km_actual": 100000,
                "km_servicio": 105000,
                "fecha": "2026-09-01",
                "estado": "Programado"
            }
        )
        # Debería fallar porque es admin-only
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_create_maintenance(self, client, admin_headers):
        """✅ Admin puede crear mantenimiento"""
        response = client.post(
            "/api/maintenance",
            headers=admin_headers,
            json={
                "unidad": "Z99",
                "tipo": "Test",
                "km_actual": 100000,
                "km_servicio": 105000,
                "fecha": "2026-09-01",
                "estado": "Programado"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
