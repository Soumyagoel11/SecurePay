-- ============================================================================
-- SecurePay : MySQL database schema
-- ============================================================================
-- Run as:  mysql -u root -p securepay < schema.sql
-- The Flask app can also auto-create tables via SQLAlchemy (works for SQLite
-- out of the box and for MySQL once this schema/database exists).
-- ============================================================================

CREATE DATABASE IF NOT EXISTS securepay
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE securepay;

-- ---------------------------------------------------------------------------
-- Users (shared authentication entity for all roles)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  user_id      INT AUTO_INCREMENT PRIMARY KEY,
  email        VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role         VARCHAR(20)  NOT NULL,                 -- admin | merchant | customer
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_users_email (email),
  INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Customers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
  customer_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT NOT NULL UNIQUE,
  phone       VARCHAR(20),
  address     VARCHAR(255),
  customer_age INT,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  INDEX idx_customers_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Merchants
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS merchants (
  merchant_id   INT AUTO_INCREMENT PRIMARY KEY,
  user_id       INT NOT NULL UNIQUE,
  company_name  VARCHAR(255) NOT NULL,
  business_type VARCHAR(100),
  merchant_risk FLOAT NOT NULL DEFAULT 0.1,          -- historical fraud rate
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  INDEX idx_merchants_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Admins
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
  admin_id   INT AUTO_INCREMENT PRIMARY KEY,
  user_id   INT NOT NULL UNIQUE,
  department VARCHAR(100),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  INDEX idx_admins_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Wallets
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS wallets (
  wallet_id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL UNIQUE,
  balance   FLOAT NOT NULL DEFAULT 0.0,
  status    VARCHAR(20) NOT NULL DEFAULT 'active',    -- active | frozen
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
  INDEX idx_wallets_customer (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Payments
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
  payment_id    INT AUTO_INCREMENT PRIMARY KEY,
  customer_id   INT NOT NULL,
  merchant_id   INT NOT NULL,
  amount        FLOAT NOT NULL,
  payment_date  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status        VARCHAR(20) NOT NULL DEFAULT 'pending',
  risk_score    FLOAT,
  fraud_flag    BOOLEAN,
  fraud_decision VARCHAR(20),                          -- Safe | Suspicious
  failure_reason VARCHAR(255),
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
  FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id) ON DELETE CASCADE,
  INDEX idx_payments_customer (customer_id),
  INDEX idx_payments_merchant (merchant_id),
  INDEX idx_payments_date (payment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Transactions (wallet ledger)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id INT AUTO_INCREMENT PRIMARY KEY,
  payment_id     INT,
  wallet_id      INT,
  type           VARCHAR(20) NOT NULL,                -- debit | credit | refund | add_money
  amount         FLOAT NOT NULL,
  status         VARCHAR(20) NOT NULL DEFAULT 'completed',
  timestamp      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  description    VARCHAR(255),
  FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE SET NULL,
  FOREIGN KEY (wallet_id)  REFERENCES wallets(wallet_id) ON DELETE SET NULL,
  INDEX idx_txn_payment (payment_id),
  INDEX idx_txn_wallet (wallet_id),
  INDEX idx_txn_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Fraud detections (one per payment)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fraud_detections (
  fraud_id      INT AUTO_INCREMENT PRIMARY KEY,
  payment_id    INT NOT NULL UNIQUE,
  prediction    VARCHAR(20) NOT NULL,                 -- Safe | Suspicious
  risk_score    FLOAT NOT NULL,
  model_version VARCHAR(50),
  model_name    VARCHAR(50),
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE CASCADE,
  INDEX idx_fraud_payment (payment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Refunds (one per payment)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS refunds (
  refund_id   INT AUTO_INCREMENT PRIMARY KEY,
  payment_id  INT NOT NULL UNIQUE,
  customer_id INT NOT NULL,
  amount      FLOAT NOT NULL,
  reason      VARCHAR(255),
  status      VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
  admin_id    INT,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at DATETIME,
  FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
  FOREIGN KEY (admin_id)    REFERENCES admins(admin_id) ON DELETE SET NULL,
  INDEX idx_refunds_payment (payment_id),
  INDEX idx_refunds_customer (customer_id),
  INDEX idx_refunds_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- QR Payments (QR checkout sessions for Google Lens / camera scanning)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS qr_payments (
  qr_id       INT AUTO_INCREMENT PRIMARY KEY,
  token       VARCHAR(64) NOT NULL UNIQUE,
  merchant_id INT NOT NULL,
  customer_id INT,
  payment_id  INT,
  amount      FLOAT NOT NULL DEFAULT 0.0,
  description VARCHAR(255) DEFAULT 'QR Payment',
  status      VARCHAR(30) NOT NULL DEFAULT 'pending', -- pending | completed | rejected | expired
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at  DATETIME,
  FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
  FOREIGN KEY (payment_id)  REFERENCES payments(payment_id) ON DELETE SET NULL,
  INDEX idx_qr_token (token),
  INDEX idx_qr_merchant (merchant_id),
  INDEX idx_qr_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

