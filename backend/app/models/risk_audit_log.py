from sqlalchemy import Column, String, Integer, DateTime, Enum, Numeric, ForeignKey, Text
from sqlalchemy import JSON, Uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from .base import Base, RiskBandEnum, ActionTakenEnum, ReviewerStatusEnum

class RiskAuditLog(Base):
    __tablename__ = 'risk_audit_logs'
    log_id             = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    txn_id             = Column(Uuid(as_uuid=True), ForeignKey('transactions.txn_id'))
    fraud_score        = Column(Numeric(5,4), nullable=False)
    risk_band          = Column(Enum(RiskBandEnum), nullable=False)
    index_scores       = Column(JSON, nullable=False)
    shap_values        = Column(JSON, nullable=False)
    human_explanation  = Column(Text, nullable=False)
    dynamic_threshold  = Column(Numeric(12,4))
    xgboost_score      = Column(Numeric(5,4))
    isolation_score    = Column(Numeric(5,4))
    ensemble_weight_xgb= Column(Numeric(4,3))
    action_taken       = Column(Enum(ActionTakenEnum), nullable=False)
    reviewer_status    = Column(Enum(ReviewerStatusEnum), default=ReviewerStatusEnum.PENDING)
    reviewer_id        = Column(Uuid(as_uuid=True), ForeignKey('users.user_id'))
    reviewer_notes     = Column(Text)
    log_hash           = Column(String(256), nullable=False)
    latency_ms         = Column(Integer)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    transaction        = relationship('Transaction', back_populates='audit_log')
