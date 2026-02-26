from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, Numeric
from sqlalchemy import JSON, Uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from .base import Base, RiskProfileEnum

class User(Base):
    __tablename__ = 'users'
    user_id          = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email            = Column(String(255), unique=True, nullable=False)
    hashed_password  = Column(String(256), nullable=False)
    phone_hash       = Column(String(256))
    risk_profile     = Column(Enum(RiskProfileEnum), default=RiskProfileEnum.LOW)
    baseline_stats   = Column(JSON, default=dict)
    account_age_days = Column(Integer, default=0)
    trusted_devices  = Column(JSON, default=list)
    trusted_locations= Column(JSON, default=list)
    avg_txn_amount   = Column(Numeric(12,2), default=0)
    total_txn_count  = Column(Integer, default=0)
    is_deleted       = Column(Boolean, default=False)
    deleted_at       = Column(DateTime(timezone=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())
    transactions     = relationship('Transaction', back_populates='user', foreign_keys='Transaction.user_id')
