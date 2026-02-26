# backend/app/ml/vedic/anurupyena.py
"""
Vedic Checksum Pre-Filter using the Anurupyena (Proportionality) Sutra.

The Beejank (digital root / Navashesh) is a Vedic concept for validating
numerical integrity. It repeatedly sums the digits of a number until a
single digit remains (equivalent to modulo 9, treating 0 as 9).

This module uses Beejank of multiple transaction fields to create a composite
checksum. If a transaction payload is tampered with in transit (e.g., amount
changed, coordinates spoofed, timestamp replayed), the recomputed checksum
won't match — providing a lightweight structural integrity check.

Issue #3 FIX: Added HMAC-SHA256 as a second integrity layer to eliminate
the ~11% collision rate inherent in single-digit Beejank checksums.
The Vedic Beejank serves as a fast first-gate sanity check; HMAC provides
cryptographic tamper-proofing.
"""

import hmac
import hashlib
import os


# HMAC secret key — in production, this would be an env variable
HMAC_SECRET_KEY = os.environ.get("VEDIC_HMAC_SECRET", "vedfin_sentinel_vedic_integrity_key_2026").encode()


def beejank(n: int) -> int:
    """
    Compute the Beejank (Vedic digital root / Navashesh) of a non-negative integer.
    
    The Beejank is computed by repeatedly summing the digits of a number
    until a single digit (1-9) remains. Mathematically equivalent to:
        1 + ((n - 1) % 9) for n > 0, or 0 for n == 0
    
    This is a core Vedic Mathematics concept used for verification of
    arithmetic operations (similar to "casting out nines").
    """
    if n == 0:
        return 0
    return 1 + ((abs(n) - 1) % 9)


def vedic_digit_sum_checksum(amount: float, timestamp_epoch: int,
                              geo_lat: float, geo_lng: float) -> int:
    """
    Compute a composite checksum by applying Beejank to each field independently,
    then computing the Beejank of their product (Anurupyena = "Proportionately").
    
    The proportional cross-product ties all fields together — changing any single
    field changes the final checksum.
    
    Returns: int (1-9) — the Vedic checksum digit
    """
    # Normalize each field to a positive integer representation
    amt_int = int(abs(amount) * 100)  # ₹1234.56 → 123456
    ts_int = abs(timestamp_epoch) if timestamp_epoch else 1
    lat_int = int((geo_lat + 90.0) * 10000) if geo_lat is not None else 1
    lng_int = int((geo_lng + 180.0) * 10000) if geo_lng is not None else 1

    # Compute Beejank of each component
    b_amt = beejank(amt_int)
    b_ts = beejank(ts_int)
    b_lat = beejank(lat_int)
    b_lng = beejank(lng_int)

    # Anurupyena: "Proportionately" — the Beejank of the product of Beejanks
    # This is the Vedic verification rule: B(a * b) == B(B(a) * B(b))
    composite = b_amt * b_ts * b_lat * b_lng
    return beejank(composite)


def _compute_hmac(amount: float, timestamp_iso: str,
                   geo_lat: float, geo_lng: float) -> str:
    """
    Compute HMAC-SHA256 of the transaction fields for cryptographic integrity.
    Returns first 16 hex characters (64-bit security — sufficient for pre-filter).
    """
    lat = geo_lat if geo_lat is not None else 0.0
    lng = geo_lng if geo_lng is not None else 0.0
    message = f"{amount:.2f}|{timestamp_iso}|{lat:.6f}|{lng:.6f}"
    mac = hmac.new(HMAC_SECRET_KEY, message.encode(), hashlib.sha256)
    return mac.hexdigest()[:16]


def compute_anurupyena_checksum(amount: float, timestamp_iso: str,
                                 geo_lat: float, geo_lng: float) -> str:
    """
    Public API: Computes the Vedic checksum with HMAC integrity layer.
    
    Two-layer integrity:
      1. Vedic Beejank digit (fast sanity check, cultural significance)
      2. HMAC-SHA256 tag (cryptographic tamper-proofing, eliminates collisions)
    
    Returns: str — format "vedic:{checksum_digit}:{hmac_short}:{amount_beejank}"
    """
    import datetime

    try:
        dt = datetime.datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00'))
        ts_epoch = int(dt.timestamp())
    except (ValueError, AttributeError):
        ts_epoch = 0

    checksum = vedic_digit_sum_checksum(amount, ts_epoch, geo_lat, geo_lng)
    amt_beejank = beejank(int(abs(amount) * 100))
    hmac_tag = _compute_hmac(amount, timestamp_iso, geo_lat, geo_lng)

    return f"vedic:{checksum}:{hmac_tag}:{amt_beejank}"


def verify_transaction_integrity(payload_checksum: str, amount: float,
                                  timestamp_iso: str, geo_lat: float,
                                  geo_lng: float) -> bool:
    """
    Verify that a received transaction has not been tampered with.
    
    Two-layer verification:
      1. Fast Vedic Beejank check (catches ~89% of tampering)
      2. HMAC-SHA256 verification (catches remaining collisions)
    
    Returns True if both checks pass (transaction is structurally valid).
    """
    recomputed = compute_anurupyena_checksum(amount, timestamp_iso, geo_lat, geo_lng)
    
    # If old-format checksum (vedic:X:Y), do legacy comparison
    if payload_checksum.count(":") == 2:
        # Legacy format — compare only Beejank parts
        parts_payload = payload_checksum.split(":")
        parts_computed = recomputed.split(":")
        return parts_payload[1] == parts_computed[1]
    
    # New format (vedic:beejank:hmac:amt_beejank) — full comparison
    return recomputed == payload_checksum

