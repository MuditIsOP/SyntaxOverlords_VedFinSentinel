from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta
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
    integrity_hash: Optional[str] = Field(None, max_length=256, description="HMAC-SHA256 integrity hash for tamper verification")

    @field_validator('txn_timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is not in the future beyond a 5min clock drift."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError('Transaction timestamp cannot be in the future')
        return v

class FraudScoreResponse(BaseModel):
    txn_id: UUID
    fraud_score: float = Field(..., ge=0.0, le=1.0)
    risk_band: str # SAFE | MONITOR | SUSPICIOUS | FRAUD
    action_taken: str
    reasons: list[str]
    latency_ms: int
    integrity_check_valid: bool
    structural_anomalies: list[str] = []
