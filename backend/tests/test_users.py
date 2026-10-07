# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Tests para routes/users.py
#  CRUD de Usuarios, Permisos, Autorización
# ═══════════════════════════════════════════════════════════

import pytest
from fastapi import status


class TestListUsersEndpoint:
    """Tests para endpoint GET /api/users"""
    
    def test_list_users_admin_access(self, client, admin_headers):
        """✅ Admin puede listar usuarios"""
        response = client.get(
            "/api/users",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 2  # Al menos admin y tecnico
    
    def test_list_users_tecnico_denied(self, client, tecnico_headers):
        """✅ Técnico no puede listar usuarios"""
        response = client.get(
            "/api/users",
            headers=tecnico_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "admin" in response.json()["detail"].lower()
    
    def test_list_users_no_auth(self, client):
        """✅ Sin autenticación se rechaza"""
        response = client.get("/api/users")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_users_invalid_token(self, client, invalid_headers):
        """✅ Token inválido se rechaza"""
        response = client.get(
            "/api/users",
            headers=invalid_headers
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_users_expired_token(self, client, expired_headers):
        """✅ Token expirado se rechaza"""
        response = client.get(
            "/api/users",
            headers=expired_headers
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateUserEndpoint:
    """Tests para endpoint POST /api/users"""
    
    def test_create_user_admin_success(self, client, admin_headers):
        """✅ Admin puede crear usuario"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "newuser",
                "password": "NewPassword123",
                "name": "New User",
                "email": "newuser@test.com",
                "role": "tecnico"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_id" in data
        assert "creado exitosamente" in data["message"]
    
    def test_create_user_tecnico_denied(self, client, tecnico_headers):
        """✅ Técnico no puede crear usuarios"""
        response = client.post(
            "/api/users",
            headers=tecnico_headers,
            json={
                "username": "newuser",
                "password": "NewPassword123",
                "name": "New User",
                "role": "tecnico"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_user_duplicate_username(self, client, admin_headers):
        """✅ No permite username duplicado"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "admin",  # Ya existe
                "password": "NewPassword123",
                "name": "Another Admin",
                "role": "admin"
            }
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "ya existe" in response.json()["detail"]
    
    def test_create_user_weak_password(self, client, admin_headers):
        """✅ Rechaza contraseña débil"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "newuser",
                "password": "weak",  # Muy corta
                "name": "New User",
                "role": "tecnico"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_user_invalid_role(self, client, admin_headers):
        """✅ Rechaza rol inválido"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "newuser",
                "password": "NewPassword123",
                "name": "New User",
                "role": "invalid_role"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_user_invalid_email_format(self, client, admin_headers):
        """✅ Rechaza email inválido"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "newuser",
                "password": "NewPassword123",
                "name": "New User",
                "email": "invalid-email",  # Sin @
                "role": "tecnico"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_user_missing_required_field(self, client, admin_headers):
        """✅ Rechaza si falta campo requerido"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "newuser",
                "password": "NewPassword123"
                # Falta "name"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_user_invalid_username(self, client, admin_headers):
        """✅ Rechaza username inválido"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "ab",  # Muy corto
                "password": "NewPassword123",
                "name": "New User",
                "role": "tecnico"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestToggleUserStatusEndpoint:
    """Tests para endpoint PATCH /api/users/{username}/toggle"""
    
    def test_toggle_user_block_tecnico(self, client, admin_headers):
        """✅ Admin puede bloquear usuario"""
        response = client.patch(
            "/api/users/tecnico/toggle",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["active"] is False
    
    def test_toggle_user_unblock_tecnico(self, client, admin_headers):
        """✅ Admin puede desbloquear usuario"""
        # Primero bloquear
        client.patch(
            "/api/users/tecnico/toggle",
            headers=admin_headers
        )
        
        # Luego desbloquear
        response = client.patch(
            "/api/users/tecnico/toggle",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["active"] is True
    
    def test_toggle_admin_protection(self, client, admin_headers):
        """✅ No permite bloquear admin principal"""
        response = client.patch(
            "/api/users/admin/toggle",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no puedes modificar" in response.json()["detail"].lower()
    
    def test_toggle_tecnico_denied(self, client, tecnico_headers):
        """✅ Técnico no puede togglear usuarios"""
        response = client.patch(
            "/api/users/tecnico/toggle",
            headers=tecnico_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_toggle_nonexistent_user(self, client, admin_headers):
        """✅ Falla si usuario no existe"""
        response = client.patch(
            "/api/users/nonexistent/toggle",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteUserEndpoint:
    """Tests para endpoint DELETE /api/users/{username}"""
    
    def test_delete_user_admin_success(self, client, admin_headers, create_test_user):
        """✅ Admin puede eliminar usuario"""
        # Crear usuario de prueba
        user = create_test_user("userdelete")
        
        response = client.delete(
            "/api/users/userdelete",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "eliminado" in response.json()["message"]
    
    def test_delete_admin_protection(self, client, admin_headers):
        """✅ No permite eliminar admin principal"""
        response = client.delete(
            "/api/users/admin",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no puedes eliminar" in response.json()["detail"].lower()
    
    def test_delete_tecnico_denied(self, client, tecnico_headers):
        """✅ Técnico no puede eliminar usuarios"""
        response = client.delete(
            "/api/users/tecnico",
            headers=tecnico_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_nonexistent_user(self, client, admin_headers):
        """✅ Falla si usuario no existe"""
        response = client.delete(
            "/api/users/nonexistent",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_no_auth(self, client):
        """✅ Sin autenticación se rechaza"""
        response = client.delete("/api/users/tecnico")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserAuthorizationMatrix:
    """Tests para verificar matriz de autorización completa"""
    
    def test_authorization_matrix_get_users(self, client, admin_headers, tecnico_headers):
        """✅ Matriz de autorización para GET /api/users"""
        # Admin: permitido
        response_admin = client.get("/api/users", headers=admin_headers)
        assert response_admin.status_code == status.HTTP_200_OK
        
        # Tecnico: denegado
        response_tecnico = client.get("/api/users", headers=tecnico_headers)
        assert response_tecnico.status_code == status.HTTP_403_FORBIDDEN
    
    def test_authorization_matrix_create_user(self, client, admin_headers, tecnico_headers):
        """✅ Matriz de autorización para POST /api/users"""
        test_data = {
            "username": "testuser",
            "password": "TestPassword123",
            "name": "Test User",
            "role": "tecnico"
        }
        
        # Admin: permitido
        response_admin = client.post("/api/users", headers=admin_headers, json=test_data)
        assert response_admin.status_code in [status.HTTP_200_OK, status.HTTP_409_CONFLICT]
        
        # Tecnico: denegado
        test_data["username"] = "testuser2"
        response_tecnico = client.post("/api/users", headers=tecnico_headers, json=test_data)
        assert response_tecnico.status_code == status.HTTP_403_FORBIDDEN
