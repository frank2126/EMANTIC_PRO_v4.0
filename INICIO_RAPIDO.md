# 🚀 EMANTIC PRO v4.0 — INICIO RÁPIDO

## Instalación (5 minutos)

### 1. Requisitos
- Python 3.12+
- Node.js 18+
- SQL Server 2019+

### 2. Instalación Automática
```bash
chmod +x install.sh
./install.sh
```

### 3. Configurar Base de Datos
```bash
nano backend/.env

# Editar:
DB_SERVER=tu-servidor-sql
DB_USER=tu-usuario
DB_PASSWORD=tu-contraseña
```

### 4. Iniciar Servicios

**Terminal 1 - Backend:**
```bash
cd backend
source venv_new/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Acceder
```
http://localhost:5173

Usuario: admin
Contraseña: Admin123!
```

## Docker (Alternativa)
```bash
docker-compose up -d
```

## Tests
```bash
cd backend
pytest tests/ -v
```

## Estructura
```
EMANTIC_PRO_v4.0/
├── backend/          (FastAPI + Python)
├── frontend/         (Vue 3 + Vite)
├── docker-compose.yml
├── nginx.conf
├── README.md
└── install.sh
```

## Documentación
- README.md — Guía completa
- backend/.env.example — Variables
- INICIO_RAPIDO.md — Este archivo

## ¿Problemas?
Ver README.md → Troubleshooting

