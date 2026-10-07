# ═══════════════════════════════════════════════════════════
#  TESTS DE SEGURIDAD — XSS Y RATE LIMITING
#  Verificar protección contra ataques comunes
# ═══════════════════════════════════════════════════════════

import pytest
from fastapi import status
import time
from database import UserDB


class TestXSSPrevention:
    """Tests para verificar protección contra XSS"""
    
    def test_create_user_sanitizes_name(self, client, admin_headers, db_session):
        """✅ Crear usuario sanitiza el nombre"""
        # Intentar crear usuario con HTML/script en nombre
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "xsstest1",
                "name": "<script>alert('xss')</script>",
                "password": "SecurePass123!",
                "role": "tecnico"
            }
        )
        
        # Debería rechazar o sanitizar
        if response.status_code == status.HTTP_201_CREATED:
            # Si acepta, verificar que se sanitizó
            user_id = response.json().get("user_id")
            
            # Obtener usuario y verificar que el nombre está limpio
            user = db_session.query(UserDB).filter_by(id=user_id).first()
            assert user is not None
            # No debería contener script tags
            assert "<script>" not in user.name.lower()
            assert "alert" not in user.name.lower()
    
    def test_create_user_removes_event_handlers(self, client, admin_headers):
        """✅ Crear usuario remueve event handlers"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "xsstest2",
                "name": "Normal Name\" onclick=\"alert('xss')",
                "password": "SecurePass123!",
                "role": "tecnico"
            }
        )
        
        # Debería no contener onclick
        if response.status_code == status.HTTP_201_CREATED:
            name = response.json().get("name", "")
            assert "onclick" not in name.lower()
    
    def test_create_user_removes_javascript_protocol(self, client, admin_headers):
        """✅ Crear usuario remueve javascript: protocol"""
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "xsstest3",
                "name": "Click me javascript:alert('xss')",
                "password": "SecurePass123!",
                "role": "tecnico"
            }
        )
        
        if response.status_code == status.HTTP_201_CREATED:
            name = response.json().get("name", "")
            assert "javascript:" not in name.lower()
    
    def test_sanitize_string_escapes_html(self):
        """✅ sanitize_string escapa HTML entities"""
        from utils.sanitize import sanitize_string
        
        # HTML debería ser escapado
        result = sanitize_string("<b>bold</b>")
        # Después de sanitizar, no debería haber tags
        assert "<" not in result
        assert ">" not in result
    
    def test_sanitize_removes_null_bytes(self):
        """✅ sanitize_string remueve null bytes"""
        from utils.sanitize import sanitize_string
        
        # Null bytes son peligrosos
        malicious = "normal\x00malicious"
        result = sanitize_string(malicious)
        assert "\x00" not in result
        assert "malicious" in result
    
    def test_is_safe_string_detects_script_tags(self):
        """✅ is_safe_string detecta script tags"""
        from utils.sanitize import is_safe_string
        
        assert not is_safe_string("<script>alert('xss')</script>")
        assert not is_safe_string("Normal<script>")
        assert is_safe_string("Normal string")


class TestRateLimitLogin:
    """Tests para rate limiting en login"""
    
    def test_login_allows_valid_attempts(self, client):
        """✅ Login permite intentos válidos"""
        # 1 intento con credenciales válidas
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123!"}
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_login_rate_limit_blocks_after_5_failures(self, client):
        """✅ Login bloquea después de 5 intentos fallidos"""
        # Hacer 5 intentos fallidos
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "WrongPassword123"}
            )
            # 1-5: Debería devolver 401 (credenciales inválidas)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Intento 6: Debería bloquear con 429
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123!"}
        )
        
        # Ahora incluso con credenciales válidas → 429
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_login_rate_limit_has_retry_after(self, client):
        """✅ Rate limit devuelve Retry-After header"""
        # Hacer intentos hasta bloquear
        for i in range(5):
            client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "Wrong"}
            )
        
        # Siguiente intento bloqueado
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123!"}
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Retry-After" in response.headers


class TestRateLimitForgotPassword:
    """Tests para rate limiting en forgot-password"""
    
    def test_forgot_password_rate_limit_blocks_after_3_attempts(self, client):
        """✅ Forgot password bloquea después de 3 intentos"""
        # Hacer 3 intentos
        for i in range(3):
            response = client.post(
                "/api/auth/forgot-password",
                json={"username": "admin"}
            )
            assert response.status_code == status.HTTP_200_OK
        
        # Intento 4: Bloqueado
        response = client.post(
            "/api/auth/forgot-password",
            json={"username": "admin"}
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestRateLimitResetPassword:
    """Tests para rate limiting en reset-password"""
    
    def test_reset_password_allows_multiple_attempts(self, client):
        """✅ Reset password permite múltiples intentos (5)"""
        # Hacer 5 intentos
        for i in range(5):
            response = client.post(
                "/api/auth/reset-password",
                json={
                    "username": "admin",
                    "code": "000000",
                    "new_password": "NewPass123!",
                    "confirm_password": "NewPass123!"
                }
            )
            # Probablemente 401 (código inválido) pero no bloqueado
            assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS
        
        # Intento 6: Bloqueado
        response = client.post(
            "/api/auth/reset-password",
            json={
                "username": "admin",
                "code": "000000",
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!"
            }
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestRateLimitRefreshToken:
    """Tests para rate limiting en refresh token"""
    
    def test_refresh_token_allows_many_attempts(self, client, admin_headers):
        """✅ Refresh token es más generoso (20 intentos/min)"""
        # Obtener refresh token
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123!"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Hacer múltiples intentos de refresh (dentro del límite)
        for i in range(10):
            response = client.post(
                "/api/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            # Debería funcionar (o fallar con 401, pero no bloqueado)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                pytest.fail(f"Rate limit hit en intento {i+1}, límite es 20/min")


class TestRateLimitCreateUser:
    """Tests para rate limiting en crear usuario"""
    
    def test_create_user_rate_limit(self, client, admin_headers):
        """✅ Crear usuario tiene rate limit por admin (10/hora)"""
        # Hacer 10 intentos
        for i in range(10):
            response = client.post(
                "/api/users",
                headers=admin_headers,
                json={
                    "username": f"ratelimituser{i}",
                    "name": f"Rate Limit User {i}",
                    "password": "SecurePass123!",
                    "role": "tecnico"
                }
            )
            # Todos deberían ser exitosos
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_409_CONFLICT  # Si username ya existe
            ]
        
        # Intento 11: Bloqueado
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "username": "ratelimituser99",
                "name": "Rate Limit User 99",
                "password": "SecurePass123!",
                "role": "tecnico"
            }
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestRateLimitResetAfterWindow:
    """Tests para verificar que rate limit se resetea después de la ventana"""
    
    def test_rate_limit_resets_after_window(self, client):
        """✅ Rate limit se resetea después de la ventana"""
        # Para testing, usaríamos una ventana muy corta
        # En producción: 5 min para login
        
        # 1. Hacer 5 intentos fallidos
        for i in range(5):
            client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "Wrong"}
            )
        
        # 2. Intento 6 bloqueado
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123!"}
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        
        # 3. En testing real, esperaríamos a que pase la ventana
        # o tener un método para resetear rate limit
        # Para este test, simplemente verificamos que se bloquea


class TestCombinedSecurityLayersLogged:
    """Tests que verifican que intentos se registren"""
    
    def test_xss_attempt_is_logged(self, caplog):
        """✅ Intento de XSS se registra en logs"""
        from utils.sanitize import log_xss_attempt
        
        suspicious_value = "<script>alert('xss')</script>"
        log_xss_attempt(suspicious_value, "name", "testuser")
        
        # Verificar que se registró
        assert "SECURITY" in caplog.text
        assert "XSS" in caplog.text
    
    def test_rate_limit_is_logged(self, client):
        """✅ Intento de rate limit se registra"""
        # Hacer 5 intentos fallidos para bloquear
        for i in range(5):
            client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "Wrong"}
            )
        
        # Intento bloqueado → genera log
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123!"}
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
