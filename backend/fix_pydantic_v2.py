#!/usr/bin/env python3
"""
Corrige el aviso de Pydantic v2:
    UserWarning: Valid config keys have changed in V2: 'orm_mode' has been renamed to 'from_attributes'

Cambia, en todo el backend:
        class Config:
            orm_mode = True
por:
        model_config = ConfigDict(from_attributes=True)
y agrega ConfigDict al "from pydantic import ..." del archivo.

Uso (dentro de la carpeta backend, con el entorno virtual activado):
    python fix_pydantic_v2.py
Cada archivo modificado deja una copia de respaldo con extensión .bak
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
OMITIR = {"venv", "venv_new", "env", "ENV", "__pycache__", "node_modules", ".git", "site-packages"}

# class Config: / orm_mode = True  (respeta el tipo de salto de línea del archivo: LF o CRLF)
BLOQUE = re.compile(r"^([ \t]*)class Config:[ \t]*(\r?\n)[ \t]+orm_mode[ \t]*=[ \t]*True[ \t]*(?:#[^\r\n]*)?(?=\r?\n|\Z)", re.M)
IMPORT = re.compile(r"^(from pydantic import )([^\r\n(\\]+?)[ \t]*(?=\r?\n|\Z)", re.M)
YA_TIENE = re.compile(r"^from pydantic import [^\r\n]*\bConfigDict\b", re.M)


def archivos():
    for p in sorted(RAIZ.rglob("*.py")):
        if OMITIR & set(p.relative_to(RAIZ).parts) or p.name == Path(__file__).name:
            continue
        yield p


def corregir(texto: str):
    n = len(BLOQUE.findall(texto))
    if not n:
        return texto, 0, True
    texto = BLOQUE.sub(lambda m: f"{m.group(1)}model_config = ConfigDict(from_attributes=True)", texto)
    if YA_TIENE.search(texto):
        return texto, n, True
    m = IMPORT.search(texto)
    if not m:
        return texto, n, False                      # no hay "from pydantic import ..." para ampliar
    texto = texto[:m.start()] + m.group(1) + m.group(2) + ", ConfigDict" + texto[m.end():]
    return texto, n, True


def main():
    cambiados, manual = 0, []
    for p in archivos():
        try:
            original = p.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        nuevo, n, import_ok = corregir(original)
        if not n:
            continue
        p.with_name(p.name + ".bak").write_bytes(original.encode("utf-8"))
        p.write_bytes(nuevo.encode("utf-8"))
        cambiados += 1
        print(f"✔ {p.relative_to(RAIZ)}: {n} clase(s) corregida(s)")
        if not import_ok:
            manual.append(p.relative_to(RAIZ))

    for p in manual:
        print(f"⚠ {p}: agrega manualmente al inicio →  from pydantic import ConfigDict")

    pendientes = []
    for p in archivos():
        try:
            for i, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if "orm_mode" in linea:
                    pendientes.append(f"{p.relative_to(RAIZ)}:{i}: {linea.strip()}")
        except UnicodeDecodeError:
            pass
    if pendientes:
        print("\n⚠ Quedan usos de orm_mode que este script no reconoció (cámbialos a from_attributes a mano):")
        print("\n".join("  " + x for x in pendientes))
    elif cambiados:
        print("\nListo. Reinicia el backend: el aviso de orm_mode ya no debe aparecer.")
    else:
        print("No se encontró ningún orm_mode. Nada que cambiar.")


if __name__ == "__main__":
    main()