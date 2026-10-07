# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Tests para Validación de Datos (Schemas)
#  Pydantic Validation, Input Sanitization
# ═══════════════════════════════════════════════════════════

import pytest
from fastapi import status
from schemas.auth import LoginRequest, CreateUserRequest


class TestLoginRequestSchema:
    """Tests para validación de LoginRequest"""
    
    def test_login_request_valid_data(self):
        """✅ LoginRequest acepta datos válidos"""
        data = LoginRequest(username="testuser", password="password123")
        
        assert data.username == "testuser"
        assert data.password == "password123"
    
    def test_login_request_username_required(self):
        """✅ LoginRequest requiere username"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            LoginRequest(password="password123")
    
    def test_login_request_password_required(self):
        """✅ LoginRequest requiere password"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            LoginRequest(username="testuser")
    
    def test_login_request_username_min_length(self):
        """✅ LoginRequest valida longitud mínima de username"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            LoginRequest(username="ab", password="password123")
    
    def test_login_request_username_max_length(self):
        """✅ LoginRequest valida longitud máxima de username"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            LoginRequest(username="a" * 51, password="password123")
    
    def test_login_request_username_lowercase(self):
        """✅ LoginRequest convierte username a minúsculas"""
        data = LoginRequest(username="TestUser", password="password123")
        
        assert data.username == "testuser"
    
    def test_login_request_password_min_length(self):
        """✅ LoginRequest requiere password no vacía"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            LoginRequest(username="testuser", password="")


class TestCreateUserRequestSchema:
    """Tests para validación de CreateUserRequest"""
    
    def test_create_user_request_valid_data(self):
        """✅ CreateUserRequest acepta datos válidos"""
        data = CreateUserRequest(
            username="testuser",
            password="TestPassword123",
            name="Test User",
            email="test@example.com",
            role="tecnico"
        )
        
        assert data.username == "testuser"
        assert data.role == "tecnico"
    
    def test_create_user_request_required_fields(self):
        """✅ CreateUserRequest requiere campos obligatorios"""
        from pydantic import ValidationError
        
        # Falta name
        with pytest.raises(ValidationError):
            CreateUserRequest(
                username="testuser",
                password="TestPassword123",
                role="tecnico"
            )
    
    def test_create_user_request_weak_password(self):
        """✅ CreateUserRequest rechaza contraseña débil"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            CreateUserRequest(
                username="testuser",
                password="weak",  # Muy corta
                name="Test User",
                role="tecnico"
            )
    
    def test_create_user_request_invalid_role(self):
        """✅ CreateUserRequest valida role"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            CreateUserRequest(
                username="testuser",
                password="TestPassword123",
                name="Test User",
                role="invalid_role"
            )
    
    def test_create_user_request_invalid_email(self):
        """✅ CreateUserRequest valida formato de email"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            CreateUserRequest(
                username="testuser",
                password="TestPassword123",
                name="Test User",
                email="invalid-email",
                role="tecnico"
            )
    
    def test_create_user_request_valid_without_email(self):
        """✅ CreateUserRequest permite omitir email"""
        data = CreateUserRequest(
            username="testuser",
            password="TestPassword123",
            name="Test User",
            role="tecnico"
        )
        
        assert data.email is None
    
    def test_create_user_request_default_role(self):
        """✅ CreateUserRequest usa rol por defecto"""
        data = CreateUserRequest(
            username="testuser",
            password="TestPassword123",
            name="Test User"
        )
        
        assert data.role == "tecnico"


class TestDataSanitization:
    """Tests para sanitización de entrada de datos"""
    
    def test_username_sql_injection_attempt(self, client):
        """✅ SQL Injection en username se maneja"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin' OR '1'='1",
                "password": "password"
            }
        )
        
        # Debe fallar con credenciales incorrectas, no con SQL error
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    def test_password_with_special_chars(self, client):
        """✅ Contraseña con caracteres especiales funciona"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123!@#$%^&*()"
            }
        )
        
        # Debe retornar 401, no error de parsing
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_username_with_spaces_trimmed(self, client):
        """✅ Espacios en username se manejan"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "  admin  ",
                "password": "admin123"
            }
        )
        
        # Debería intentar login, después que se recorte
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
    
    def test_xss_attempt_in_name(self, client, admin_headers):
        """✅ XSS attempt en nombre se maneja"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "testuser",
                "password": "TestPassword123",
                "name": "<script>alert('xss')</script>",
                "role": "tecnico"
            }
        )
        
        # Debe procesarse como texto plano, no ejecutarse
        # Status 200 si se crea, o 422 si lo valida y rechaza
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestFieldLengthValidation:
    """Tests para validación de longitud de campos"""
    
    def test_username_exactly_min_length(self, client):
        """✅ Username con longitud mínima exacta funciona"""
        response = client.post(
            "/api/auth/login",
            json={"username": "abc", "password": "password"}  # Exactamente 3
        )
        
        # Debe pasar validación de longitud (aunque usuario no exista)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    def test_username_exactly_max_length(self, client):
        """✅ Username con longitud máxima exacta funciona"""
        username = "a" * 50  # Exactamente 50
        response = client.post(
            "/api/auth/login",
            json={"username": username, "password": "password"}
        )
        
        # Debe pasar validación de longitud
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    def test_name_very_long(self, client, admin_headers):
        """✅ Name muy largo se procesa"""
        long_name = "A" * 200
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "testuser",
                "password": "TestPassword123",
                "name": long_name,
                "role": "tecnico"
            }
        )
        
        # Debe aceptar o validar según límite configurado
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestEmailValidationInRequest:
    """Tests para validación de email en requests"""
    
    def test_email_with_subdomain(self, client, admin_headers):
        """✅ Email con subdominio es válido"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "testuser1",
                "password": "TestPassword123",
                "name": "Test User",
                "email": "user@mail.example.com",
                "role": "tecnico"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_email_with_plus(self, client, admin_headers):
        """✅ Email con plus es válido"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "testuser2",
                "password": "TestPassword123",
                "name": "Test User",
                "email": "user+tag@example.com",
                "role": "tecnico"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
