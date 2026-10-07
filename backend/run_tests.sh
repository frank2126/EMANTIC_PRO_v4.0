#!/bin/bash

# EMANTIX PRO — Script de Ejecución de Tests

set -e

echo "═══════════════════════════════════════════════════════════"
echo "🧪 EMANTIX PRO — EJECUCIÓN DE TESTS FASE 2"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Detectar sistema operativo
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    PYTHON="python"
    VENV="venv\\Scripts\\activate"
else
    PYTHON="python3"
    VENV="venv/bin/activate"
fi

# Verificar si existe venv
if [ ! -d "venv" ] && [ ! -d "venv_new" ]; then
    echo "❌ Virtual environment no encontrado"
    echo "Por favor, crea un venv primero:"
    echo "  $PYTHON -m venv venv"
    echo "  source $VENV"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo "📦 Verificando dependencias..."

# Verificar pytest
if ! $PYTHON -c "import pytest" 2>/dev/null; then
    echo "❌ pytest no está instalado"
    echo "Instalando pytest..."
    $PYTHON -m pip install pytest pytest-asyncio httpx -q
fi

echo "✅ Dependencias verificadas"
echo ""

# Ejecutar pytest con salida detallada
echo "🚀 Ejecutando tests..."
echo ""

$PYTHON -m pytest tests/ -v --tb=short --color=yes --no-header 2>&1 | tee test_results.txt

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "📊 Resumen de Resultados"
echo "═══════════════════════════════════════════════════════════"

# Extraer estadísticas
PASSED=$(grep -c "PASSED" test_results.txt || echo "0")
FAILED=$(grep -c "FAILED" test_results.txt || echo "0")
ERRORS=$(grep -c "ERROR" test_results.txt || echo "0")
SKIPPED=$(grep -c "SKIPPED" test_results.txt || echo "0")

echo "✅ Tests exitosos: $PASSED"
echo "❌ Tests fallidos: $FAILED"
echo "⚠️  Errores: $ERRORS"
echo "⏭️  Saltados: $SKIPPED"
echo ""

# Calcular total
TOTAL=$((PASSED + FAILED + ERRORS + SKIPPED))
echo "📈 Total de tests ejecutados: $TOTAL"

if [ "$FAILED" -eq 0 ] && [ "$ERRORS" -eq 0 ]; then
    echo ""
    echo "🎉 ¡TODOS LOS TESTS PASARON!"
    exit 0
else
    echo ""
    echo "⚠️  Hay tests que fallaron o tuvieron errores"
    exit 1
fi
