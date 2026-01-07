"""
Enterprise Key Management System

Provides secure key storage and retrieval with support for:
- AWS Secrets Manager (production)
- Environment variables (staging/development)
- File-based storage (local development)

This system ensures encryption keys are never stored in code or configuration files.
"""

import logging
import os
import json
from typing import Optional, Dict
from django.conf import settings
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class KeyManagementBackend:
    """
    Base class for key management backends
    All backends must implement get_secret() method
    """
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from the key management system
        
        Args:
            secret_name: Name/identifier of the secret
            default: Default value if secret not found
            
        Returns:
            Secret value as string, or default if not found
        """
        raise NotImplementedError("Subclasses must implement get_secret()")
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Store a secret in the key management system
        
        Args:
            secret_name: Name/identifier of the secret
            secret_value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement set_secret()")


class AWSSecretsManagerBackend(KeyManagementBackend):
    """
    AWS Secrets Manager backend for production environments
    
    Requires: boto3 library and AWS credentials configured
    """
    
    def __init__(self, region_name: Optional[str] = None):
        """
        Initialize AWS Secrets Manager backend
        
        Args:
            region_name: AWS region (defaults to environment variable or 'us-east-1')
        """
        self.region_name = region_name or os.environ.get('AWS_REGION', 'us-east-1')
        self._client = None
    
    def _get_client(self):
        """Get or create AWS Secrets Manager client (lazy loading)"""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client('secretsmanager', region_name=self.region_name)
                logger.info(f"AWS Secrets Manager client initialized for region: {self.region_name}")
            except ImportError:
                logger.error("boto3 library not installed. Install with: pip install boto3")
                raise ImportError("boto3 is required for AWS Secrets Manager backend")
            except Exception as e:
                logger.error(f"Failed to initialize AWS Secrets Manager client: {str(e)}")
                raise
        
        return self._client
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve secret from AWS Secrets Manager
        
        Args:
            secret_name: Full secret name/ARN
            default: Default value if secret not found
            
        Returns:
            Secret value as string, or default if not found
        """
        try:
            client = self._get_client()
            response = client.get_secret_value(SecretId=secret_name)
            
            # Secrets Manager can store secrets as JSON or plain text
            secret_string = response.get('SecretString', '')
            
            # Try to parse as JSON (for structured secrets)
            try:
                secret_dict = json.loads(secret_string)
                # If it's a JSON object, try to get the secret_name key, or use 'value'
                if isinstance(secret_dict, dict):
                    return secret_dict.get(secret_name.split('/')[-1], secret_dict.get('value', secret_string))
            except (json.JSONDecodeError, KeyError):
                # If not JSON or key not found, return as-is (plain text)
                pass
            
            return secret_string
            
        except client.exceptions.ResourceNotFoundException:
            logger.warning(f"Secret '{secret_name}' not found in AWS Secrets Manager. Using default.")
            return default
        except client.exceptions.DecryptionFailureException:
            logger.error(f"Failed to decrypt secret '{secret_name}' from AWS Secrets Manager")
            return default
        except Exception as e:
            logger.error(f"Error retrieving secret '{secret_name}' from AWS Secrets Manager: {str(e)}")
            return default
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Store secret in AWS Secrets Manager
        
        Args:
            secret_name: Full secret name/ARN
            secret_value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            
            # Try to update existing secret
            try:
                client.update_secret(SecretId=secret_name, SecretString=secret_value)
                logger.info(f"Updated secret '{secret_name}' in AWS Secrets Manager")
            except client.exceptions.ResourceNotFoundException:
                # Secret doesn't exist, create it
                client.create_secret(Name=secret_name, SecretString=secret_value)
                logger.info(f"Created secret '{secret_name}' in AWS Secrets Manager")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing secret '{secret_name}' in AWS Secrets Manager: {str(e)}")
            return False


