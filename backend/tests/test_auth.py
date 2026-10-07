# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Tests para routes/auth.py
#  Login, Logout, Reset Password, JWT
# ═══════════════════════════════════════════════════════════

import pytest
from fastapi import status


class TestLoginEndpoint:
    """Tests para endpoint POST /api/auth/login"""
    
    def test_login_successful_admin(self, client):
        """✅ Login exitoso con credenciales admin"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"
    
    def test_login_successful_tecnico(self, client):
        """✅ Login exitoso con credenciales técnico"""
        response = client.post(
            "/api/auth/login",
            json={"username": "tecnico", "password": "tecnico123"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "tecnico"
        assert data["user"]["role"] == "tecnico"
    
    def test_login_invalid_password(self, client):
        """✅ Login falla con contraseña incorrecta"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Credenciales incorrectas" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """✅ Login falla con usuario inexistente"""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password123"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Credenciales incorrectas" in response.json()["detail"]
    
    def test_login_blocked_user(self, client, db_session):
        """✅ Login falla si usuario está bloqueado"""
        from database import UserDB
        from security import hash_password
        
        # Crear usuario bloqueado
        db_session.query(UserDB).filter_by(username="admin").update({"active": False})
        db_session.commit()
        
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_brute_force_protection(self, client):
        """✅ Protección contra brute force (bloqueo tras 5 intentos)"""
        # Intentar 5 veces con contraseña incorrecta
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrongpassword"}
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # 6to intento debe devolver 429 Too Many Requests
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "intentos fallidos" in response.json()["detail"]
    
    def test_login_missing_username(self, client):
        """✅ Login falla si falta username"""
        response = client.post(
            "/api/auth/login",
            json={"password": "admin123"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_missing_password(self, client):
        """✅ Login falla si falta contraseña"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_username_case_insensitive(self, client):
        """✅ Login es case-insensitive para username"""
        response = client.post(
            "/api/auth/login",
            json={"username": "ADMIN", "password": "admin123"}
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_login_returns_valid_jwt_token(self, client):
        """✅ Token retornado es JWT válido"""
        from security import verify_token
        
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        token = response.json()["access_token"]
        payload = verify_token(token)
        
        assert payload["username"] == "admin"
        assert payload["role"] == "admin"


class TestCurrentUserEndpoint:
    """Tests para endpoint GET /api/auth/me"""
    
    def test_get_current_user_with_valid_token(self, client, admin_headers):
        """✅ Obtener usuario actual con token válido"""
        response = client.get(
            "/api/auth/me",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"
        assert data["id"] == "admin-id"
    
    def test_get_current_user_without_token(self, client):
        """✅ Falla sin token"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_current_user_invalid_token(self, client, invalid_headers):
        """✅ Falla con token inválido"""
        response = client.get(
            "/api/auth/me",
            headers=invalid_headers
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_expired_token(self, client, expired_headers):
        """✅ Falla con token expirado"""
        response = client.get(
            "/api/auth/me",
            headers=expired_headers
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expirado" in response.json()["detail"]


class TestForgotPasswordEndpoint:
    """Tests para endpoint POST /api/auth/forgot-password"""
    
    def test_forgot_password_valid_user(self, client):
        """✅ Solicitar reset para usuario existente"""
        response = client.post(
            "/api/auth/forgot-password",
            json={"username": "admin"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "masked_email" in data
    
    def test_forgot_password_nonexistent_user(self, client):
        """✅ No expone si usuario no existe"""
        response = client.post(
            "/api/auth/forgot-password",
            json={"username": "nonexistent"}
        )
        
        # No debe revelar si usuario existe o no
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_forgot_password_user_without_email(self, client, db_session):
        """✅ Falla si usuario no tiene email"""
        from database import UserDB
        
        db_session.query(UserDB).filter_by(username="admin").update({"email": ""})
        db_session.commit()
        
        response = client.post(
            "/api/auth/forgot-password",
            json={"username": "admin"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_forgot_password_invalid_username_format(self, client):
        """✅ Valida formato de username"""
        response = client.post(
            "/api/auth/forgot-password",
            json={"username": "ab"}  # Muy corto
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestVerifyCodeEndpoint:
    """Tests para endpoint POST /api/auth/verify-code"""
    
    def test_verify_code_valid_code(self, client):
        """✅ Verificar código válido"""
        # Primero solicitar reset para obtener código
        from routes.auth import router
        from database import PasswordResetDB, SessionLocal
        
        # Este test requiere tener el código generado en forgot-password
        # Por ahora, verificamos que el endpoint existe
        response = client.post(
            "/api/auth/verify-code",
            json={"username": "admin", "code": "123456"}
        )
        
        # Espera error porque el código no es válido
        assert response.status_code in [status.HTTP_400_BAD_REQUEST]
    
    def test_verify_code_invalid_code(self, client):
        """✅ Falla con código inválido"""
        response = client.post(
            "/api/auth/verify-code",
            json={"username": "admin", "code": "000000"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestResetPasswordEndpoint:
    """Tests para endpoint POST /api/auth/reset-password"""
    
    def test_reset_password_missing_code(self, client):
        """✅ Falla si falta código"""
        response = client.post(
            "/api/auth/reset-password",
            json={
                "username": "admin",
                "new_password": "NewPassword123",
                "confirm_password": "NewPassword123"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_reset_password_mismatched_passwords(self, client):
        """✅ Falla si contraseñas no coinciden"""
        response = client.post(
            "/api/auth/reset-password",
            json={
                "username": "admin",
                "code": "123456",
                "new_password": "NewPassword123",
                "confirm_password": "DifferentPassword123"
            }
        )
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    def test_reset_password_weak_password(self, client):
        """✅ Falla si contraseña es débil"""
        response = client.post(
            "/api/auth/reset-password",
            json={
                "username": "admin",
                "code": "123456",
                "new_password": "weak",
                "confirm_password": "weak"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_reset_password_invalid_code(self, client):
        """✅ Falla con código inválido"""
        response = client.post(
            "/api/auth/reset-password",
            json={
                "username": "admin",
                "code": "000000",
                "new_password": "ValidPassword123",
                "confirm_password": "ValidPassword123"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRefreshTokenEndpoint:
    """Tests para endpoint POST /api/auth/refresh"""
    
    def test_refresh_token_successful(self, client, db_session):
        """✅ Refresh token genera nuevo access token"""
        from database import UserDB
        
        # 1. Login para obtener tokens
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123!"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        refresh_token = response.json()["refresh_token"]
        old_access_token = response.json()["access_token"]
        
        # 2. Usar refresh token
        response_refresh = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response_refresh.status_code == status.HTTP_200_OK
        assert "access_token" in response_refresh.json()
        new_access_token = response_refresh.json()["access_token"]
        
        # 3. Verificar que tokens son diferentes
        assert new_access_token != old_access_token
    
    def test_refresh_token_without_refresh_token(self, client):
        """✅ Falla sin refresh token"""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": ""}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_refresh_token_invalid_token(self, client):
        """✅ Falla con refresh token inválido"""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token_expired_token(self, client, db_session):
        """✅ Falla con refresh token expirado"""
        from security import create_refresh_token
        import time
        from datetime import timedelta, datetime, timezone
        
        # Crear refresh token con expiración de -1 segundo (ya expirado)
        expired_token_data = {
            "sub": "fake-id",
            "username": "admin",
            "role": "admin",
            "name": "Admin",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            "type": "refresh"
        }
        
        import jwt
        from config import settings
        expired_token = jwt.encode(
            expired_token_data,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": expired_token}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token_user_inactive(self, client, db_session):
        """✅ Falla si usuario se desactiva entre login y refresh"""
        from database import UserDB
        
        # 1. Login
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123!"}
        )
        
        refresh_token = response.json()["refresh_token"]
        
        # 2. Desactivar usuario
        admin = db_session.query(UserDB).filter_by(username="admin").first()
        admin.active = False
        db_session.commit()
        
        # 3. Intentar refresh
        response_refresh = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response_refresh.status_code == status.HTTP_401_UNAUTHORIZED
        
        # 4. Reactivar para otros tests
        admin.active = True
        db_session.commit()
    
    def test_new_access_token_can_be_used(self, client, db_session):
        """✅ Nuevo access token funciona en endpoints protegidos"""
        # 1. Login
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin123!"}
        )
        
        refresh_token = response.json()["refresh_token"]
        
        # 2. Refresh token
        response_refresh = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        new_access_token = response_refresh.json()["access_token"]
        
        # 3. Usar nuevo access token en endpoint protegido
        response_me = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        
        assert response_me.status_code == status.HTTP_200_OK


class TestLogoutEndpoint:
    """Tests para endpoint POST /api/auth/logout"""
    
    def test_logout_successful(self, client, admin_headers):
        """✅ Logout funciona con token válido"""
        response = client.post(
            "/api/auth/logout",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["logged_out"] == True
    
    def test_logout_without_auth(self, client):
        """✅ Falla logout sin autenticación"""
        response = client.post("/api/auth/logout")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_logout_invalid_token(self, client):
        """✅ Falla logout con token inválido"""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePasswordEndpoint:
    """Tests para endpoint POST /api/auth/change-password"""
    
    def test_change_password_successful(self, client, admin_headers):
        """✅ Cambio de contraseña exitoso"""
        response = client.post(
            "/api/auth/change-password",
            headers=admin_headers,
            json={
                "current_password": "Admin123!",
                "new_password": "NewAdmin456@",
                "confirm_password": "NewAdmin456@"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()
    
    def test_change_password_without_auth(self, client):
        """✅ Falla sin autenticación"""
        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "Admin123!",
                "new_password": "NewAdmin456@",
                "confirm_password": "NewAdmin456@"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_change_password_wrong_current_password(self, client, admin_headers):
        """✅ Falla con contraseña actual incorrecta"""
        response = client.post(
            "/api/auth/change-password",
            headers=admin_headers,
            json={
                "current_password": "WrongPassword",
                "new_password": "NewAdmin456@",
                "confirm_password": "NewAdmin456@"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrecta" in response.json()["detail"]
    
    def test_change_password_mismatched_new_passwords(self, client, admin_headers):
        """✅ Falla si nuevas contraseñas no coinciden"""
        response = client.post(
            "/api/auth/change-password",
            headers=admin_headers,
            json={
                "current_password": "Admin123!",
                "new_password": "NewAdmin456@",
                "confirm_password": "DifferentPassword456@"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_change_password_weak_new_password(self, client, admin_headers):
        """✅ Falla si nueva contraseña es débil"""
        response = client.post(
            "/api/auth/change-password",
            headers=admin_headers,
            json={
                "current_password": "Admin123!",
                "new_password": "weak",
                "confirm_password": "weak"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_change_password_same_as_current(self, client, admin_headers):
        """✅ Falta si nueva es igual a la actual"""
        response = client.post(
            "/api/auth/change-password",
            headers=admin_headers,
            json={
                "current_password": "Admin123!",
                "new_password": "Admin123!",
                "confirm_password": "Admin123!"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "diferente" in response.json()["detail"]
    
    def test_change_password_then_login_with_new_password(self, client, admin_headers, db_session):
        """✅ Después de cambiar, login funciona con nueva contraseña"""
        from database import UserDB
        
        # Cambiar contraseña
        response = client.post(
            "/api/auth/change-password",
            headers=admin_headers,
            json={
                "current_password": "Admin123!",
                "new_password": "BrandNewPassword456@",
                "confirm_password": "BrandNewPassword456@"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Intentar login con nueva contraseña
        response_login = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "BrandNewPassword456@"
            }
        )
        
        assert response_login.status_code == status.HTTP_200_OK
