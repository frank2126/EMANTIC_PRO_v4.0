#!/usr/bin/env python3
"""
Script manual para verificar funcionalidad de autenticación y cambio de contraseña.
No requiere pytest - usa verificaciones simples.
"""

import sys
import os

# Agregar al path
sys.path.insert(0, os.path.dirname(__file__))

from security import hash_password, verify_password, validate_password_strength, get_password_error_message

print("=" * 70)
print(" 🔐 VERIFICACIÓN DE SEGURIDAD DE AUTENTICACIÓN")
print("=" * 70)

# TEST 1: Hashing de contraseña
print("\n[TEST 1] Hashing con bcrypt")
password = "Admin123!"
hashed = hash_password(password)
print(f"  Password: {password}")
print(f"  Hash:     {hashed}")
print(f"  Tipo:     {type(hashed)}")
print(f"  Longitud: {len(hashed)}")

# Verificar que es bcrypt (comienza con $2)
if hashed.startswith("$2"):
    print("  ✅ Formato bcrypt correcto")
else:
    print(f"  ❌ ERROR: No es bcrypt (comienza con {hashed[:2]})")
    sys.exit(1)

# TEST 2: Verificación de contraseña
print("\n[TEST 2] Verificación de contraseña")
is_correct = verify_password(password, hashed)
is_wrong = verify_password("WrongPassword", hashed)

if is_correct:
    print(f"  ✅ Contraseña correcta verifica como TRUE")
else:
    print(f"  ❌ ERROR: Contraseña correcta verifica como FALSE")
    sys.exit(1)

if not is_wrong:
    print(f"  ✅ Contraseña incorrecta verifica como FALSE")
else:
    print(f"  ❌ ERROR: Contraseña incorrecta verifica como TRUE")
    sys.exit(1)

# TEST 3: Validación de fuerza
print("\n[TEST 3] Validación de fuerza de contraseña")

test_passwords = [
    ("weak", False, "muy corta"),
    ("WeakPass", False, "sin números"),
    ("12345678", False, "sin mayúsculas"),
    ("Admin123!", True, "fuerza correcta"),
    ("SecurePassword123!", True, "fuerza correcta"),
]

for pwd, should_be_valid, description in test_passwords:
    validation = validate_password_strength(pwd)
    is_valid = all(validation.values())
    error_msg = get_password_error_message(validation)
    
    status = "✅" if is_valid == should_be_valid else "❌"
    print(f"  {status} '{pwd}' ({description})")
    if is_valid != should_be_valid:
        print(f"     Validación: {validation}")
        print(f"     Mensaje: {error_msg}")
        sys.exit(1)

# TEST 4: Cambio de contraseña (lógica)
print("\n[TEST 4] Lógica de cambio de contraseña")

old_password = "CurrentPassword123!"
new_password = "NewPassword456@"

old_hash = hash_password(old_password)
new_hash = hash_password(new_password)

# Verificar que vieja contraseña verifica contra viejo hash
if not verify_password(old_password, old_hash):
    print("  ❌ ERROR: Vieja contraseña no verifica")
    sys.exit(1)
print("  ✅ Vieja contraseña verifica contra viejo hash")

# Verificar que nueva contraseña NO verifica contra viejo hash
if verify_password(new_password, old_hash):
    print("  ❌ ERROR: Nueva contraseña verifica contra viejo hash (collision)")
    sys.exit(1)
print("  ✅ Nueva contraseña NO verifica contra viejo hash")

# Verificar que nueva contraseña verifica contra nuevo hash
if not verify_password(new_password, new_hash):
    print("  ❌ ERROR: Nueva contraseña no verifica contra nuevo hash")
    sys.exit(1)
print("  ✅ Nueva contraseña verifica contra nuevo hash")

# Verificar que vieja contraseña NO verifica contra nuevo hash
if verify_password(old_password, new_hash):
    print("  ❌ ERROR: Vieja contraseña verifica contra nuevo hash (collision)")
    sys.exit(1)
print("  ✅ Vieja contraseña NO verifica contra nuevo hash")

# TEST 5: Hashes únicos (salt aleatorio)
print("\n[TEST 5] Uniqueness - Mismo password genera hashes diferentes")

hash1 = hash_password("SamePassword123!")
hash2 = hash_password("SamePassword123!")

if hash1 == hash2:
    print(f"  ❌ ERROR: Hashes idénticos (salt no funciona)")
    print(f"     Hash1: {hash1}")
    print(f"     Hash2: {hash2}")
    sys.exit(1)
else:
    print(f"  ✅ Hashes diferentes (salt aleatorio funciona)")
    print(f"     Hash1: {hash1[:40]}...")
    print(f"     Hash2: {hash2[:40]}...")

# Pero ambos verifican contra misma contraseña
if verify_password("SamePassword123!", hash1) and verify_password("SamePassword123!", hash2):
    print(f"  ✅ Ambos hashes verifican contra misma contraseña")
else:
    print(f"  ❌ ERROR: Verificación de hashes fallida")
    sys.exit(1)

print("\n" + "=" * 70)
print(" ✅ TODOS LOS TESTS PASARON")
print("=" * 70)

print("\n📋 RESUMEN:")
print("  • Hashing: bcrypt con 12 rounds")
print("  • Verificación: Correcta contra hashes diferentes")
print("  • Fuerza: Validación de requisitos")
print("  • Uniqueness: Salt aleatorio genera hashes diferentes")
print("  • Security: Mismo password sempre verifica correctamente")

sys.exit(0)
