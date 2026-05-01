from django.conf import settings
import os

keys = [
    "GRC_ENCRYPTION_KEY",
    "GRC_ENCRYPTION_KEYS",
    "TPRM_ENCRYPTION_KEY",
    "DATA_ENCRYPTION_KEY",
    "VENDOR_ENCRYPTION_KEY"
]

for k in keys:
    val = getattr(settings, k, None)
    env_val = os.environ.get(k)
    print(f"{k}: Settings={bool(val)}, Env={bool(env_val)}")
