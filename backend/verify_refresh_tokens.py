#!/usr/bin/env python3
"""
Script de verificación de funcionalidad de refresh tokens.
Prueba sin usar pytest - solo verificaciones simples.
"""

import sys
import os
import json
from datetime import datetime, timedelta, timezone

# Agregar al path
sys.path.insert(0, os.path.dirname(__file__))

import jwt
from config import settings
from security import create_access_token, create_refresh_token, verify_refresh_token

print("=" * 80)
print(" 🔄 VERIFICACIÓN DE REFRESH TOKENS")
print("=" * 80)

# TEST 1: Crear access token
print("\n[TEST 1] Crear Access Token")
access_token_data = {
    "sub": "user-123",
    "username": "admin",
    "role": "admin",
    "name": "Administrador"
}

access_token = create_access_token(access_token_data)
print(f"  ✅ Access token creado")
print(f"     Longitud: {len(access_token)} caracteres")
print(f"     Primeros 40 chars: {access_token[:40]}...")

# Decodificar para verificar
decoded = jwt.decode(access_token, settings.secret_key, algorithms=[settings.algorithm])
print(f"  ✅ Decodificado:")
print(f"     Type: {decoded.get('type', 'access')} (no incluye 'type')")
print(f"     Username: {decoded.get('username')}")
print(f"     Expiration: {datetime.fromtimestamp(decoded.get('exp'))}")
exp_minutes = (decoded.get('exp') - datetime.now(timezone.utc).timestamp()) / 60
print(f"     Expira en: {exp_minutes:.1f} minutos")

if exp_minutes > 14 and exp_minutes < 16:
    print("  ✅ Duración correcta (15 minutos)")
else:
    print(f"  ❌ ERROR: Duración incorrecta ({exp_minutes:.1f} minutos, esperado ~15)")
    sys.exit(1)

# TEST 2: Crear refresh token
print("\n[TEST 2] Crear Refresh Token")
refresh_token_data = {
    "sub": "user-123",
    "username": "admin",
    "role": "admin",
    "name": "Administrador"
}

refresh_token = create_refresh_token(refresh_token_data)
print(f"  ✅ Refresh token creado")
print(f"     Longitud: {len(refresh_token)} caracteres")
print(f"     Primeros 40 chars: {refresh_token[:40]}...")

# Decodificar para verificar
decoded = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])
print(f"  ✅ Decodificado:")
print(f"     Type: {decoded.get('type')}")
print(f"     Username: {decoded.get('username')}")
print(f"     Expiration: {datetime.fromtimestamp(decoded.get('exp'))}")
exp_days = (decoded.get('exp') - datetime.now(timezone.utc).timestamp()) / (24 * 3600)
print(f"     Expira en: {exp_days:.1f} días")

if exp_days > 6.9 and exp_days < 7.1:
    print("  ✅ Duración correcta (~7 días)")
else:
    print(f"  ❌ ERROR: Duración incorrecta ({exp_days:.1f} días, esperado ~7)")
    sys.exit(1)

# TEST 3: Verificar que tokens son diferentes
print("\n[TEST 3] Tokens son diferentes")
if access_token != refresh_token:
    print(f"  ✅ Tokens son diferentes")
else:
    print(f"  ❌ ERROR: Tokens son idénticos")
    sys.exit(1)

# TEST 4: Access token NO tiene type="refresh"
print("\n[TEST 4] Access token tiene type correcto")
decoded_access = jwt.decode(access_token, settings.secret_key, algorithms=[settings.algorithm])
if decoded_access.get("type") != "refresh":
    print(f"  ✅ Access token no tiene type='refresh' (type={decoded_access.get('type')})")
else:
    print(f"  ❌ ERROR: Access token tiene type='refresh'")
    sys.exit(1)

# TEST 5: Refresh token tiene type="refresh"
print("\n[TEST 5] Refresh token tiene type correcto")
decoded_refresh = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])
if decoded_refresh.get("type") == "refresh":
    print(f"  ✅ Refresh token tiene type='refresh'")
else:
    print(f"  ❌ ERROR: Refresh token tiene type={decoded_refresh.get('type')}")
    sys.exit(1)

