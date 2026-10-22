# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Configuración de Base de Datos SQL Server
# ═══════════════════════════════════════════════════════════

from sqlalchemy import create_engine, Column, String, Boolean, Text, DateTime, Integer, Float, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import uuid
from sqlalchemy import UniqueConstraint
import os

# Importar configuración desde .env
try:
    from config import settings
    database_url = settings.database_url
    db_echo = settings.db_echo
    db_pool_size = settings.db_pool_size
    db_max_overflow = settings.db_max_overflow
    db_pool_recycle = settings.db_pool_recycle
except:
    # Fallback a variables de entorno directas
    DB_SERVER = os.getenv('DB_SERVER', 'localhost')
    DB_USER = os.getenv('DB_USER', 'admin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_NAME = os.getenv('DB_NAME', 'EMANTIC')
    DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    
    database_url = f'mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}?driver={DB_DRIVER}'
    db_echo = False
    db_pool_size = 20
    db_max_overflow = 40
    db_pool_recycle = 3600

# Crear motor con configuración
engine = create_engine(
    database_url,
    echo=db_echo,
    pool_pre_ping=True,
    pool_size=db_pool_size,
    max_overflow=db_max_overflow,
    pool_recycle=db_pool_recycle,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── MODELOS ────────────────────────────────────────────────

class UserDB(Base):
    __tablename__ = "users"
    id         = Column(String(36), primary_key=True)
    username   = Column(String(100), unique=True, nullable=False)
    password   = Column(String(256), nullable=False)
    name       = Column(String(200), nullable=False)
    email      = Column(String(200), default="")
    role       = Column(String(50), default="tecnico")
    active     = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ManualDB(Base):
    __tablename__ = "manuals"
    id          = Column(String(36), primary_key=True)
    title       = Column(String(300), nullable=False)
    description = Column(Text, default="")
    category    = Column(String(100), default="General")
    filename    = Column(String(400), default="")
    url         = Column(String(500), default="")
    size_mb     = Column(String(20), default="0")
    uploaded_by = Column(String(100), default="")
    uploaded_at = Column(String(50), default="")
    active      = Column(Boolean, default=True)

class DocumentDB(Base):
    __tablename__ = "documents"
    id          = Column(String(36), primary_key=True)
    title       = Column(String(300), nullable=False)
    category    = Column(String(100), default="General")
    filename    = Column(String(400), default="")
    url         = Column(String(500), default="")
    ext         = Column(String(20), default="FILE")
    size_kb     = Column(String(20), default="0")
    uploaded_by = Column(String(100), default="")
    uploaded_at = Column(String(50), default="")

class MaintenanceDB(Base):
    __tablename__ = "maintenance"
    id          = Column(String(36), primary_key=True)
    unidad      = Column(String(100), nullable=False)
    tipo        = Column(String(200), nullable=False)
    km_actual   = Column(Integer, default=0)
    km_servicio = Column(Integer, default=0)
    fecha       = Column(String(20), default="")
    estado      = Column(String(50), default="Programado")
    tecnico     = Column(String(100), default="")
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)

class ReporteDB(Base):
    __tablename__ = "reportes_campo"
    id               = Column(String(36), primary_key=True)
    fecha            = Column(String(20), default="")
    pir              = Column(String(100), default="")
    unidad_funcional = Column(String(50), default="")
    tecnico          = Column(String(100), default="")
    supervisor       = Column(String(100), default="")
    protocolo        = Column(String(100), default="")
    bus              = Column(Integer, default=0)
    novedad          = Column(Text, default="")
    tipo_novedad     = Column(String(50), default="OK")
    created_at       = Column(DateTime, default=datetime.datetime.utcnow)
    uploaded_by      = Column(String(100), default="")

class DpvRegistroDB(Base):
    __tablename__ = "dpv_registros"
    id                    = Column(Integer, primary_key=True, autoincrement=True)
    dpv_id                = Column(Integer, unique=True, nullable=False, index=True)
    estado                = Column(String(100), default="")
    fecha_inicio          = Column(DateTime, nullable=True)
    fecha_cierre          = Column(DateTime, nullable=True)
    empresa               = Column(String(200), default="")
    fuente                = Column(String(200), default="")
    placa                 = Column(String(20),  default="", index=True)
    movil                 = Column(String(20),  default="")
    tipologia             = Column(String(100), default="")
    fecha_inmovilizacion  = Column(DateTime, nullable=True)
    hora                  = Column(String(10),  default="")
    causa_inmovilizacion  = Column(String(300), default="")
    descripcion_novedad   = Column(Text,        default="")
    ruta                  = Column(String(100), default="")
    operador              = Column(String(50),  default="")
    dia_semana            = Column(String(20),  default="")
    alerta                = Column(String(100), default="")
    franja_horaria        = Column(String(50),  default="")
    created_at            = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class IcoRegistroDB(Base):
    __tablename__ = "ico_registros"
    id                    = Column(Integer, primary_key=True, autoincrement=True)
    ico_id                = Column(Integer, unique=True, nullable=False, index=True)
    id_novedad            = Column(Integer, nullable=True)
    estado                = Column(String(100), default="")
    fecha_inicio          = Column(DateTime, nullable=True)
    fecha_cierre          = Column(DateTime, nullable=True)
    empresa               = Column(String(200), default="")
    tipo_novedad          = Column(String(100), default="", index=True)
    fecha_novedad         = Column(DateTime, nullable=True)
    fecha_identificacion  = Column(DateTime, nullable=True)
    fecha_notificacion    = Column(DateTime, nullable=True)
    fuente                = Column(String(200), default="")
    area                  = Column(String(100), default="")
    direccion             = Column(String(300), default="")
    placa                 = Column(String(20),  default="", index=True)
    movil                 = Column(String(20),  default="")
    tipologia             = Column(String(100), default="")
    dia_semana            = Column(String(20),  default="")
    puntos                = Column(String(50),  default="")
    descripcion           = Column(Text,        default="")
    created_at            = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class CargaHistorialDB(Base):
    __tablename__ = "cargas_historial"
    id                      = Column(Integer, primary_key=True, autoincrement=True)
    tipo_carga              = Column(String(20), default="dpv", index=True)
    usuario_id              = Column(String(100), default="")
    nombre_archivo          = Column(String(300), default="")
    total_filas             = Column(Integer, default=0)
    filas_insertadas        = Column(Integer, default=0)
    filas_actualizadas      = Column(Integer, default=0)
    filas_error             = Column(Integer, default=0)
    estado                  = Column(String(20), default="exitoso")
    mensaje_error           = Column(Text, default="")
    tiempo_procesamiento_seg = Column(String(20), default="0")
    created_at              = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class DpvMensualDB(Base):
    __tablename__ = "dpv_mensual"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    empresa       = Column(String(50), nullable=False, index=True)
    mes           = Column(DateTime, nullable=False, index=True)
    fecha_texto   = Column(String(100), default="")
    dpv_general   = Column(Integer, default=0)
    dpv_estandar  = Column(Integer, default=10000)
    dpv_critico   = Column(Integer, default=7000)
    no_varados    = Column(Integer, default=0)
    kms           = Column(Integer, default=0)
    padron        = Column(Integer, default=0)
    buseton       = Column(Integer, default=0)
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (UniqueConstraint('empresa', 'mes', name='uq_dpv_mensual_empresa_mes'),)

class DpvKmMensualDB(Base):
    """Kilómetros oficiales de cada mes por unidad (E10 / E16), en total y por tipología.

    Es el denominador del DPV: las inmovilizaciones se calculan siempre en vivo desde dpv_registros,
    así que aquí NO se guardan DPV ni conteos (solo, como referencia de auditoría, lo que traía el Excel).
    Tabla nueva: init_db() la crea sola al reiniciar; no hace falta tocar dpv_mensual.
    """
    __tablename__ = "dpv_km_mensual"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    empresa     = Column(String(10), nullable=False, index=True)    # 'E10' | 'E16'
    mes         = Column(DateTime, nullable=False, index=True)      # primer día del mes
    km_total    = Column(Float, default=0)
    km_padron   = Column(Float, nullable=True)
    km_buseton  = Column(Float, nullable=True)
    inm_excel   = Column(Integer, nullable=True)                    # TOTAL INMOVILIZADOS que calculó el Excel (referencia)
    dpv_excel   = Column(Float, nullable=True)                      # DPV GENERAL que mostraba el Excel (referencia)
    fuente      = Column(String(20), default="excel")               # 'excel' (carga) | 'manual' (formulario)
    updated_by  = Column(String(100), default="")
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (UniqueConstraint('empresa', 'mes', name='uq_dpv_km_mensual_empresa_mes'),)

class DisponibilidadDB(Base):
    __tablename__ = "disponibilidad"
    id                   = Column(Integer, primary_key=True, autoincrement=True)
    empresa              = Column(String(50), nullable=False, index=True)
    fecha_corte          = Column(DateTime, nullable=True, index=True)
    movil                = Column(String(50), default="")
    fecha_ingreso        = Column(DateTime, nullable=True)
    dias_inoperatividad  = Column(Float, default=0)
    area                 = Column(String(150), default="")
    descripcion          = Column(Text, default="")
    inmovilizado         = Column(Boolean, default=False)
    created_at           = Column(DateTime, default=datetime.datetime.utcnow)

class PasswordResetDB(Base):
    __tablename__ = "password_resets"
    id         = Column(String(36), primary_key=True)
    username   = Column(String(100), nullable=False)
    code       = Column(String(6),   nullable=False)
    expires_at = Column(DateTime,    nullable=False)
    used       = Column(Boolean,     default=False)
    created_at = Column(DateTime,    default=datetime.datetime.utcnow)

class RoleAuditDB(Base):
    __tablename__ = "role_audits"
    
    id              = Column(String(36), primary_key=True)
    admin_id        = Column(String(36), nullable=False)
    admin_username  = Column(String(100), nullable=False)
    user_id         = Column(String(36), nullable=False)
    user_username   = Column(String(100), nullable=False)
    old_role        = Column(String(50), nullable=True)
    new_role        = Column(String(50), nullable=False)
    action          = Column(String(50), nullable=False)
    reason          = Column(Text, default="")
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)
    ip_address      = Column(String(50), default="")

    __table_args__ = (
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_admin_id', 'admin_id'),
        Index('idx_audit_created_at', 'created_at'),
    )

