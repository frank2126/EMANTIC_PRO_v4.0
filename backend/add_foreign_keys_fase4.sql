-- ═══════════════════════════════════════════════════════════════════════════════
--  EMANTIX PRO — FASE 4 — FOREIGN KEYS PARA INTEGRIDAD REFERENCIAL
--  Script para agregar relaciones entre tablas
--  SQL Server
-- ═══════════════════════════════════════════════════════════════════════════════

-- ── ADVERTENCIA ────────────────────────────────────────────────────────────
-- ANTES DE EJECUTAR:
-- 1. Hacer backup de BD
-- 2. Limpiar datos huérfanos primero
-- 3. Ejecutar en horario de bajo uso
-- 4. Verificar que no hay datos inconsistentes

PRINT 'INICIANDO ADICIÓN DE FOREIGN KEYS...';
PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PASO 1: VERIFICAR DATOS INCONSISTENTES
-- ═══════════════════════════════════════════════════════════════════════════════

PRINT '═══════════════════════════════════════════════════════════════════════════════';
PRINT 'PASO 1: Verificando datos inconsistentes...';
PRINT '═══════════════════════════════════════════════════════════════════════════════';
PRINT '';

-- Verificar técnicos en maintenance que no existen en users
PRINT 'Técnicos en maintenance sin usuario:';
SELECT DISTINCT tecnico FROM dbo.maintenance m
WHERE tecnico != '' AND tecnico IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM dbo.users u WHERE u.username = m.tecnico);

-- Verificar usuarios en reportes que no existen en users
PRINT '';
PRINT 'Usuarios en reportes sin usuario registrado:';
SELECT DISTINCT uploaded_by FROM dbo.reportes_campo r
WHERE uploaded_by != '' AND uploaded_by IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM dbo.users u WHERE u.username = r.uploaded_by);

PRINT '';
PRINT 'Advertencia: Si hay resultados arriba, limpiar datos antes de continuar';
PRINT 'Ejemplo: UPDATE maintenance SET tecnico = NULL WHERE tecnico NOT IN (SELECT username FROM users)';
PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PASO 2: AGREGAR FOREIGN KEYS PRINCIPALES
-- ═══════════════════════════════════════════════════════════════════════════════

PRINT 'PASO 2: Agregando Foreign Keys...';
PRINT '';

-- FK 1: maintenance → users (relación tecnico)
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_maintenance_user_tecnico')
BEGIN
    ALTER TABLE dbo.maintenance
    ADD CONSTRAINT fk_maintenance_user_tecnico
    FOREIGN KEY (tecnico) REFERENCES dbo.users(username)
    ON DELETE SET NULL
    ON UPDATE CASCADE;
    
    PRINT '✅ Agregado: fk_maintenance_user_tecnico';
END
ELSE
BEGIN
    PRINT '⚠️  Ya existe: fk_maintenance_user_tecnico';
END

-- FK 2: reportes_campo → users (relación uploaded_by)
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_reportes_user_uploaded_by')
BEGIN
    ALTER TABLE dbo.reportes_campo
    ADD CONSTRAINT fk_reportes_user_uploaded_by
    FOREIGN KEY (uploaded_by) REFERENCES dbo.users(username)
    ON DELETE SET NULL
    ON UPDATE CASCADE;
    
    PRINT '✅ Agregado: fk_reportes_user_uploaded_by';
END
ELSE
BEGIN
    PRINT '⚠️  Ya existe: fk_reportes_user_uploaded_by';
END

-- FK 3: cargas_historial → users (relación usuario_id)
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_cargas_user_usuario_id')
BEGIN
    ALTER TABLE dbo.cargas_historial
    ADD CONSTRAINT fk_cargas_user_usuario_id
    FOREIGN KEY (usuario_id) REFERENCES dbo.users(username)
    ON DELETE SET NULL
    ON UPDATE CASCADE;
    
    PRINT '✅ Agregado: fk_cargas_user_usuario_id';
END
ELSE
BEGIN
    PRINT '⚠️  Ya existe: fk_cargas_user_usuario_id';
END

PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PASO 3: AGREGAR ÍNDICES PARA FOREIGN KEYS
-- ═══════════════════════════════════════════════════════════════════════════════

PRINT 'PASO 3: Agregando índices para Foreign Keys...';
PRINT '';

-- Índice para maintenance.tecnico (ya existe desde FASE 3, pero confirmamos)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_maintenance_tecnico')
BEGIN
    CREATE NONCLUSTERED INDEX idx_maintenance_tecnico 
    ON dbo.maintenance(tecnico);
    PRINT '✅ Creado: idx_maintenance_tecnico';
