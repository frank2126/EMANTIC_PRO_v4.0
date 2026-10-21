#  Autenticación
#  Validación segura de datos de entrada/salida

from pydantic import BaseModel, Field, validator
from typing import Optional
from security import validate_username, validate_password_strength, get_password_error_message
from utils.sanitize import sanitize_string, sanitize_email


# ── LOGIN ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    """Esquema para login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1)
    
    @validator('username')
    def validate_username_field(cls, v):
        if not validate_username(v):
            raise ValueError("Username inválido")
        return v.lower()


class LoginResponse(BaseModel):
    """Esquema de respuesta de login"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


# ── REFRESH TOKEN ──────────────────────────────────────
class RefreshTokenRequest(BaseModel):
    """Solicitar nuevo access token con refresh token"""
    refresh_token: str = Field(..., min_length=1)


class RefreshTokenResponse(BaseModel):
    """Respuesta de refresh token"""
    access_token: str
    token_type: str = "bearer"


# ── USUARIO ACTUAL ────────────────────────────────────
class CurrentUserResponse(BaseModel):
    """Información del usuario actual"""
    id: str
    username: str
    name: str
    role: str
    email: Optional[str] = None


# ── RESET DE CONTRASEÑA ───────────────────────────────
class ForgotPasswordRequest(BaseModel):
    """Solicitar reset de contraseña"""
    username: str = Field(..., min_length=3, max_length=50)
    
    @validator('username')
    @classmethod
    def validate_username_field(cls, v):
        return v.lower()


class VerifyCodeRequest(BaseModel):
    """Verificar código de reset"""
    username: str = Field(..., min_length=3)
    code: str = Field(..., min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    """Reset de contraseña con código"""
    username: str = Field(..., min_length=3)
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    @classmethod
    def validate_password(cls, v):
        validation = validate_password_strength(v)
        error_msg = get_password_error_message(validation)
        if error_msg:
            raise ValueError(error_msg)
        return v
    
    @validator('confirm_password')
    @classmethod
    def validate_confirm(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError("Las contraseñas no coinciden")
        return v


# ── CREAR USUARIO ──────────────────────────────────────
class CreateUserRequest(BaseModel):
    """Crear nuevo usuario (admin solo)"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[str] = None
    role: str = Field(default="tecnico")
    
    @validator('username')
    @classmethod
    def validate_username_field(cls, v):
        if not validate_username(v):
            raise ValueError("Username inválido")
        return v.lower()
    
    @validator('name')
    @classmethod
    def sanitize_name(cls, v):
        """Sanitizar nombre de usuario (prevenir XSS)"""
        if not v:
            raise ValueError("Nombre requerido")
        v = sanitize_string(v, max_length=200)
        return v
    
    @validator('password')
    @classmethod
    def validate_password_field(cls, v):
        validation = validate_password_strength(v)
        error_msg = get_password_error_message(validation)
        if error_msg:
            raise ValueError(error_msg)
        return v
    
    @validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ["admin", "tecnico"]:
            raise ValueError("Rol debe ser 'admin' o 'tecnico'")
        return v
    
    @validator('email')
    @classmethod
    def validate_email_field(cls, v):
        if v:
            if "@" not in v:
                raise ValueError("Email inválido")
            v = v.lower().strip()
        return v


# ── CAMBIO DE CONTRASEÑA ───────────────────────────
class ChangePasswordRequest(BaseModel):
    """Cambiar contraseña para usuario autenticado"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    @classmethod
    def validate_password(cls, v):
        validation = validate_password_strength(v)
        error_msg = get_password_error_message(validation)
        if error_msg:
            raise ValueError(error_msg)
        return v
    
    @validator('confirm_password')
    @classmethod
    def validate_confirm(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError("Las contraseñas no coinciden")
        return v


class UserResponse(BaseModel):
    """Información de usuario para respuestas"""
    id: str
    username: str
    name: str
    email: Optional[str] = None
    role: str
    active: bool
    created_at: str
    
    class Config:
        orm_mode = True
