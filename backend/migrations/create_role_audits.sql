-- ═══════════════════════════════════════════════════════════════════
--  EMANTIC PRO — Tabla de Auditoría de Cambios de Roles
--  Script para SQL Server
-- ═══════════════════════════════════════════════════════════════════

-- Crear tabla role_audits
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'role_audits')
BEGIN
    CREATE TABLE role_audits (
        id VARCHAR(36) PRIMARY KEY NOT NULL,
        admin_id VARCHAR(36) NOT NULL,
        admin_username VARCHAR(100) NOT NULL,
        user_id VARCHAR(36) NOT NULL,
        user_username VARCHAR(100) NOT NULL,
        old_role VARCHAR(50) NULL,
        new_role VARCHAR(50) NOT NULL,
        action VARCHAR(50) NOT NULL,
        reason NVARCHAR(MAX) DEFAULT '',
        created_at DATETIME NOT NULL DEFAULT GETUTCDATE(),
        ip_address VARCHAR(50) DEFAULT ''
    )
    
    -- Crear índices
    CREATE INDEX idx_audit_user_id ON role_audits(user_id)
    CREATE INDEX idx_audit_admin_id ON role_audits(admin_id)
    CREATE INDEX idx_audit_created_at ON role_audits(created_at)
    
    PRINT 'Tabla role_audits creada exitosamente'
END
ELSE
BEGIN
    PRINT 'Tabla role_audits ya existe'
END

-- ═══════════════════════════════════════════════════════════════════
-- Verificar que la tabla existe y tiene datos
-- ═══════════════════════════════════════════════════════════════════

SELECT 
    'Tabla role_audits' AS Tabla,
    COUNT(*) AS 'Registros',
    'OK' AS Estado
FROM role_audits
UNION ALL
SELECT 
    'Índices',
    COUNT(*),
    'OK'
FROM sys.indexes
WHERE object_id = OBJECT_ID('role_audits')

-- ═══════════════════════════════════════════════════════════════════
-- Ejemplo de auditoría manual (para testing)
-- ═══════════════════════════════════════════════════════════════════

-- INSERT INTO role_audits (
--     id, admin_id, admin_username, user_id, user_username,
--     old_role, new_role, action, reason, created_at, ip_address
-- ) VALUES (
--     LOWER(NEWID()), 
--     'admin-123', 
--     'admin',
--     'user-456',
--     'tecnico1',
--     'tecnico',
--     'admin',
--     'UPDATE',
--     'Cambio de rol de tecnico a admin',
--     GETUTCDATE(),
--     '192.168.1.100'
-- )

-- ═══════════════════════════════════════════════════════════════════
-- Consultas útiles
-- ═══════════════════════════════════════════════════════════════════

-- Ver todos los cambios de roles
-- SELECT * FROM role_audits ORDER BY created_at DESC

-- Ver cambios de un usuario específico
-- SELECT * FROM role_audits WHERE user_username = 'tecnico1' ORDER BY created_at DESC

-- Ver cambios realizados por un admin
-- SELECT * FROM role_audits WHERE admin_username = 'admin' ORDER BY created_at DESC

-- Ver resumen de cambios
-- SELECT action, COUNT(*) as total FROM role_audits GROUP BY action

-- Ver cambios en los últimos 7 días
-- SELECT * FROM role_audits WHERE created_at >= DATEADD(day, -7, GETUTCDATE()) ORDER BY created_at DESC
