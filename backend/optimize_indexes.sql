-- ═══════════════════════════════════════════════════════════
--  EMANTIX PRO — OPTIMIZACIÓN DE ÍNDICES SQL SERVER
--  Script para crear índices faltantes
-- ═══════════════════════════════════════════════════════════

-- TABLA: users
-- Índices necesarios para filtros comunes
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_users_email')
    CREATE NONCLUSTERED INDEX idx_users_email ON dbo.users(email);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_users_active')
    CREATE NONCLUSTERED INDEX idx_users_active ON dbo.users(active);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_users_role')
    CREATE NONCLUSTERED INDEX idx_users_role ON dbo.users(role);

-- TABLA: manuals
-- Índice para búsqueda por categoría
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_manuals_category')
    CREATE NONCLUSTERED INDEX idx_manuals_category ON dbo.manuals(category);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_manuals_active')
    CREATE NONCLUSTERED INDEX idx_manuals_active ON dbo.manuals(active);

-- TABLA: documents
-- Índices para búsqueda y filtrado
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_documents_category')
    CREATE NONCLUSTERED INDEX idx_documents_category ON dbo.documents(category);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_documents_ext')
    CREATE NONCLUSTERED INDEX idx_documents_ext ON dbo.documents(ext);

-- TABLA: maintenance
-- Índices críticos para filtrado y búsqueda
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_maintenance_unidad')
    CREATE NONCLUSTERED INDEX idx_maintenance_unidad ON dbo.maintenance(unidad);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_maintenance_estado')
    CREATE NONCLUSTERED INDEX idx_maintenance_estado ON dbo.maintenance(estado);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_maintenance_tecnico')
    CREATE NONCLUSTERED INDEX idx_maintenance_tecnico ON dbo.maintenance(tecnico);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_maintenance_fecha')
    CREATE NONCLUSTERED INDEX idx_maintenance_fecha ON dbo.maintenance(fecha);

-- TABLA: reportes_campo
-- Índices críticos para filtrado y agregación
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_reportes_tipo')
    CREATE NONCLUSTERED INDEX idx_reportes_tipo ON dbo.reportes_campo(tipo_novedad);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_reportes_fecha')
    CREATE NONCLUSTERED INDEX idx_reportes_fecha ON dbo.reportes_campo(fecha);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_reportes_unidad_funcional')
    CREATE NONCLUSTERED INDEX idx_reportes_unidad_funcional ON dbo.reportes_campo(unidad_funcional);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_reportes_tecnico')
    CREATE NONCLUSTERED INDEX idx_reportes_tecnico ON dbo.reportes_campo(tecnico);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_reportes_pir')
    CREATE NONCLUSTERED INDEX idx_reportes_pir ON dbo.reportes_campo(pir);

-- TABLA: dpv_registros
-- Índices compuestos para reportes comunes
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_dpv_empresa')
    CREATE NONCLUSTERED INDEX idx_dpv_empresa ON dbo.dpv_registros(empresa) INCLUDE (estado, fecha_inicio);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_dpv_estado')
    CREATE NONCLUSTERED INDEX idx_dpv_estado ON dbo.dpv_registros(estado);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_dpv_fecha')
    CREATE NONCLUSTERED INDEX idx_dpv_fecha ON dbo.dpv_registros(fecha_inmovilizacion);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_dpv_placa')
    CREATE NONCLUSTERED INDEX idx_dpv_placa ON dbo.dpv_registros(placa) INCLUDE (estado, fecha_inmovilizacion);

-- TABLA: ico_registros
-- Índices compuestos para reportes comunes
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_ico_empresa')
    CREATE NONCLUSTERED INDEX idx_ico_empresa ON dbo.ico_registros(empresa) INCLUDE (estado, fecha_inicio);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_ico_tipo_novedad')
    CREATE NONCLUSTERED INDEX idx_ico_tipo_novedad ON dbo.ico_registros(tipo_novedad);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_ico_fecha')
    CREATE NONCLUSTERED INDEX idx_ico_fecha ON dbo.ico_registros(fecha_novedad);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_ico_area')
    CREATE NONCLUSTERED INDEX idx_ico_area ON dbo.ico_registros(area);

-- TABLA: dpv_mensual
-- Índices compuestos para búsqueda eficiente
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_dpv_mensual_empresa_mes')
    CREATE NONCLUSTERED INDEX idx_dpv_mensual_empresa_mes ON dbo.dpv_mensual(empresa, mes);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_dpv_mensual_fecha')
    CREATE NONCLUSTERED INDEX idx_dpv_mensual_fecha ON dbo.dpv_mensual(mes);

-- TABLA: disponibilidad
-- Índices para filtrado y reporte
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_disponibilidad_empresa')
    CREATE NONCLUSTERED INDEX idx_disponibilidad_empresa ON dbo.disponibilidad(empresa) INCLUDE (fecha_corte, dias_inoperatividad);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_disponibilidad_fecha')
    CREATE NONCLUSTERED INDEX idx_disponibilidad_fecha ON dbo.disponibilidad(fecha_corte);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_disponibilidad_inmovilizado')
    CREATE NONCLUSTERED INDEX idx_disponibilidad_inmovilizado ON dbo.disponibilidad(inmovilizado);

-- TABLA: cargas_historial
-- Índices para auditoría y reporte
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_cargas_tipo')
    CREATE NONCLUSTERED INDEX idx_cargas_tipo ON dbo.cargas_historial(tipo_carga);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_cargas_fecha')
    CREATE NONCLUSTERED INDEX idx_cargas_fecha ON dbo.cargas_historial(created_at);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_cargas_usuario')
    CREATE NONCLUSTERED INDEX idx_cargas_usuario ON dbo.cargas_historial(usuario_id);

-- ═══════════════════════════════════════════════════════════
--  ESTADÍSTICAS Y MANTENIMIENTO
-- ═══════════════════════════════════════════════════════════

-- Actualizar estadísticas de todas las tablas
EXEC sp_updatestats;

-- Reorganizar índices fragmentados (> 10%)
-- Nota: Ejecutar periódicamente, no como parte de script inicial
-- ALTER INDEX ALL ON dbo.users REBUILD;
-- ALTER INDEX ALL ON dbo.dpv_registros REBUILD;
-- ALTER INDEX ALL ON dbo.ico_registros REBUILD;

PRINT 'Índices creados exitosamente';
PRINT 'Total de índices esperados: ~20';
PRINT 'Ejecutar: EXEC sp_updatestats; semanalmente';
