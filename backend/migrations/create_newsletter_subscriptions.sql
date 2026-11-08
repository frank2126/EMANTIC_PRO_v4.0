-- ═══════════════════════════════════════════════════════════════════
--  EMANTIC — Suscripciones a correos técnicos (footer + preferencias)
--  Script para SQL Server. Es opcional: si no lo ejecutas, SQLAlchemy
--  crea la tabla sola al iniciar (Base.metadata.create_all en init_db).
-- ═══════════════════════════════════════════════════════════════════

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'newsletter_subscriptions')
BEGIN
    CREATE TABLE newsletter_subscriptions (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        user_id         VARCHAR(36)   NULL,                       -- users.id (la tabla de usuarios usa GUID en texto, no INT)
        email           VARCHAR(255)  NOT NULL,                   -- siempre en minúsculas
        accepted_terms  BIT           NOT NULL DEFAULT 0,
        is_active       BIT           NOT NULL DEFAULT 1,         -- 1 = recibe correos
        role            VARCHAR(50)   NOT NULL DEFAULT 'Externo', -- 'Tecnico' | 'Administrador' | 'Externo'
        created_at      DATETIME2     NOT NULL DEFAULT GETDATE(),
        updated_at      DATETIME2     NOT NULL DEFAULT GETDATE(),
        unsubscribed_at DATETIME2     NULL,
        CONSTRAINT uq_newsletter_email UNIQUE (email),
        CONSTRAINT fk_newsletter_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )
    CREATE INDEX idx_newsletter_active ON newsletter_subscriptions(is_active)
    CREATE INDEX idx_newsletter_user   ON newsletter_subscriptions(user_id)
    PRINT 'Tabla newsletter_subscriptions creada'
END
ELSE
    PRINT 'La tabla newsletter_subscriptions ya existe'
GO
