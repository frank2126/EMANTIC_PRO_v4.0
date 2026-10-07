# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Tests para security.py
#  JWT, Bcrypt, Validaciones
# ═══════════════════════════════════════════════════════════

import pytest
from datetime import datetime, timedelta, timezone
from security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    validate_password_strength,
    get_password_error_message,
    validate_email,
    validate_username,
)
from config import settings
import jwt


class TestPasswordHashing:
    """Tests para hashing y verificación de contraseñas con bcrypt"""
    
    def test_hash_password_creates_valid_hash(self):
        """✅ hash_password genera hash válido"""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert len(hashed) > 0
        assert "$2b$" in hashed  # Bcrypt hash format
    
    def test_hash_password_different_each_time(self):
        """✅ hash_password genera diferentes hashes para misma contraseña"""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes diferentes debido al salt aleatorio
        assert hash1 != hash2
    
    def test_verify_password_correct_password(self):
        """✅ verify_password retorna True para contraseña correcta"""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect_password(self):
        """✅ verify_password retorna False para contraseña incorrecta"""
        password = "TestPassword123"
        wrong_password = "WrongPassword123"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_case_sensitive(self):
        """✅ verify_password es case-sensitive"""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        # Cambiar mayúscula
        assert verify_password("testpassword123", hashed) is False
        assert verify_password("TESTPASSWORD123", hashed) is False
    
    def test_hash_password_minimum_length(self):
        """❌ hash_password rechaza contraseña muy corta"""
        with pytest.raises(ValueError, match="Contraseña debe tener mínimo"):
            hash_password("short")
    
    def test_verify_password_invalid_hash(self):
        """✅ verify_password maneja hash inválido gracefully"""
        result = verify_password("password", "invalid_hash")
        assert result is False


class TestJWTTokens:
    """Tests para creación y verificación de JWT"""
    
    def test_create_access_token_generates_valid_jwt(self):
        """✅ create_access_token genera JWT válido"""
        data = {"sub": "user-123", "username": "testuser", "role": "admin"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT tiene 3 partes: header.payload.signature
    
    def test_verify_token_decodes_valid_token(self):
        """✅ verify_token decodifica JWT válido"""
        data = {"sub": "user-123", "username": "testuser", "role": "admin"}
        token = create_access_token(data)
        
        decoded = verify_token(token)
        assert decoded["sub"] == "user-123"
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "admin"
    
    def test_verify_token_rejects_invalid_signature(self):
        """✅ verify_token rechaza JWT con firma inválida"""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyJ9.invalid_signature"
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException, match="401"):
            verify_token(token)
    
    def test_verify_token_rejects_expired_token(self):
        """✅ verify_token rechaza tokens expirados"""
        # Crear token con expiración en el pasado
        payload = {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException, match="expirado"):
            verify_token(token)
    
    def test_create_access_token_includes_expiration(self):
        """✅ create_access_token incluye expiración"""
        data = {"sub": "user-123"}
        token = create_access_token(data)
        
        decoded = verify_token(token)
        assert "exp" in decoded
        assert decoded["exp"] > datetime.now(timezone.utc).timestamp()
    
    def test_create_access_token_custom_expiration(self):
        """✅ create_access_token respeta expiración personalizada"""
        data = {"sub": "user-123"}
        custom_expiration = timedelta(hours=1)
        token = create_access_token(data, expires_delta=custom_expiration)
        
        decoded = verify_token(token)
        # Verificar que está cerca de 1 hora en el futuro (con margen de 5 segundos)
        expected_exp = (datetime.now(timezone.utc) + custom_expiration).timestamp()
        assert abs(decoded["exp"] - expected_exp) < 5
    
    def test_create_refresh_token_generates_valid_jwt(self):
        """✅ create_refresh_token genera JWT válido"""
        data = {"sub": "user-123"}
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        decoded = verify_token(token)
        assert decoded.get("type") == "refresh"
    
    def test_verify_token_rejects_malformed_jwt(self):
        """✅ verify_token rechaza JWT malformado"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException):
            verify_token("not.a.valid.jwt.structure")


class TestPasswordValidation:
    """Tests para validación de fortaleza de contraseña"""
    
    def test_validate_password_strength_strong_password(self):
        """✅ Detecta contraseña fuerte"""
        validation = validate_password_strength("ValidPassword123!")
        assert validation["length"] is True
        assert validation["uppercase"] is True
        assert validation["number"] is True
    
    def test_validate_password_strength_missing_uppercase(self):
        """✅ Detecta falta de mayúscula"""
        validation = validate_password_strength("validpassword123")
        assert validation["uppercase"] is False
    
    def test_validate_password_strength_missing_number(self):
        """✅ Detecta falta de número"""
        validation = validate_password_strength("ValidPassword")
        assert validation["number"] is False
    
    def test_validate_password_strength_too_short(self):
        """✅ Detecta contraseña muy corta"""
        validation = validate_password_strength("Pass1")
        assert validation["length"] is False
    
    def test_get_password_error_message_length_error(self):
        """✅ get_password_error_message retorna mensaje de longitud"""
        validation = {"length": False, "uppercase": True, "number": True, "special": True}
        msg = get_password_error_message(validation)
        assert "caracteres" in msg
    
    def test_get_password_error_message_uppercase_error(self):
        """✅ get_password_error_message retorna mensaje de mayúscula"""
        validation = {"length": True, "uppercase": False, "number": True, "special": True}
        msg = get_password_error_message(validation)
        assert "mayúscula" in msg
    
    def test_get_password_error_message_valid_password(self):
        """✅ get_password_error_message retorna None para contraseña válida"""
        validation = {"length": True, "uppercase": True, "number": True, "special": True}
        msg = get_password_error_message(validation)
        assert msg is None


class TestEmailValidation:
    """Tests para validación de email"""
    
    def test_validate_email_valid_email(self):
        """✅ Valida email correcto"""
        assert validate_email("user@example.com") is True
    
    def test_validate_email_invalid_email_no_at(self):
        """✅ Rechaza email sin @"""
        assert validate_email("userexample.com") is False
    
    def test_validate_email_invalid_email_no_domain(self):
        """✅ Rechaza email sin dominio"""
        assert validate_email("user@") is False
    
    def test_validate_email_with_plus(self):
        """✅ Valida email con plus"""
        assert validate_email("user+tag@example.com") is True
    
    def test_validate_email_subdomain(self):
        """✅ Valida email con subdominio"""
        assert validate_email("user@mail.example.com") is True


class TestUsernameValidation:
    """Tests para validación de username"""
    
    def test_validate_username_valid_username(self):
        """✅ Valida username válido"""
        assert validate_username("validuser") is True
    
    def test_validate_username_with_dots(self):
        """✅ Valida username con puntos"""
        assert validate_username("valid.user") is True
    
    def test_validate_username_with_dashes(self):
        """✅ Valida username con guiones"""
        assert validate_username("valid-user") is True
    
    def test_validate_username_with_underscores(self):
        """✅ Valida username con guiones bajos"""
        assert validate_username("valid_user") is True
    
    def test_validate_username_too_short(self):
        """✅ Rechaza username muy corto"""
        assert validate_username("ab") is False
    
    def test_validate_username_too_long(self):
        """✅ Rechaza username muy largo"""
        assert validate_username("a" * 51) is False
    
    def test_validate_username_with_spaces(self):
        """✅ Rechaza username con espacios"""
        assert validate_username("valid user") is False
    
    def test_validate_username_with_special_chars(self):
        """✅ Rechaza username con caracteres especiales"""
        assert validate_username("valid@user") is False