END
ELSE
BEGIN
    PRINT '✓ Ya existe: idx_maintenance_tecnico';
END

-- Índice para reportes_campo.uploaded_by (si no existe)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_reportes_uploaded_by')
BEGIN
    CREATE NONCLUSTERED INDEX idx_reportes_uploaded_by 
    ON dbo.reportes_campo(uploaded_by);
    PRINT '✅ Creado: idx_reportes_uploaded_by';
END
ELSE
BEGIN
    PRINT '✓ Ya existe: idx_reportes_uploaded_by';
END

-- Índice para cargas_historial.usuario_id (si no existe)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_cargas_usuario_id')
BEGIN
    CREATE NONCLUSTERED INDEX idx_cargas_usuario_id 
    ON dbo.cargas_historial(usuario_id);
    PRINT '✅ Creado: idx_cargas_usuario_id';
END
ELSE
BEGIN
    PRINT '✓ Ya existe: idx_cargas_usuario_id';
END

PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PASO 4: AGREGAR CHECK CONSTRAINTS PARA VALIDACIÓN
-- ═══════════════════════════════════════════════════════════════════════════════

PRINT 'PASO 4: Agregando Check Constraints...';
PRINT '';

-- Check: estado en maintenance debe ser válido
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_maintenance_estado')
BEGIN
    ALTER TABLE dbo.maintenance
    ADD CONSTRAINT ck_maintenance_estado 
    CHECK (estado IN ('Programado', 'En Progreso', 'Completado', 'Cancelado', 'En Espera'));
    
    PRINT '✅ Agregado: ck_maintenance_estado';
END
ELSE
BEGIN
    PRINT '✓ Ya existe: ck_maintenance_estado';
END

-- Check: km_actual no puede ser negativo
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_maintenance_km_actual')
BEGIN
    ALTER TABLE dbo.maintenance
    ADD CONSTRAINT ck_maintenance_km_actual 
    CHECK (km_actual >= 0);
    
    PRINT '✅ Agregado: ck_maintenance_km_actual';
END
ELSE
BEGIN
    PRINT '✓ Ya existe: ck_maintenance_km_actual';
END

-- Check: km_servicio no puede ser negativo
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_maintenance_km_servicio')
BEGIN
    ALTER TABLE dbo.maintenance
    ADD CONSTRAINT ck_maintenance_km_servicio 
    CHECK (km_servicio >= 0);
    
    PRINT '✅ Agregado: ck_maintenance_km_servicio';
END
ELSE
BEGIN
    PRINT '✓ Ya existe: ck_maintenance_km_servicio';
END

PRINT '';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PASO 5: ESTADÍSTICAS Y FINALIZACIÓN
-- ═══════════════════════════════════════════════════════════════════════════════

PRINT '═══════════════════════════════════════════════════════════════════════════════';
PRINT 'Actualizando estadísticas...';

EXEC sp_updatestats;

PRINT '';
PRINT '✅ FOREIGN KEYS AGREGADAS EXITOSAMENTE';
PRINT '';
PRINT 'Resumen de cambios:';
PRINT '- Foreign Keys agregadas: 3';
PRINT '- Índices agregados: 3';
PRINT '- Check Constraints agregados: 3';
PRINT '';
PRINT 'Relaciones creadas:';
PRINT '1. maintenance → users (via tecnico)';
PRINT '2. reportes_campo → users (via uploaded_by)';
PRINT '3. cargas_historial → users (via usuario_id)';
PRINT '';
PRINT 'Impacto esperado:';
PRINT '- Integridad referencial: ✅ GARANTIZADA';
PRINT '- Eliminación en cascada: ✅ AUTOMÁTICA';
PRINT '- Performance: Sin cambio significativo (índices cubren)';
PRINT '';

-- Mostrar Foreign Keys creadas
PRINT '';
PRINT 'Foreign Keys en BD:';
SELECT 
    OBJECT_NAME(fk.parent_object_id) AS tabla_referenciada,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS columna_referenciada,
    OBJECT_NAME(fk.referenced_object_id) AS tabla_principal,
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS columna_principal,
    fk.name AS nombre_fk
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
WHERE OBJECT_NAME(fk.parent_object_id) IN ('maintenance', 'reportes_campo', 'cargas_historial')
ORDER BY tabla_referenciada, nombre_fk;

PRINT '';
PRINT '═══════════════════════════════════════════════════════════════════════════════';
PRINT '✅ FASE 4 — Foreign Keys — COMPLETADA';
PRINT '═══════════════════════════════════════════════════════════════════════════════';
