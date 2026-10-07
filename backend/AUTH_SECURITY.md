# 🔐 EMANTIC PRO — POLÍTICA DE SEGURIDAD DE AUTENTICACIÓN

**Versión:** 1.0  
**Última actualización:** 30 de Agosto de 2026  
**Estado:** ✅ IMPLEMENTADO

---

## 📋 CONTENIDO

1. Política de contraseñas
2. Endpoints de autenticación
3. Flujos de seguridad
4. Configuración de email
5. Migración de usuarios existentes

---

## 🔐 POLÍTICA DE CONTRASEÑAS

### Requisitos de Fuerza

```
Longitud mínima:     8 caracteres
Mayúsculas:          Al menos 1 (A-Z)
Números:             Al menos 1 (0-9)
Caracteres especiales: Opcional (! @ # $ % ^ & * ( ) - _ = + [ ] { } | ; : , . < > ?)
```

### Hashing y Almacenamiento

```
Algoritmo:           bcrypt
Rounds:              12
Hash Length:         60 caracteres
Salt:                Incluido en hash
Versión bcrypt:      $2a$ / $2b$ / $2y$
```

**Ejemplo de hash almacenado:**
```
$2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ee6PVM9qc1E8Nm9i
```

### Verificación

```python
# Hasheado con bcrypt (12 rounds)
from security import hash_password, verify_password

# Al crear usuario
password_hash = hash_password("MyPassword123")

# Al verificar login
is_correct = verify_password("MyPassword123", password_hash)
```

---

## 🔑 ENDPOINTS DE AUTENTICACIÓN

### 1. LOGIN
**`POST /api/auth/login`**

```json
Request:
{
  "username": "admin",
  "password": "Admin123!"
}

Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user-123",
    "username": "admin",
    "name": "Administrador",
    "role": "admin",
    "email": "admin@emantix.com"
  }
}

Errores:
- 401: Credenciales incorrectas
- 429: Cuenta bloqueada (5+ intentos fallidos)
```

**Protección contra fuerza bruta:**
- Máximo 5 intentos fallidos
- Bloqueo por 5 minutos (300 segundos)
- Contador se resetea tras login exitoso

---

### 2. OBTENER USUARIO ACTUAL
**`GET /api/auth/me`**

```
Headers:
  Authorization: Bearer <token>

Response (200 OK):
{
  "id": "user-123",
  "username": "admin",
  "name": "Administrador",
  "role": "admin",
  "email": "admin@emantix.com"
}

Errores:
- 401: Token inválido o expirado
- 403: Sin autenticación
```

---

### 3. SOLICITAR RECUPERACIÓN DE CONTRASEÑA
**`POST /api/auth/forgot-password`**

```json
Request:
{
  "username": "admin"
}

Response (200 OK):
{
  "message": "Código enviado a ad***@emantix.com",
  "masked_email": "ad***@emantix.com"
}

Proceso:
1. Genera código de 6 dígitos
2. Valida que usuario existe y tiene email
3. Invalida códigos anteriores no usados
4. Envía email con código (válido 15 minutos)
5. Enmasca email en respuesta (privacidad)

Errores:
- 404: Usuario no encontrado
- 400: Usuario sin email registrado
- 500: Error al enviar email
```

---

### 4. VERIFICAR CÓDIGO DE RESET
**`POST /api/auth/verify-code`**

```json
Request:
{
  "username": "admin",
  "code": "123456"
}

Response (200 OK):
{
  "message": "Código válido",
  "valid": true
}

Errores:
- 400: Código inválido
- 400: Código expirado (> 15 minutos)
```

---

### 5. RESETEAR CONTRASEÑA
**`POST /api/auth/reset-password`**

```json
Request:
{
  "username": "admin",
  "code": "123456",
  "new_password": "NewPassword456@",
  "confirm_password": "NewPassword456@"
}

Response (200 OK):
{
  "message": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."
}

Validaciones:
- Código debe ser válido y no expirado
- Nuevas contraseñas deben coincidir
- Nueva contraseña debe cumplir requisitos
- Código se marca como usado

Errores:
- 400: Código inválido o expirado
- 400: Contraseñas no coinciden
- 400: Contraseña débil
- 404: Usuario no encontrado
```

