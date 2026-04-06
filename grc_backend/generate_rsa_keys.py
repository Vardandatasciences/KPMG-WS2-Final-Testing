import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def generate_key_pair():
    """Generate a new RSA key pair for RS256 JWT signing."""
    print("Generating new RSA key pair for RS256...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Serialize private key to PEM
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Generate public key
    public_key = private_key.public_key()
    
    # Serialize public key to PEM
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    # Format for .env (preserving newlines as \n literal)
    env_private = private_pem.replace('\n', '\\n')
    env_public = public_pem.replace('\n', '\\n')
    
    print("\nNew keys generated successfully!")
    print("\n--- COPY THESE TO YOUR .env FILE ---")
    print("\nJWT_ALGORITHM=RS256")
    print(f"\nJWT_PRIVATE_KEY=\"{env_private}\"")
    print(f"\nJWT_PUBLIC_KEY=\"{env_public}\"")
    print("\n-------------------------------------")
    print("\n> IMPORTANT: After updating .env, all current sessions will be invalidated.")

if __name__ == "__main__":
    generate_key_pair()
