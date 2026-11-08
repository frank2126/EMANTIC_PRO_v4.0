# Solicitudes al Centro de Gestión — reglas puras (sin base de datos ni FastAPI: se prueban solas)

import datetime
import re
from typing import Optional, Tuple

# clave → etiqueta. El frontend (utils/solicitudesUtils.js) usa las MISMAS claves.
TIPOS = {
    "mantenimiento":        "Novedad de mantenimiento",
    "informe_detallado":    "Informes detallados",
    "temperatura":          "Diagnóstico de temperatura",
    "reporte_revision":     "Reportes y revisión",
    "analisis_operativo":   "Análisis operativo",
    "actualizacion_bases":  "Actualización de bases DPV / ICO",
    "moviles_contundentes": "Móviles contestados contundentes y su estado",
    "programacion":         "Sugerencias de programación de móviles",
    "otro":                 "Otra información",
}
ESTADOS = ("pendiente", "en_proceso", "atendida", "cerrada")
PRIORIDADES = ("normal", "urgente")

MIN_MENSAJE, MAX_MENSAJE, MAX_RESPUESTA, MAX_MOVIL = 10, 600, 4000, 30
_MOVIL_RE = re.compile(r"^[A-Z0-9][A-Z0-9 .\-/]*$")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ErrorValidacion(ValueError):
    pass


def limpiar_texto(s: Optional[str]) -> str:
    """Quita caracteres de control, unifica saltos de línea y recorta; deja los saltos de línea del usuario."""
    s = _CONTROL_RE.sub("", (s or "").replace("\r\n", "\n").replace("\r", "\n"))
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def normalizar_movil(m: Optional[str]) -> str:
    m = re.sub(r"\s+", " ", (m or "").strip().upper())
    if not m:
        return ""
    if len(m) > MAX_MOVIL or not _MOVIL_RE.match(m):
        raise ErrorValidacion("El móvil solo puede llevar letras, números, guiones y puntos (ej: Z32-7036).")
    return m


def validar_nueva(tipo: str, mensaje: str, movil: Optional[str], prioridad: Optional[str]) -> dict:
    """Devuelve los campos limpios o lanza ErrorValidacion con un mensaje para mostrar al usuario."""
    if tipo not in TIPOS:
        raise ErrorValidacion("Elige qué tipo de información necesitas.")
    texto = limpiar_texto(mensaje)
    if len(texto) < MIN_MENSAJE:
        raise ErrorValidacion(f"Cuéntanos un poco más (mínimo {MIN_MENSAJE} caracteres).")
    if len(texto) > MAX_MENSAJE:
        raise ErrorValidacion(f"El mensaje es muy largo (máximo {MAX_MENSAJE} caracteres).")
    prio = (prioridad or "normal").lower()
    if prio not in PRIORIDADES:
        raise ErrorValidacion("Prioridad inválida.")
    return {"tipo": tipo, "mensaje": texto, "movil": normalizar_movil(movil), "prioridad": prio}


def aplicar_gestion(sol, estado: Optional[str], respuesta: Optional[str], gestor: str, ahora: Optional[datetime.datetime] = None) -> dict:
    """
    Aplica la gestión del Centro sobre `sol` (objeto con estado, respuesta, respondido_por, respondido_at, visto_solicitante).
    Reglas:
      · escribir una respuesta nueva → el solicitante la verá como «sin leer»; si no se indica estado, pasa a «atendida»
      · «atendida» exige tener respuesta
      · sin respuesta nueva ni estado no hay nada que hacer
    Devuelve {'cambio_respuesta': bool, 'cambio_estado': bool}.
    """
    ahora = ahora or datetime.datetime.utcnow()
    if estado is not None and estado not in ESTADOS:
        raise ErrorValidacion("Estado inválido.")
    nueva = None
    if respuesta is not None:
        nueva = limpiar_texto(respuesta)
        if len(nueva) > MAX_RESPUESTA:
            raise ErrorValidacion(f"La respuesta es muy larga (máximo {MAX_RESPUESTA} caracteres).")
    cambio_resp = bool(nueva) and nueva != (sol.respuesta or "")
    destino = estado or (("atendida") if cambio_resp else sol.estado)
    final_resp = nueva if nueva is not None else (sol.respuesta or "")
    if destino == "atendida" and not final_resp:
        raise ErrorValidacion("Para marcarla como atendida escribe la respuesta.")
    if estado is None and not cambio_resp:
        raise ErrorValidacion("No hay nada que actualizar.")
    cambio_estado = destino != sol.estado
    if nueva is not None:
        sol.respuesta = nueva
    if cambio_resp:
        sol.respondido_por = gestor
        sol.respondido_at = ahora
        sol.visto_solicitante = False
    sol.estado = destino
    return {"cambio_respuesta": cambio_resp, "cambio_estado": cambio_estado}


def iso_utc(dt: Optional[datetime.datetime]) -> Optional[str]:
    return dt.replace(microsecond=0).isoformat() + "Z" if dt else None


def serializar(s, incluir_solicitante: bool = False) -> dict:
    d = {
        "id": s.id, "tipo": s.tipo, "tipo_label": TIPOS.get(s.tipo, s.tipo), "movil": s.movil or "",
        "mensaje": s.mensaje, "prioridad": s.prioridad, "estado": s.estado,
        "respuesta": s.respuesta or "", "respondido_por": s.respondido_por or "",
        "respondido_at": iso_utc(s.respondido_at), "created_at": iso_utc(s.created_at),
        "sin_leer": bool(s.respuesta) and not s.visto_solicitante,
    }
    if incluir_solicitante:
        d["solicitante"] = s.solicitante or s.username or ""
        d["username"] = s.username or ""
    return d
