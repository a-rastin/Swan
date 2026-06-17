#!/usr/bin/env python
"""Generate VAPID key pair for web push. Run once, copy output to .env.

VAPID_PRIVATE = urlsafe-b64 of the 32-byte P-256 private value (pywebpush accepts this).
VAPID_PUBLIC  = urlsafe-b64 of the 65-byte uncompressed point (browser applicationServerKey).
"""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


key = ec.generate_private_key(ec.SECP256R1())
priv = key.private_numbers().private_value.to_bytes(32, "big")
pub = key.public_key().public_bytes(
    serialization.Encoding.X962,
    serialization.PublicFormat.UncompressedPoint,
)

print(f"VAPID_PUBLIC={b64(pub)}")
print(f"VAPID_PRIVATE={b64(priv)}")
print("VAPID_SUBJECT=mailto:admin@yourdomain.com")