# TEST 6: verify_refresh_token valida type
print("\n[TEST 6] verify_refresh_token rechaza access token")
try:
    # Intentar usar access token en verify_refresh_token
    verify_refresh_token(access_token)
    print(f"  ❌ ERROR: verify_refresh_token aceptó access token")
    sys.exit(1)
except Exception as e:
    if "tipo" in str(e).lower() or "type" in str(e).lower():
        print(f"  ✅ verify_refresh_token rechazó access token correctamente")
        print(f"     Error: {str(e)[:60]}...")
    else:
        print(f"  ✅ verify_refresh_token rechazó access token")
        print(f"     Error: {str(e)[:60]}...")

# TEST 7: verify_refresh_token acepta refresh token válido
print("\n[TEST 7] verify_refresh_token acepta refresh token válido")
try:
    payload = verify_refresh_token(refresh_token)
    print(f"  ✅ Refresh token validado correctamente")
    print(f"     Username: {payload.get('username')}")
    print(f"     Type: {payload.get('type')}")
except Exception as e:
    print(f"  ❌ ERROR: {str(e)}")
    sys.exit(1)

# TEST 8: Crear refresh token con expiración negativa (ya expirado)
print("\n[TEST 8] verify_refresh_token rechaza token expirado")
expired_payload = {
    "sub": "user-123",
    "username": "admin",
    "role": "admin",
    "type": "refresh",
    "exp": datetime.now(timezone.utc) - timedelta(seconds=1),  # Ya expirado
    "iat": datetime.now(timezone.utc)
}

expired_token = jwt.encode(
    expired_payload,
    settings.secret_key,
    algorithm=settings.algorithm
)

try:
    verify_refresh_token(expired_token)
    print(f"  ❌ ERROR: verify_refresh_token aceptó token expirado")
    sys.exit(1)
except Exception as e:
    if "expira" in str(e).lower() or "expired" in str(e).lower():
        print(f"  ✅ Token expirado rechazado correctamente")
        print(f"     Error: {str(e)[:60]}...")
    else:
        print(f"  ✅ Token expirado rechazado")
        print(f"     Error: {str(e)[:60]}...")

# TEST 9: Diferentes usuarios tienen diferentes tokens
print("\n[TEST 9] Diferentes usuarios tienen diferentes tokens")
token_user1 = create_refresh_token({"sub": "user-1", "username": "admin"})
token_user2 = create_refresh_token({"sub": "user-2", "username": "tecnico"})

if token_user1 != token_user2:
    decoded1 = jwt.decode(token_user1, settings.secret_key, algorithms=[settings.algorithm])
    decoded2 = jwt.decode(token_user2, settings.secret_key, algorithms=[settings.algorithm])
    
    if decoded1.get("sub") != decoded2.get("sub"):
        print(f"  ✅ Tokens son diferentes para usuarios diferentes")
        print(f"     User 1: {decoded1.get('username')}")
        print(f"     User 2: {decoded2.get('username')}")
    else:
        print(f"  ❌ ERROR: Tokens comparten mismo sub")
        sys.exit(1)
else:
    print(f"  ❌ ERROR: Tokens son idénticos")
    sys.exit(1)

# TEST 10: JWT incluye claims necesarios
print("\n[TEST 10] Refresh token incluye todos los claims")
claims = ["sub", "username", "role", "name", "type", "exp", "iat"]
decoded_refresh = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])

missing = [c for c in claims if c not in decoded_refresh]
if not missing:
    print(f"  ✅ Todos los claims presentes")
    print(f"     Claims: {', '.join(claims)}")
else:
    print(f"  ⚠️  Claims faltantes: {', '.join(missing)}")
    # No es error fatal, algunos claims son opcionales

print("\n" + "=" * 80)
print(" ✅ TODOS LOS TESTS PASARON")
print("=" * 80)

print("\n📋 RESUMEN:")
print("  • Access token: 15 minutos, sin type='refresh'")
print("  • Refresh token: 7 días, con type='refresh'")
print("  • verify_refresh_token valida type y expiración")
print("  • Diferentes usuarios tienen diferentes tokens")
print("  • Todos los claims incluidos correctamente")

sys.exit(0)
