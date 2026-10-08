# EMANTIC PRO v4.0 — Plataforma Centralizada de Gestión Empresarial

**Sistema seguro, escalable y de alto rendimiento para la centralización de información empresarial, organización de manuales de mantenimiento y gestión de datos operativos**

## Tabla de Contenidos

1. [Descripción](#descripción)
2. [Características Principales](#características-principales)
3. [Tecnologías](#tecnologías)
4. [Requisitos](#requisitos)
5. [Instalación](#instalación)
6. [Configuración](#configuración)
7. [Tests](#tests)
8. [Despliegue](#despliegue)
9. [Troubleshooting](#troubleshooting)

---

## Descripción

**EMANTIC PRO** es una plataforma integral de gestión técnica de flotas vehiculares que centraliza información de mantenimiento, reportes de campo, indicadores de desempeño y documentación técnica.

### Características Clave
- . Autenticación JWT segura con refresh tokens
- . Control de acceso basado en roles (RBAC)
- . Dashboard con estadísticas en tiempo real
- . Carga de datos Excel con validación
- . Almacenamiento de manuales PDF
- . Análisis de flota (DPV, ICO, disponibilidad)
- . Rate limiting anti-brute force
- . Sanitización XSS
- . Imágenes optimizadas (65% reducción)
- . Frontend responsive

--

## Tecnologías

- **Backend:** Python 3.12, FastAPI, SQLAlchemy
- **Base de datos:** SQL Server 2019+
- **Frontend:** Vue 3, Vite, Axios
- **DevOps:** Docker, Nginx, pytest

--

## Requisitos

- Python 3.12+
- Node.js 18+
- SQL Server 2019+
- 4GB RAM, 5GB disco

---

## Instalación Rápida

### Backend
```bash
cd backend
python -m venv venv_new
source venv_new/bin/activate              # En Windows: venv_new\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Editar .env con credenciales SQL Server
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Configuración (.env)

```env
# Base de Datos
DB_SERVER=localhost
DB_USER=admin
DB_PASSWORD=tu_contraseña
DB_NAME=EMANTIC

# Seguridad
SECRET_KEY=generar-nuevo-con-secrets.token_urlsafe(32)
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:5173"]

# App
DEBUG=True  # False en producción
APP_VERSION=4.0
```

---

##  Tests

```bash
cd backend
pytest tests/ -v
```

---

## Despliegue

### Docker
```bash
docker-compose up -d
```

### Servidor Ubuntu
Ver sección completa en README.md 

---