class EnvironmentBackend(KeyManagementBackend):
    """
    Environment variable backend (fallback/staging)
    
    Reads secrets from environment variables
    """
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve secret from environment variable
        
        Args:
            secret_name: Environment variable name
            default: Default value if not found
            
        Returns:
            Secret value from environment, or default
        """
        value = os.environ.get(secret_name, default)
        if value:
            logger.debug(f"Retrieved secret '{secret_name}' from environment variable")
        return value
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Store secret in environment variable (runtime only)
        
        Note: This only sets it for current process, not persistent
        
        Args:
            secret_name: Environment variable name
            secret_value: Value to store
            
        Returns:
            True (always succeeds for environment variables)
        """
        os.environ[secret_name] = secret_value
        logger.debug(f"Set environment variable '{secret_name}' (runtime only)")
        return True


class FileBackend(KeyManagementBackend):
    """
    File-based backend for local development
    
    WARNING: NOT SECURE for production! Use only for local development.
    """
    
    def __init__(self, secrets_dir: Optional[str] = None):
        """
        Initialize file-based backend
        
        Args:
            secrets_dir: Directory to store secrets (defaults to project root/.secrets)
        """
        if secrets_dir is None:
            from pathlib import Path
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            secrets_dir = base_dir / '.secrets'
        
        self.secrets_dir = secrets_dir
        self.secrets_dir.mkdir(mode=0o700, exist_ok=True)  # Create with restrictive permissions
        logger.warning(f"Using file-based key storage at {secrets_dir} (NOT SECURE for production!)")
    
    def _get_secret_path(self, secret_name: str) -> str:
        """Get file path for a secret"""
        # Sanitize secret name to prevent directory traversal
        safe_name = secret_name.replace('/', '_').replace('\\', '_')
        return str(self.secrets_dir / safe_name)
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve secret from file
        
        Args:
            secret_name: Secret identifier
            default: Default value if not found
            
        Returns:
            Secret value from file, or default
        """
        secret_path = self._get_secret_path(secret_name)
        
        try:
            if os.path.exists(secret_path):
                with open(secret_path, 'r') as f:
                    value = f.read().strip()
                    logger.debug(f"Retrieved secret '{secret_name}' from file")
                    return value
        except Exception as e:
            logger.error(f"Error reading secret file '{secret_path}': {str(e)}")
        
        return default
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Store secret in file
        
        Args:
            secret_name: Secret identifier
            secret_value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        secret_path = self._get_secret_path(secret_name)
        
        try:
            # Write with restrictive permissions (owner read/write only)
            with open(secret_path, 'w') as f:
                f.write(secret_value)
            os.chmod(secret_path, 0o600)  # rw-------
            logger.debug(f"Stored secret '{secret_name}' in file")
            return True
        except Exception as e:
            logger.error(f"Error writing secret file '{secret_path}': {str(e)}")
            return False


class EnterpriseKeyManager:
    """
    Enterprise Key Management System
    
    Provides unified interface for key management with multiple backends.
    Tries backends in order of preference (most secure first).
    """
    
    # Standard secret names
    ENCRYPTION_KEY_NAME = 'GRC_ENCRYPTION_KEY'
    JWT_SECRET_KEY_NAME = 'JWT_SECRET_KEY'
    DJANGO_SECRET_KEY_NAME = 'DJANGO_SECRET_KEY'
    
    def __init__(self):
        """Initialize key manager with configured backends"""
        self.backends = self._initialize_backends()
        logger.info(f"Enterprise Key Manager initialized with {len(self.backends)} backend(s)")
    
    def _initialize_backends(self) -> list:
        """
        Initialize key management backends in order of preference
        
        Returns:
            List of backend instances in priority order
        """
        backends = []
        
        # 1. AWS Secrets Manager (production - most secure)
        use_aws = getattr(settings, 'USE_AWS_SECRETS_MANAGER', False)
        if use_aws or os.environ.get('USE_AWS_SECRETS_MANAGER', '').lower() == 'true':
            try:
                aws_backend = AWSSecretsManagerBackend()
                backends.append(aws_backend)
                logger.info("AWS Secrets Manager backend enabled")
            except Exception as e:
                logger.warning(f"AWS Secrets Manager backend failed to initialize: {str(e)}")
        
        # 2. Environment variables (staging/development - secure enough)
        env_backend = EnvironmentBackend()
        backends.append(env_backend)
        
        # 3. File-based (local development only - NOT secure)
        is_production = not getattr(settings, 'DEBUG', True)
        if not is_production:
            try:
                file_backend = FileBackend()
                backends.append(file_backend)
                logger.info("File-based backend enabled (development only)")
            except Exception as e:
                logger.warning(f"File-based backend failed to initialize: {str(e)}")
        
        if not backends:
            raise RuntimeError("No key management backends available!")
        
        return backends
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve secret from key management system
        
        Tries backends in order until one succeeds
        
        Args:
            secret_name: Name/identifier of the secret
            default: Default value if secret not found in any backend
            
        Returns:
            Secret value, or default if not found
        """
        for backend in self.backends:
            try:
                value = backend.get_secret(secret_name, None)
                if value:
                    logger.debug(f"Retrieved '{secret_name}' from {backend.__class__.__name__}")
                    return value
            except Exception as e:
                logger.warning(f"Backend {backend.__class__.__name__} failed for '{secret_name}': {str(e)}")
                continue
        
        logger.warning(f"Secret '{secret_name}' not found in any backend, using default")
        return default
    
    def set_secret(self, secret_name: str, secret_value: str, backend_index: int = 0) -> bool:
        """
        Store secret in key management system
        
        Stores in the first available backend (usually the most secure)
        
        Args:
            secret_name: Name/identifier of the secret
            secret_value: Value to store
            backend_index: Which backend to use (0 = first/most secure)
            
        Returns:
            True if successful, False otherwise
        """
        if backend_index >= len(self.backends):
            logger.error(f"Backend index {backend_index} out of range")
            return False
        
        backend = self.backends[backend_index]
        try:
            success = backend.set_secret(secret_name, secret_value)
            if success:
                logger.info(f"Stored '{secret_name}' in {backend.__class__.__name__}")
            return success
        except Exception as e:
            logger.error(f"Failed to store '{secret_name}' in {backend.__class__.__name__}: {str(e)}")
            return False
    
    def get_encryption_key(self) -> Optional[bytes]:
        """
        Get encryption key for data encryption
        
        Returns:
            Encryption key as bytes, or None if not found
        """
        # Try standard names
        key_names = [
            self.ENCRYPTION_KEY_NAME,
            'ENCRYPTION_KEY',
            'GRC_ENCRYPTION_KEY',
        ]
        
        for key_name in key_names:
            key_string = self.get_secret(key_name)
            if key_string:
                # Convert string to bytes if needed
                if isinstance(key_string, str):
                    key_string = key_string.encode()
                return key_string
        
        return None
    
    def get_jwt_secret_key(self) -> Optional[str]:
        """
        Get JWT secret key
        
        Returns:
            JWT secret key as string, or None if not found
        """
        return self.get_secret(self.JWT_SECRET_KEY_NAME) or self.get_secret('JWT_SECRET_KEY')
    
    def get_django_secret_key(self) -> Optional[str]:
        """
        Get Django secret key
        
        Returns:
            Django secret key as string, or None if not found
        """
        return self.get_secret(self.DJANGO_SECRET_KEY_NAME) or self.get_secret('SECRET_KEY')


# Global instance
_key_manager = None


def get_key_manager() -> EnterpriseKeyManager:
    """Get or create global key manager instance"""
    global _key_manager
    if _key_manager is None:
        _key_manager = EnterpriseKeyManager()
    return _key_manager


# Convenience functions
def get_encryption_key() -> Optional[bytes]:
    """Get encryption key (convenience function)"""
    return get_key_manager().get_encryption_key()


def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """Get secret (convenience function)"""
    return get_key_manager().get_secret(secret_name, default)