class AppConfigDB(Base):
    __tablename__ = "app_config"
    key        = Column(String(100), primary_key=True)
    value      = Column(Text, default="")
    updated_by = Column(String(100), default="")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# ── FUNCIONES DE DEPENDENCIA ───────────────────────────────

def get_db():
    """Dependency injection for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """Get database session directly"""
    return SessionLocal()

def close_db(db):
    """Close database session"""
    if db:
        db.close()

def init_db():
    """Crea tablas e inserta datos iniciales si no existen."""
    from security import hash_password
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Admin por defecto (usa bcrypt para nueva seguridad)
        if not db.query(UserDB).filter_by(username="admin").first():
            db.add(UserDB(
                id=str(uuid.uuid4()), 
                username="admin",
                password=hash_password("Admin123!"), 
                name="Administrador",
                email="admin@emantix.com", 
                role="admin", 
                active=True
            ))
            print("  ✅ Usuario admin creado (bcrypt)")

        # Técnico por defecto (usa bcrypt para nueva seguridad)
        if not db.query(UserDB).filter_by(username="tecnico1").first():
            db.add(UserDB(
                id=str(uuid.uuid4()), 
                username="tecnico1",
                password=hash_password("Tecnico123!"), 
                name="Técnico Uno",
                email="tecnico1@emantix.com", 
                role="tecnico", 
                active=True
            ))
            print("  ✅ Usuario tecnico1 creado (bcrypt)")

        # Datos de mantenimiento iniciales
        if db.query(MaintenanceDB).count() == 0:
            maintenance_data = [
                ("Z32-001", "Servicio A", 125400, 130000, "2026-01-28", "Programado"),
                ("Z32-002", "Cambio Aceite", 98700, 100000, "2026-01-25", "Urgente"),
                ("Z34-001", "Revisión Frenos", 167800, 170000, "2026-01-30", "Programado"),
                ("Z34-002", "Servicio B", 134200, 135000, "2026-01-26", "Próximo"),
            ]
            for unidad, tipo, km_actual, km_servicio, fecha, estado in maintenance_data:
                db.add(MaintenanceDB(
                    id=str(uuid.uuid4()), 
                    unidad=unidad, 
                    tipo=tipo,
                    km_actual=km_actual, 
                    km_servicio=km_servicio, 
                    fecha=fecha, 
                    estado=estado, 
                    tecnico="tecnico1"
                ))
            print("  ✅ Datos de mantenimiento iniciales creados")

        db.commit()
        print("  ✅ Base de datos inicializada correctamente")
    except Exception as e:
        db.rollback()
        print(f"  ❌ Error inicializando BD: {e}")
        raise e
    finally:
        db.close()

# ═══════════════════════════════════════════════════════════
# MODELO REPUESTODB
# ═══════════════════════════════════════════════════════════

class RepuestoDB(Base):
    """
    Modelo para repuestos/piezas
    Cargados desde el Excel de repuestos
    """
    __tablename__ = "repuestos"
    
    # Columnas principales
    id = Column(Integer, primary_key=True, autoincrement=True)
    pieza = Column(String(50), unique=True, nullable=False, index=True)  # Código del repuesto
    descripcion = Column(String(500), nullable=False, index=True)  # Descripción
    udm = Column(String(20), default="UN")  # Unidad de medida
    clase = Column(String(50), index=True)  # Clase
    
    # Jerarquía
    jerarquia_pieza = Column(String(100))  # Jerarquía de la pieza
    nivel_sistema = Column(String(50), index=True)  # Nivel de sistema
    nivel_montaje = Column(String(100))  # Nivel de montaje
    nivel_componente = Column(String(100))  # Nivel de componente
    
    # Información adicional
    condicion = Column(String(100))  # Condición
    numero_pieza_fabricante = Column(String(100))  # Número de pieza del fabricante
    suministrador_sugerido = Column(String(200))  # Suministrador sugerido
    
    # Seguimiento
    seguimiento_piezas_reparables = Column(String(10), default="NO")  # Sí/No
    seguimiento_por_activo = Column(String(10), default="NO")  # Sí/No
    dias_garantia = Column(Integer, default=0)  # Días de garantía
    evitar_nuevos_pedidos = Column(String(10), default="NO")  # Sí/No
    
    # Metadatos
    foto_perfil = Column(String(500), default="")  # Ruta foto
    activo = Column(Boolean, default=True, index=True)  # Activo/Inactivo
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  # CORREGIDO: datetime.datetime.utcnow
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)  # CORREGIDO
    
    # Índices compuestos para búsqueda rápida
    __table_args__ = (
        Index('idx_pieza_descripcion', 'pieza', 'descripcion'),
        Index('idx_clase_nivel', 'clase', 'nivel_sistema'),
    )

# ═══════════════════════════════════════════════════════════
#  PEGAR AL FINAL DE database.py  (usa los imports que ya tiene)
#  init_db() ya hace Base.metadata.create_all → crea las 3 tablas solas al reiniciar.
# ═══════════════════════════════════════════════════════════

class LecturaKmDB(Base):
    """Una fila por móvil y día (viene de la exportación de telemetría)."""
    __tablename__ = "lecturas_km"
    id        = Column(Integer, primary_key=True, autoincrement=True)
    movil     = Column(String(20), nullable=False, index=True)
    fecha     = Column(String(10), nullable=False, index=True)   # AAAA-MM-DD
    recorrido = Column(Float, default=0)
    odo_min   = Column(Float, default=0)
    odo_max   = Column(Float, default=0)                         # Mín = Máx = 0 → sin dato
    __table_args__ = (UniqueConstraint('movil', 'fecha', name='uq_lectura_movil_fecha'),)

class MovilBaseDB(Base):
    """Odómetro de cada móvil la primera vez que se cargó: lo anterior se da por intervenido."""
    __tablename__ = "moviles_base"
    movil      = Column(String(20), primary_key=True)
    odo_base   = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ProgramacionMovilDB(Base):
    """Un hito (p. ej. 330000 km) por móvil: Programado → Intervenido."""
    __tablename__ = "programacion_moviles"
    id                 = Column(Integer, primary_key=True, autoincrement=True)
    movil              = Column(String(20), nullable=False, index=True)
    hito_km            = Column(Integer, nullable=False)
    estado             = Column(String(20), default="Programado")
    fecha_programada   = Column(String(10), default="")
    fecha_intervencion = Column(String(10), default="")
    km_intervencion    = Column(Integer, default=0)
    observacion        = Column(String(300), default="")
    updated_by         = Column(String(100), default="")
    updated_at         = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    __table_args__ = (UniqueConstraint('movil', 'hito_km', name='uq_prog_movil_hito'),)

    # ═══════════════════════════════════════════════════════════
#  PEGAR AL FINAL DE backend/database.py  (usa los imports que ya tiene)
#  init_db() ya hace Base.metadata.create_all → crea las 3 tablas solas al reiniciar.
# ═══════════════════════════════════════════════════════════

class ChecklistReporteDB(Base):
    """Un reporte 'Necesita atención' del check list del operador (una fila del Excel)."""
    __tablename__ = "checklist_reportes"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    movil           = Column(String(20), nullable=False, index=True)
    estado          = Column(String(50), default="")
    fecha_creacion  = Column(DateTime, nullable=False, index=True)
    lugar           = Column(String(50), default="")
    codigo_conductor = Column(String(20), default="")
    nombre_conductor = Column(String(200), default="")
    notas           = Column(Text, default="")
    ruta            = Column(String(30), default="")
    items_texto     = Column(Text, default="")        # texto original completo de 'Items de atención'
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)
    # Evita duplicados cuando el Excel (día de por medio) se traslapa con el anterior
    __table_args__ = (UniqueConstraint('movil', 'fecha_creacion', 'codigo_conductor', name='uq_chk_rep'),)

class ChecklistItemDB(Base):
    """Cada ítem de mantenimiento (de los 12 del catálogo) dentro de un reporte."""
    __tablename__ = "checklist_items"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    reporte_id      = Column(Integer, nullable=False, index=True)
    movil           = Column(String(20), nullable=False, index=True)
    item            = Column(String(100), nullable=False, index=True)
    fecha_creacion  = Column(DateTime, nullable=False)
    codigo_conductor = Column(String(20), default="")
    nombre_conductor = Column(String(200), default="")
    __table_args__ = (UniqueConstraint('reporte_id', 'item', name='uq_chk_item'),)

class ChecklistSeguimientoDB(Base):
    """Seguimiento por móvil + ítem: Pendiente/Programado (abierto) → Intervenido (queda como historial)."""
    __tablename__ = "checklist_seguimiento"
    id                 = Column(Integer, primary_key=True, autoincrement=True)
    movil              = Column(String(20), nullable=False, index=True)
    item               = Column(String(100), nullable=False)
    estado             = Column(String(20), default="Pendiente")
    fecha_programada   = Column(String(10), default="")
    fecha_intervencion = Column(String(10), default="")
    orden_trabajo      = Column(String(50), default="")       # opcional
    observacion        = Column(String(300), default="")
    corte_fecha        = Column(DateTime, nullable=True)      # reportes <= corte ya se dan por atendidos
    updated_by         = Column(String(100), default="")
    updated_at         = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)