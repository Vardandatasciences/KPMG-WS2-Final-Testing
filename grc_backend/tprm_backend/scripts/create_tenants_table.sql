-- ============================================================================
-- Create Tenants Table for TPRM Multi-Tenancy
-- This matches the GRC tenants table schema exactly for consistency
-- ============================================================================

CREATE TABLE IF NOT EXISTS `tenants` (
  `TenantId` int NOT NULL AUTO_INCREMENT,
  `Name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Subdomain` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `LicenseKey` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `SubscriptionTier` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'starter',
  `Status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'trial',
  `MaxUsers` int NOT NULL DEFAULT '10',
  `StorageLimitGB` int NOT NULL DEFAULT '10',
  `CreatedAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `UpdatedAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `TrialEndsAt` datetime(6) DEFAULT NULL,
  `Settings` json NOT NULL,
  `PrimaryContactEmail` varchar(254) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `PrimaryContactName` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `PrimaryContactPhone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`TenantId`),
  UNIQUE KEY `uniq_tenants_subdomain` (`Subdomain`),
  UNIQUE KEY `uniq_tenants_licensekey` (`LicenseKey`),
  KEY `idx_tenants_status` (`Status`),
  CONSTRAINT `chk_tenants_status` CHECK ((`Status` in (_utf8mb4'trial',_utf8mb4'active',_utf8mb4'suspended',_utf8mb4'cancelled'))),
  CONSTRAINT `chk_tenants_subscriptiontier` CHECK ((`SubscriptionTier` in (_utf8mb4'starter',_utf8mb4'professional',_utf8mb4'enterprise')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verify table creation
SELECT * FROM tenants LIMIT 1;

