# 🚀 EMANTIX PRO — Guía de Instalación y Configuración

## ✅ Requisitos previos

- Python 3.9+
- SQL Server 2019+ (o SQL Server Express)
- ODBC Driver 17 para SQL Server

## 📋 Pasos de instalación

### 1. Clonar/Descargar el proyecto
```bash
cd /ruta/a/emantix_refactored/backend
```

### 2. Crear virtual environment
```bash
python -m venv venv
```

### 3. Activar virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

Copiar `.env.example` a `.env` y editar con tus valores:

```bash
cp .env.example .env
```

Editar `.env`:
```env
# Generar SECRET_KEY segura con:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=tu-clave-segura-aqui

# Database
DB_SERVER=tu-servidor
DB_NAME=EmantixDB
DB_USER=sa
DB_PASSWORD=tu-password

# SMTP (opcional)
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password

# CORS - Dominio del frontend
CORS_ORIGINS=http://localhost:5173,https://emantix.miempresa.com

# DEBUG (solo en desarrollo)
DEBUG=True
```

### 6. Inicializar base de datos
```bash
python -c "from database import init_db; init_db(); print('✅ BD inicializada')"
```

### 7. Ejecutar servidor
```bash
python main.py
```

O con uvicorn directamente:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## 🔐 Consideraciones de Seguridad

### ✅ QUÉ CAMBIÓ (FASE 1)

1. **JWT Seguro**
   - Se usa PyJWT oficial en lugar de implementación manual
   - Tokens con expiración automática
   - Validación correcta de firma

2. **Contraseñas**
   - Se usa bcrypt (salt automático, 12 rounds)
   - Reemplaza SHA-256 inseguro
   - Las contraseñas antiguas se migran al hacer login

3. **Variables de Entorno**
   - Todas las credenciales en `.env` (NO en código)
   - `.env` está en `.gitignore`
   - Valores por defecto seguros

4. **CORS**
   - Configuración específica por origen
   - No permite `"*"` (all origins)
   - Métodos limitados (GET, POST, PATCH, DELETE)

5. **Manejo de Errores**
   - Errores genéricos en producción (no expone internals)
   - Logging detallado en servidor
   - SIN stack traces en respuesta al cliente

6. **Autenticación**
   - Protección contra brute force (bloqueo tras 5 intentos)
   - Timeout de bloqueo configurable (por defecto 5 minutos)
   - Email enmascarado en respuestas

7. **Autorización**
   - `get_current_user()` para rutas autenticadas
   - `get_current_admin_user()` para rutas admin-only
   - `get_current_tecnico_user()` para técnicos+

## 📁 Estructura Modular

```
backend/
├── config.py              # Configuración (de .env)
├── security.py            # JWT, bcrypt, validación
├── database.py            # Modelos SQLAlchemy
├── deps.py                # Dependencias (Depends)
├── main.py                # App FastAPI (limpio)
├── routes/
│   ├── auth.py           # Login, reset password
│   ├── users.py          # CRUD usuarios (admin)
│   ├── manuals.py        # PDFs (próximo)
│   └── ... (más módulos)
├── schemas/
│   ├── auth.py           # Pydantic models
│   └── ... (más schemas)
├── services/
│   ├── email.py          # Envío de emails
│   ├── excel.py          # Procesamiento Excel (próximo)
│   └── file.py           # Validación de archivos (próximo)
└── .env.example           # Plantilla de configuración
```

## 🔑 Cambios en Autenticación

### Antes (Inseguro)
```python
SECRET_KEY = "emantix-pro-2025-change-in-production"  # ❌ En código
JWT = crear_manualmente_sin_librerias()  # ❌ Vulnerabilidades
password = hashlib.sha256(p).hexdigest()  # ❌ Sin salt
```

### Después (Seguro)
```python
SECRET_KEY = os.getenv("SECRET_KEY")  # ✅ Desde .env
JWT = jwt.encode(payload, settings.secret_key, algorithm)  # ✅ PyJWT oficial
password = bcrypt.hashpw(p.encode(), bcrypt.gensalt(12))  # ✅ Con salt
```

## 📚 Endpoints Implementados (FASE 1)

### Autenticación
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Usuario actual
- `POST /api/auth/forgot-password` - Solicitar reset
- `POST /api/auth/verify-code` - Verificar código
- `POST /api/auth/reset-password` - Cambiar contraseña

### Usuarios (admin only)
- `GET /api/users` - Listar usuarios
- `POST /api/users` - Crear usuario
- `PATCH /api/users/{username}/toggle` - Activar/Bloquear
- `DELETE /api/users/{username}` - Eliminar usuario

### Sistema
- `GET /health` - Health check
- `GET /` - Información de API

## 🧪 Pruebas Rápidas

### 1. Health check
```bash
curl http://localhost:8000/health
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"tu-password"}'
```

### 3. Obtener usuario actual (necesita token)
```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

## ⚙️ Configuración Avanzada

### Requisitos de Contraseña
Editar `.env`:
```env
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=True
PASSWORD_REQUIRE_NUMBER=True
PASSWORD_REQUIRE_SPECIAL=False
```

### JWT Tokens
```env
ACCESS_TOKEN_EXPIRE_MINUTES=15    # Token de acceso (corto)
REFRESH_TOKEN_EXPIRE_DAYS=7       # Refresh token (largo)
```

### Base de Datos
```env
DB_POOL_SIZE=20          # Conexiones en el pool
DB_MAX_OVERFLOW=10       # Conexiones adicionales
DB_POOL_RECYCLE=3600     # Reciclar cada hora
```

### Email
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu@gmail.com
SMTP_PASSWORD=tu-app-password  # Usar "App Password" de Google
```

## 🚨 Problemas Comunes

### "ModuleNotFoundError: No module named 'X'"
```bash
pip install -r requirements.txt
```

### "Authentication failed for user 'sa'"
Verificar credenciales en `.env` y que SQL Server esté corriendo

### "ODBC Driver 17 for SQL Server not found"
Instalar ODBC Driver:
- **Windows**: Descargar desde https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
- **Linux**: `sudo apt install msodbcsql17`

### "Address already in use"
El puerto 8000 ya está en uso. Cambiar:
```bash
python main.py --port 8001
```

## 📝 Próximos Pasos

- **FASE 2**: Refactorizar rutas de archivos (PDF, Excel)
- **FASE 3**: Implementar caché y paginación
- **FASE 4**: Docker + Nginx
- **FASE 5**: CI/CD y deployment

## 📞 Soporte

Cualquier duda con la refactorización, revisar los logs:
```bash
tail -f logs/emantix.log
```

O ejecutar en modo debug:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```
