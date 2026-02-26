from sqlalchemy import Column, String, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy import JSON, Uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from .base import Base

class Transaction(Base):
    __tablename__ = 'transactions'
    txn_id           = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id          = Column(Uuid(as_uuid=True), ForeignKey('users.user_id'))
    amount           = Column(Numeric(12,2), nullable=False)
    txn_timestamp    = Column(DateTime(timezone=True), nullable=False)
    geo_lat          = Column(Numeric(9,6))
    geo_lng          = Column(Numeric(9,6))
    device_id        = Column(String(256), nullable=False)
    device_os        = Column(String(64))
    ip_subnet        = Column(String(45))
    merchant_category= Column(String(64), nullable=False)
    merchant_id      = Column(String(128))
    recipient_id     = Column(Uuid(as_uuid=True), ForeignKey('users.user_id'))
    fraud_label      = Column(Boolean)
    vedic_checksum   = Column(String(128))
    vedic_valid      = Column(Boolean, default=True)
    raw_payload      = Column(JSON)
    is_deleted       = Column(Boolean, default=False)
    deleted_at       = Column(DateTime(timezone=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    user             = relationship('User', back_populates='transactions', foreign_keys=[user_id])
    audit_log        = relationship('RiskAuditLog', back_populates='transaction', uselist=False)
