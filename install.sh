#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         EMANTIC PRO v4.0 — Script de Instalación          ║"
echo "╚════════════════════════════════════════════════════════════╝"

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Función para imprimir
print_step() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Verificar requisitos
echo ""
echo "Verificando requisitos..."

if ! command -v python3.12 &> /dev/null; then
    print_error "Python 3.12 no encontrado"
    exit 1
fi
print_step "Python 3.12 encontrado"

if ! command -v npm &> /dev/null; then
    print_error "npm no encontrado"
    exit 1
fi
print_step "npm encontrado"

# Backend
echo ""
echo "Configurando backend..."

cd backend

if [ ! -d "venv_new" ]; then
    print_step "Creando entorno virtual..."
    python3.12 -m venv venv_new
else
    print_step "Entorno virtual ya existe"
fi

source venv_new/bin/activate

print_step "Instalando dependencias..."
pip install --quiet -r requirements.txt

if [ ! -f ".env" ]; then
    print_step "Creando .env..."
    cp .env.example .env
    print_warning "Por favor editar .env con las credenciales de SQL Server"
else
    print_step ".env ya existe"
fi

print_step "Backend configurado"

# Frontend
echo ""
echo "Configurando frontend..."

cd ../frontend

print_step "Instalando dependencias npm..."
npm install --quiet

if [ ! -f ".env" ]; then
    echo "VITE_API_BASE_URL=http://localhost:8000" > .env
    print_step "Creado .env frontend"
fi

print_step "Frontend configurado"

# Resumen
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Instalación Completada"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Editar las credenciales SQL Server:"
echo "   nano backend/.env"
echo ""
echo "2. Iniciar el backend:"
echo "   cd backend"
echo "   source venv_new/bin/activate"
echo "   python main.py"
echo ""
echo "3. En otra terminal, iniciar el frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. Acceder a http://localhost:5173"
echo ""

cd ..
