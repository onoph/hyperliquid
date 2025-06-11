-- =====================================================
-- Script de création de base de données Trading
-- Base de données pour Hyperliquid Observer API
-- =====================================================

-- Création de la base de données (optionnel)
-- CREATE DATABASE IF NOT EXISTS hyperliquid_trading;
-- USE hyperliquid_trading;

-- =====================================================
-- 1. TABLE DES ORDRES (ORDERS)
-- =====================================================

CREATE TABLE IF NOT EXISTS orders (
    -- ID technique
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Informations de base
    order_id VARCHAR(255) NOT NULL UNIQUE COMMENT 'ID unique de l\'ordre (oid)',
    client_order_id VARCHAR(255) NULL COMMENT 'ID client optionnel (cloid)',
    
    -- Dates et timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date d\'insertion en DB',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    order_timestamp BIGINT NOT NULL COMMENT 'Timestamp original de l\'ordre',
    order_datetime DATETIME NOT NULL COMMENT 'Date/heure lisible de l\'ordre',
    last_trade_timestamp BIGINT NULL,
    last_update_timestamp BIGINT NULL,
    
    -- Informations de trading
    symbol VARCHAR(50) NOT NULL COMMENT 'Symbole tradé (ex: BTC-USD)',
    coin VARCHAR(20) NOT NULL COMMENT 'Coin tradé (ex: BTC)',
    side ENUM('buy', 'sell') NOT NULL COMMENT 'Direction de l\'ordre',
    order_type ENUM('market', 'limit', 'stop', 'stop_limit') NOT NULL COMMENT 'Type d\'ordre',
    time_in_force VARCHAR(10) NOT NULL DEFAULT 'GTC' COMMENT 'TIF (GTC, IOC, FOK)',
    
    -- Prix et quantités
    price DECIMAL(20, 8) NOT NULL COMMENT 'Prix de l\'ordre',
    trigger_price DECIMAL(20, 8) NULL COMMENT 'Prix de déclenchement (stop orders)',
    amount DECIMAL(20, 8) NOT NULL COMMENT 'Quantité totale',
    filled DECIMAL(20, 8) NOT NULL DEFAULT 0 COMMENT 'Quantité exécutée',
    remaining DECIMAL(20, 8) NOT NULL COMMENT 'Quantité restante',
    cost DECIMAL(20, 8) NOT NULL DEFAULT 0 COMMENT 'Coût total',
    average_price DECIMAL(20, 8) NULL COMMENT 'Prix moyen d\'exécution',
    
    -- Status et flags
    status ENUM('open', 'closed', 'canceled', 'expired', 'rejected', 'pending') NOT NULL COMMENT 'Statut de l\'ordre',
    post_only BOOLEAN NOT NULL DEFAULT FALSE,
    reduce_only BOOLEAN NOT NULL DEFAULT FALSE,
    is_trigger BOOLEAN NOT NULL DEFAULT FALSE,
    is_position_tpsl BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Prix stop loss / take profit
    stop_price DECIMAL(20, 8) NULL,
    take_profit_price DECIMAL(20, 8) NULL,
    stop_loss_price DECIMAL(20, 8) NULL,
    
    -- Informations supplémentaires
    original_size VARCHAR(50) NULL COMMENT 'Taille originale (format string)',
    trigger_condition VARCHAR(50) NULL,
    wallet_address VARCHAR(42) NOT NULL COMMENT 'Adresse du wallet observé',
    
    -- Fees (JSON pour flexibilité)
    fees JSON NULL COMMENT 'Détails des frais en format JSON',
    
    -- Index pour performance
    INDEX idx_order_id (order_id),
    INDEX idx_wallet_address (wallet_address),
    INDEX idx_symbol (symbol),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_order_timestamp (order_timestamp),
    INDEX idx_symbol_status (symbol, status),
    INDEX idx_wallet_symbol (wallet_address, symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Table des ordres de trading Hyperliquid';

-- =====================================================
-- 2. TABLE DES POSITIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS positions (
    -- ID technique
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Informations de base
    position_id VARCHAR(255) NOT NULL COMMENT 'ID unique de la position (wallet+coin)',
    wallet_address VARCHAR(42) NOT NULL COMMENT 'Adresse du wallet',
    coin VARCHAR(20) NOT NULL COMMENT 'Coin de la position',
    
    -- Dates et timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date d\'insertion en DB',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    opened_at DATETIME NOT NULL COMMENT 'Date d\'ouverture de la position',
    closed_at DATETIME NULL COMMENT 'Date de fermeture (si fermée)',
    
    -- Status de la position
    status ENUM('open', 'closed') NOT NULL DEFAULT 'open' COMMENT 'Statut: ouvert ou fermé',
    
    -- Informations de trading
    side ENUM('long', 'short') NOT NULL COMMENT 'Direction de la position',
    size DECIMAL(20, 8) NOT NULL COMMENT 'Taille de la position (szi)',
    entry_price DECIMAL(20, 8) NOT NULL COMMENT 'Prix d\'entrée moyen',
    exit_price DECIMAL(20, 8) NULL COMMENT 'Prix de sortie moyen (si fermée)',
    
    -- Valeurs et PnL
    position_value DECIMAL(20, 8) NOT NULL COMMENT 'Valeur de la position',
    unrealized_pnl DECIMAL(20, 8) NOT NULL DEFAULT 0 COMMENT 'PnL non réalisé',
    realized_pnl DECIMAL(20, 8) NULL COMMENT 'PnL réalisé (si fermée)',
    return_on_equity DECIMAL(10, 6) NOT NULL DEFAULT 0 COMMENT 'ROE en pourcentage',
    
    -- Gestion du risque
    leverage_type VARCHAR(20) NOT NULL COMMENT 'Type de levier (cross/isolated)',
    leverage_value DECIMAL(10, 2) NOT NULL COMMENT 'Valeur du levier',
    liquidation_price DECIMAL(20, 8) NOT NULL COMMENT 'Prix de liquidation',
    margin_used DECIMAL(20, 8) NOT NULL COMMENT 'Marge utilisée',
    max_leverage DECIMAL(10, 2) NOT NULL COMMENT 'Levier maximum',
    
    -- Funding
    cum_funding_all_time DECIMAL(20, 8) NOT NULL DEFAULT 0,
    cum_funding_since_open DECIMAL(20, 8) NOT NULL DEFAULT 0,
    cum_funding_since_change DECIMAL(20, 8) NOT NULL DEFAULT 0,
    
    -- Métadonnées
    last_update_timestamp BIGINT NOT NULL COMMENT 'Dernier timestamp de mise à jour',
    
    -- Contraintes d'unicité
    UNIQUE KEY unique_wallet_coin_open (wallet_address, coin, status),
    
    -- Index pour performance
    INDEX idx_position_id (position_id),
    INDEX idx_wallet_address (wallet_address),
    INDEX idx_coin (coin),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_opened_at (opened_at),
    INDEX idx_closed_at (closed_at),
    INDEX idx_wallet_coin (wallet_address, coin),
    INDEX idx_status_wallet (status, wallet_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Table des positions de trading Hyperliquid';

-- =====================================================
-- 3. TABLE DE LIAISON ORDRES-POSITIONS (optionnelle)
-- =====================================================

CREATE TABLE IF NOT EXISTS order_position_relations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    position_id BIGINT NOT NULL,
    relation_type ENUM('open', 'close', 'modify') NOT NULL COMMENT 'Type de relation',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE,
    UNIQUE KEY unique_order_position (order_id, position_id, relation_type),
    INDEX idx_order_id (order_id),
    INDEX idx_position_id (position_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Relations entre ordres et positions';

-- =====================================================
-- 4. TABLE DE LOG DES ÉVÉNEMENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS trading_events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    event_type ENUM('order_created', 'order_filled', 'order_canceled', 'position_opened', 'position_closed', 'position_updated') NOT NULL,
    wallet_address VARCHAR(42) NOT NULL,
    reference_id VARCHAR(255) NOT NULL COMMENT 'ID de référence (order_id ou position_id)',
    event_data JSON NULL COMMENT 'Données complètes de l\'événement',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_timestamp BIGINT NOT NULL,
    
    INDEX idx_event_type (event_type),
    INDEX idx_wallet_address (wallet_address),
    INDEX idx_created_at (created_at),
    INDEX idx_event_timestamp (event_timestamp),
    INDEX idx_wallet_type (wallet_address, event_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Log de tous les événements de trading';

-- =====================================================
-- 5. VUES UTILES
-- =====================================================

-- Vue des positions ouvertes avec PnL actuel
CREATE OR REPLACE VIEW open_positions AS
SELECT 
    p.*,
    TIMESTAMPDIFF(HOUR, p.opened_at, NOW()) as hours_open,
    CASE 
        WHEN p.side = 'long' THEN (p.position_value - (p.size * p.entry_price))
        WHEN p.side = 'short' THEN ((p.size * p.entry_price) - p.position_value)
    END as calculated_pnl
FROM positions p 
WHERE p.status = 'open';

-- Vue des ordres actifs
CREATE OR REPLACE VIEW active_orders AS
SELECT 
    o.*,
    TIMESTAMPDIFF(MINUTE, o.order_datetime, NOW()) as minutes_active
FROM orders o 
WHERE o.status IN ('open', 'pending');

-- Vue résumé par wallet
CREATE OR REPLACE VIEW wallet_summary AS
SELECT 
    wallet_address,
    COUNT(CASE WHEN status = 'open' THEN 1 END) as open_positions,
    COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_positions,
    SUM(CASE WHEN status = 'open' THEN unrealized_pnl ELSE 0 END) as total_unrealized_pnl,
    SUM(CASE WHEN status = 'closed' THEN realized_pnl ELSE 0 END) as total_realized_pnl,
    MAX(updated_at) as last_activity
FROM positions 
GROUP BY wallet_address;

-- =====================================================
-- 6. PROCÉDURES STOCKÉES UTILES
-- =====================================================

DELIMITER //

-- Procédure pour fermer une position
CREATE PROCEDURE ClosePosition(
    IN p_position_id BIGINT,
    IN p_exit_price DECIMAL(20,8),
    IN p_realized_pnl DECIMAL(20,8)
)
BEGIN
    UPDATE positions 
    SET 
        status = 'closed',
        closed_at = NOW(),
        exit_price = p_exit_price,
        realized_pnl = p_realized_pnl,
        updated_at = NOW()
    WHERE id = p_position_id AND status = 'open';
END //

-- Procédure pour mettre à jour une position
CREATE PROCEDURE UpdatePosition(
    IN p_position_id BIGINT,
    IN p_size DECIMAL(20,8),
    IN p_position_value DECIMAL(20,8),
    IN p_unrealized_pnl DECIMAL(20,8),
    IN p_timestamp BIGINT
)
BEGIN
    UPDATE positions 
    SET 
        size = p_size,
        position_value = p_position_value,
        unrealized_pnl = p_unrealized_pnl,
        last_update_timestamp = p_timestamp,
        updated_at = NOW()
    WHERE id = p_position_id;
END //

DELIMITER ;

-- =====================================================
-- 7. INSERTION DE DONNÉES DE TEST (OPTIONNEL)
-- =====================================================

-- Exemple d'insertion d'un ordre
/*
INSERT INTO orders (
    order_id, symbol, coin, side, order_type, price, amount, 
    remaining, status, order_timestamp, order_datetime, wallet_address
) VALUES (
    '12345', 'BTC-USD', 'BTC', 'buy', 'limit', 50000.00, 0.1, 
    0.1, 'open', UNIX_TIMESTAMP() * 1000, NOW(), '0x1234567890abcdef1234567890abcdef12345678'
);
*/

-- Exemple d'insertion d'une position
/*
INSERT INTO positions (
    position_id, wallet_address, coin, side, size, entry_price, 
    position_value, unrealized_pnl, leverage_type, leverage_value, 
    liquidation_price, margin_used, max_leverage, opened_at, last_update_timestamp
) VALUES (
    'wallet123_BTC', '0x1234567890abcdef1234567890abcdef12345678', 'BTC', 'long', 
    0.1, 50000.00, 5000.00, 100.00, 'cross', 10.00, 45000.00, 500.00, 20.00, 
    NOW(), UNIX_TIMESTAMP() * 1000
);
*/

-- =====================================================
-- SCRIPT TERMINÉ
-- =====================================================

-- Pour vérifier que tout est créé correctement :
-- SHOW TABLES;
-- DESCRIBE orders;
-- DESCRIBE positions; 