---

### 6. CAMBIAR CONTRASEÑA (USUARIO AUTENTICADO)
**`POST /api/auth/change-password`**

```json
Request:
{
  "current_password": "Admin123!",
  "new_password": "NewPassword456@",
  "confirm_password": "NewPassword456@"
}

Headers:
  Authorization: Bearer <token>

Response (200 OK):
{
  "message": "Contraseña actualizada correctamente."
}

Validaciones:
- Usuario debe estar autenticado
- Contraseña actual debe ser correcta
- Nueva contraseña debe ser diferente de la actual
- Nueva contraseña debe cumplir requisitos
- Nuevas contraseñas deben coincidir

Errores:
- 401: Contraseña actual incorrecta
- 400: Nueva contraseña igual a la actual
- 400: Contraseña débil
- 403: Sin autenticación
```

---

## 🔄 FLUJOS DE SEGURIDAD

### Flujo: LOGIN NORMAL

```
Usuario escribe credenciales
        ↓
POST /api/auth/login
        ↓
Validar username/password no vacíos
        ↓
¿Cuenta bloqueada? → 429 Too Many Requests
        ↓
¿Usuario existe? → 401 Unauthorized
        ↓
¿Usuario activo? → 401 Unauthorized
        ↓
¿Contraseña correcta? (bcrypt verify)
  ✓ SÍ → Generar JWT, limpiar intentos → 200 OK
  ✗ NO → Registrar intento fallido → 401 Unauthorized
```

---

### Flujo: RECUPERACIÓN POR OLVIDO

```
Usuario olvidó contraseña
        ↓
POST /api/auth/forgot-password {username}
        ↓
¿Usuario existe con email? → 404 si no
        ↓
Generar código 6 dígitos
        ↓
Invalidar códigos anteriores no usados
        ↓
Guardar en table password_resets (15 min expiry)
        ↓
Enviar email con código
        ↓
POST /api/auth/verify-code {username, code}
        ↓
¿Código válido y no expirado?
  ✓ SÍ → 200 Código válido
  ✗ NO → 400 Inválido/expirado
        ↓
POST /api/auth/reset-password {username, code, new_password}
        ↓
Validar contraseña fuerte
        ↓
Hashear con bcrypt
        ↓
Actualizar usuario.password
        ↓
Marcar código como used
        ↓
✅ Contraseña resetada
```

---

### Flujo: CAMBIO DE CONTRASEÑA (USUARIO LOGUEADO)

```
Usuario autenticado quiere cambiar contraseña
        ↓
POST /api/auth/change-password {current, new, confirm}
  Headers: Authorization: Bearer <token>
        ↓
Validar token JWT
        ↓
¿Contraseña actual correcta? (bcrypt verify)
  ✗ NO → 401 Unauthorized
        ↓
¿Nueva diferente de actual? (bcrypt verify)
  ✗ NO → 400 Bad Request
        ↓
Validar nueva contraseña fuerte
        ↓
Validar new == confirm
        ↓
Hashear nueva con bcrypt
        ↓
Actualizar usuario.password
        ↓
✅ Contraseña actualizada
```

---

## 📧 CONFIGURACIÓN DE EMAIL

### Variables de Entorno (.env)

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com           # Server SMTP
SMTP_PORT=587                       # Puerto (587 = TLS, 465 = SSL)
SMTP_USER=tu-email@gmail.com       # Email remitente
SMTP_PASSWORD=app-password         # Contraseña de app (no personal)
SMTP_FROM=noreply@emantix.com     # Email de origen

# Para Gmail:
# 1. Habilitar autenticación en 2 factores
# 2. Generar "App Password"
# 3. Usar app password en SMTP_PASSWORD
```

### Ejemplo de Email de Reset

```
From: EMANTIC <noreply@emantix.com>
To: usuario@email.com
Subject: Código de recuperación de contraseña - EMANTIC

