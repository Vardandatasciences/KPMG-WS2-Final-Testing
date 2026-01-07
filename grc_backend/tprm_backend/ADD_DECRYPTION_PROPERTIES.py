"""
Utility script to generate _plain property code for all encrypted models.
This generates the code you need to add to each model class.
"""

from utils.encryption_config import TPRM_ENCRYPTED_FIELDS_CONFIG


def generate_plain_properties(model_name, fields):
    """Generate @property methods for decryption"""
    properties = []
    properties.append(f"    # Decryption properties for {model_name}")
    
    for field in fields:
        properties.append(f"    @property")
        properties.append(f"    def {field}_plain(self):")
        properties.append(f"        \"\"\"Get decrypted {field}\"\"\"")
        properties.append(f"        return self._get_decrypted_value('{field}')")
        properties.append("")
    
    return "\n".join(properties)


def main():
    """Generate all _plain properties"""
    print("=" * 80)
    print("DECRYPTION PROPERTIES FOR ALL TPRM MODELS")
    print("=" * 80)
    print()
    
    for model_name, fields in TPRM_ENCRYPTED_FIELDS_CONFIG.items():
        if fields:  # Only if there are fields to encrypt
            print(f"\n{'=' * 60}")
            print(f"Model: {model_name}")
            print(f"{'=' * 60}\n")
            print(generate_plain_properties(model_name, fields))


if __name__ == "__main__":
    main()

