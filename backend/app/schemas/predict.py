from pydantic import BaseModel, Field, validator
from typing import Optional, Dict
from datetime import datetime, timezone
from uuid import UUID

class TransactionRequest(BaseModel):
    user_id: UUID
    amount: float = Field(gt=0, le=10_000_000)
    txn_timestamp: datetime
    geo_lat: Optional[float] = Field(None, ge=-90, le=90)
    geo_lng: Optional[float] = Field(None, ge=-180, le=180)
    device_id: str = Field(..., max_length=256)
    device_os: Optional[str] = Field(None, max_length=64)
    ip_subnet: Optional[str] = Field(None, max_length=45)
    merchant_category: str = Field(..., max_length=64)
    merchant_id: Optional[str] = Field(None, max_length=128)
    recipient_id: Optional[UUID] = None
    vedic_checksum: Optional[str] = Field(None, max_length=128, description="Anurupyena checksum for tamper verification")

    @validator('txn_timestamp')
    def validate_timestamp(cls, v):
        """Ensure timestamp is not in the future beyond a 5min clock drift."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v > datetime.now(timezone.utc) + getattr(datetime, 'timedelta', __import__('datetime').timedelta)(minutes=5):
            raise ValueError('Transaction timestamp cannot be in the future')
        return v

class FraudScoreResponse(BaseModel):
    txn_id: UUID
    fraud_score: float = Field(..., ge=0.0, le=1.0)
    risk_band: str # SAFE | MONITOR | SUSPICIOUS | FRAUD
    action_taken: str
    reasons: list[str]
    latency_ms: int
    nikhilam_speedup: Optional[float] = None
    vedic_checksum_valid: bool