Hola Nombre,

Recibimos una solicitud para recuperar tu contraseña en EMANTIC.

Tu código de verificación es:

  ┌─────────────────┐
  │   123 456       │
  └─────────────────┘

Este código es válido por 15 minutos.

Si no solicitaste este cambio, ignora este email.

---
Sistema EMANTIC
```

---

## 🔄 MIGRACIÓN DE USUARIOS EXISTENTES

### Problema: Usuarios con contraseñas en SHA-256

Si tu sistema tiene usuarios con SHA-256:

```python
# Viejo (NO usar en nuevos usuarios)
import hashlib
def hash_pw(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()

# Nuevo (USAR siempre)
from security import hash_password
def hash_new(p: str) -> str:
    return hash_password(p)  # bcrypt
```

### Solución: Migración Gradual

**Opción 1: Forzar reset de contraseña**
```sql
-- Marcar todas las contraseñas como expiradas
UPDATE users SET password = '' WHERE password LIKE '%$2%' IS FALSE;

-- Usuarios intentarán login:
-- → Fallarán porque contraseña vacía
-- → Usar /api/auth/forgot-password
-- → Resetear con bcrypt
```

**Opción 2: Migración transparente en login**
```python
# En endpoint login:
if len(user.password) == 64:  # SHA-256 = 64 caracteres
    # Es SHA-256 antiguo
    if hashlib.sha256(password.encode()).hexdigest() == user.password:
        # Contraseña correcta, pero migrar a bcrypt
        user.password = hash_password(password)
        db.commit()
```

### Status de Usuarios de Prueba

| Usuario | Contraseña | Hash | Status |
|---------|-----------|------|--------|
| admin | Admin123! | bcrypt | ✅ Nuevo (v4.0) |
| tecnico1 | Tecnico123! | bcrypt | ✅ Nuevo (v4.0) |

---

## 📊 TABLA PASSWORD_RESETS

```sql
CREATE TABLE password_resets (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    code VARCHAR(6) NOT NULL,
    expires_at DATETIME NOT NULL,
    used BIT DEFAULT 0,
    created_at DATETIME DEFAULT GETUTCDATE()
);
```

**Limpieza automática:**
- Códigos expirados se pueden eliminar con:
```sql
DELETE FROM password_resets 
WHERE expires_at < GETUTCDATE() 
  AND used = 1;
```

---

## 🧪 PRUEBAS DE SEGURIDAD

### Test 1: Hashing Seguro

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123!"}'

# Verificar que retorna JWT válido
```

### Test 2: Brute Force Protection

```bash
# Intentar 6 logins fallidos
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"WrongPassword"}'
done

# 6to intento debe retornar 429
```

### Test 3: Change Password

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123!"}' \
  | jq -r '.access_token')

# 2. Cambiar contraseña
curl -X POST http://localhost:8000/api/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "Admin123!",
    "new_password": "NewPassword456@",
    "confirm_password": "NewPassword456@"
  }'

# 3. Verificar que login con nueva contraseña funciona
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"NewPassword456@"}'
```

---

## 📋 CHECKLIST DE SEGURIDAD

- [x] Contraseñas hasheadas con bcrypt (12 rounds)
- [x] Protección contra brute force (5 intentos, 5 min bloqueo)
- [x] Validación de fuerza de contraseña
- [x] Cambio de contraseña para usuario autenticado
- [x] Recuperación de contraseña por email
- [x] Códigos de reset de un solo uso
- [x] Códigos temporales (15 minutos)
- [x] Email enmascarado en respuesta
- [x] JWT tokens con expiración (15 min)
- [x] Refresh tokens (7 días)
- [x] SMTP configurado
- [x] Logging de intentos fallidos
- [x] Validación en frontend + backend

---

**Documento actualizado:** 30 de Agosto de 2026  
**Versión:** EMANTIC PRO v4.0
