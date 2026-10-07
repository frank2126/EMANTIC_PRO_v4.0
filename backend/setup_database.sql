
-- EMANTIX PRO — Script SQL Server

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'EmantixDB')
BEGIN
    CREATE DATABASE EmantixDB;
    PRINT '✅ Base de datos EmantixDB creada';
END
ELSE
    PRINT '⚠️  EmantixDB ya existe — continuando...';
GO

USE EmantixDB;
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
BEGIN
    CREATE TABLE users (
        id         NVARCHAR(36)  PRIMARY KEY,
        username   NVARCHAR(100) UNIQUE NOT NULL,
        password   NVARCHAR(256) NOT NULL,
        name       NVARCHAR(200) NOT NULL,
        email      NVARCHAR(200) DEFAULT '',
        role       NVARCHAR(50)  DEFAULT 'tecnico',
        active     BIT           DEFAULT 1,
        created_at DATETIME      DEFAULT GETDATE()
    );
    PRINT '✅ Tabla users creada';
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='manuals' AND xtype='U')
BEGIN
    CREATE TABLE manuals (
        id          NVARCHAR(36)  PRIMARY KEY,
        title       NVARCHAR(300) NOT NULL,
        description NVARCHAR(MAX) DEFAULT '',
        category    NVARCHAR(100) DEFAULT 'General',
        filename    NVARCHAR(400) DEFAULT '',
        url         NVARCHAR(500) DEFAULT '',
        size_mb     NVARCHAR(20)  DEFAULT '0',
        uploaded_by NVARCHAR(100) DEFAULT '',
        uploaded_at NVARCHAR(50)  DEFAULT '',
        active      BIT           DEFAULT 1
    );
    PRINT '✅ Tabla manuals creada';
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='documents' AND xtype='U')
BEGIN
    CREATE TABLE documents (
        id          NVARCHAR(36)  PRIMARY KEY,
        title       NVARCHAR(300) NOT NULL,
        category    NVARCHAR(100) DEFAULT 'General',
        filename    NVARCHAR(400) DEFAULT '',
        url         NVARCHAR(500) DEFAULT '',
        ext         NVARCHAR(20)  DEFAULT 'FILE',
        size_kb     NVARCHAR(20)  DEFAULT '0',
        uploaded_by NVARCHAR(100) DEFAULT '',
        uploaded_at NVARCHAR(50)  DEFAULT ''
    );
    PRINT '✅ Tabla documents creada';
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='maintenance' AND xtype='U')
BEGIN
    CREATE TABLE maintenance (
        id          NVARCHAR(36)  PRIMARY KEY,
        unidad      NVARCHAR(100) NOT NULL,
        tipo        NVARCHAR(200) NOT NULL,
        km_actual   INT           DEFAULT 0,
        km_servicio INT           DEFAULT 0,
        fecha       NVARCHAR(20)  DEFAULT '',
        estado      NVARCHAR(50)  DEFAULT 'Programado',
        tecnico     NVARCHAR(100) DEFAULT '',
        created_at  DATETIME      DEFAULT GETDATE()
    );
    PRINT '✅ Tabla maintenance creada';
END
 