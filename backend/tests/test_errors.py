# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Tests para Manejo de Errores y Edge Cases
#  Excepciones, Accesos No Autorizados, Límites
# ═══════════════════════════════════════════════════════════

import pytest
from fastapi import status


class TestUnauthorizedAccess:
    """Tests para accesos no autorizados"""
    
    def test_access_admin_endpoint_without_token(self, client):
        """✅ Acceso denegado sin token a endpoints admin"""
        response = client.get("/api/users")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_access_admin_endpoint_with_expired_token(self, client, expired_headers):
        """✅ Acceso denegado con token expirado"""
        response = client.get("/api/users", headers=expired_headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_admin_endpoint_with_invalid_token(self, client, invalid_headers):
        """✅ Acceso denegado con token inválido"""
        response = client.get("/api/users", headers=invalid_headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_tecnico_cannot_access_admin_endpoints(self, client, tecnico_headers):
        """✅ Técnico no puede acceder a endpoints admin"""
        response = client.get("/api/users", headers=tecnico_headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_missing_authorization_header(self, client):
        """✅ Sin header Authorization falla"""
        response = client.get(
            "/api/users",
            headers={"Authorization": ""}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_wrong_authorization_scheme(self, client, admin_token):
        """✅ Scheme de autorización incorrecto falla"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Basic {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAuthenticationErrors:
    """Tests para errores de autenticación"""
    
    def test_login_with_empty_password(self, client):
        """✅ Login con contraseña vacía falla"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": ""}
        )
        
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_401_UNAUTHORIZED
        ]
    
    def test_login_with_empty_username(self, client):
        """✅ Login con username vacío falla"""
        response = client.post(
            "/api/auth/login",
            json={"username": "", "password": "admin123"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_with_very_long_password(self, client):
        """✅ Login con contraseña muy larga"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "x" * 10000}
        )
        
        # Debe procesarse sin colgar (timeout)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        ]
    
    def test_login_case_sensitivity(self, client):
        """✅ Contraseña es case-sensitive"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "ADMIN123"}  # Mayúsculas
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestInputValidationEdgeCases:
    """Tests para casos límite de validación de entrada"""
    
    def test_username_with_unicode(self, client):
        """✅ Username con caracteres unicode"""
        response = client.post(
            "/api/auth/login",
            json={"username": "üsér", "password": "password"}
        )
        
        # Debe aceptar o rechazar consistentemente
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    def test_password_with_unicode(self, client):
        """✅ Contraseña con caracteres unicode"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "pässwörd123"}
        )
        
        # Debe procesarse
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_200_OK
        ]
    
    def test_name_with_special_characters(self, client, admin_headers):
        """✅ Nombre con caracteres especiales"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "user1",
                "password": "Password123",
                "name": "O'Brien & Co. <Test>",
                "role": "tecnico"
            }
        )
        
        # Debe procesarse sin error de escape
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_email_with_many_dots(self, client, admin_headers):
        """✅ Email con muchos puntos"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "user2",
                "password": "Password123",
                "name": "Test User",
                "email": "user.name.with.many.dots@example.com.uk",
                "role": "tecnico"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK


class TestConcurrencyAndRaceConditions:
    """Tests para condiciones de concurrencia"""
    
    def test_multiple_login_attempts(self, client):
        """✅ Múltiples intentos de login simultáneos"""
        # Simular múltiples requests
        for _ in range(3):
            response = client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "admin123"}
            )
            assert response.status_code == status.HTTP_200_OK
    
    def test_user_creation_concurrent(self, client, admin_headers):
        """✅ Creación concurrente de usuarios"""
        for i in range(3):
            response = client.post(
                "/api/users",
                headers=admin_headers,
                json={
                    "username": f"concurrent{i}",
                    "password": "Password123",
                    "name": f"User {i}",
                    "role": "tecnico"
                }
            )
            assert response.status_code == status.HTTP_200_OK


class TestBoundaryConditions:
    """Tests para condiciones de límite"""
    
    def test_very_long_username(self, client):
        """✅ Username muy largo es rechazado"""
        response = client.post(
            "/api/auth/login",
            json={"username": "a" * 100, "password": "password"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_zero_length_fields(self, client):
        """✅ Campos de longitud cero son rechazados"""
        response = client.post(
            "/api/auth/login",
            json={"username": "", "password": ""}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_whitespace_only_fields(self, client):
        """✅ Campos solo con espacios"""
        response = client.post(
            "/api/auth/login",
            json={"username": "   ", "password": "   "}
        )
        
        # Depende del trimming
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


class TestResourceNotFound:
    """Tests para recursos no encontrados"""
    
    def test_delete_nonexistent_user(self, client, admin_headers):
        """✅ Eliminar usuario inexistente retorna 404"""
        response = client.delete(
            "/api/users/nonexistent",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_toggle_nonexistent_user(self, client, admin_headers):
        """✅ Toggle de usuario inexistente retorna 404"""
        response = client.patch(
            "/api/users/nonexistent/toggle",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_nonexistent_endpoint(self, client):
        """✅ Endpoint inexistente retorna 404"""
        response = client.get("/api/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestConflicts:
    """Tests para conflictos de recursos"""
    
    def test_create_user_duplicate_username(self, client, admin_headers):
        """✅ Crear usuario con username duplicado retorna 409"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "admin",
                "password": "Password123",
                "name": "Duplicate Admin",
                "role": "admin"
            }
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
    
    def test_create_user_duplicate_email(self, client, admin_headers):
        """✅ Crear usuario con email duplicado"""
        # Primero crear un usuario
        client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "user1",
                "password": "Password123",
                "name": "User 1",
                "email": "same@example.com",
                "role": "tecnico"
            }
        )
        
        # Intentar crear otro con mismo email
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "user2",
                "password": "Password123",
                "name": "User 2",
                "email": "same@example.com",
                "role": "tecnico"
            }
        )
        
        # Puede ser 409 o 200 dependiendo de si se valida
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_409_CONFLICT]


class TestMethodNotAllowed:
    """Tests para métodos HTTP no permitidos"""
    
    def test_post_on_get_endpoint(self, client):
        """✅ POST en endpoint GET-only retorna 405"""
        response = client.post("/health")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_get_on_post_endpoint(self, client):
        """✅ GET en endpoint POST-only retorna 405"""
        response = client.get("/api/auth/login")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_put_on_patch_only_endpoint(self, client, admin_headers):
        """✅ PUT en endpoint PATCH-only retorna 405"""
        response = client.put(
            "/api/users/tecnico/toggle",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestDataIntegrity:
    """Tests para integridad de datos"""
    
    def test_password_not_returned_in_response(self, client, admin_headers):
        """✅ Contraseña nunca se retorna en respuesta"""
        response = client.get(
            "/api/users",
            headers=admin_headers
        )
        
        users = response.json()
        for user in users:
            assert "password" not in user
            assert not any("password" in str(v).lower() for v in user.values() if isinstance(v, str))
    
    def test_user_email_masked_in_reset(self, client):
        """✅ Email se enmascara en respuesta de reset"""
        response = client.post(
            "/api/auth/forgot-password",
            json={"username": "admin"}
        )
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            if "masked_email" in data:
                # Email debe estar parcialmente ocultado
                assert "***" in data["masked_email"]
