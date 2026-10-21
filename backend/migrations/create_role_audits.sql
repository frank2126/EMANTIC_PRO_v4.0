
--— Tabla de Auditoría de Cambios de Roles


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
