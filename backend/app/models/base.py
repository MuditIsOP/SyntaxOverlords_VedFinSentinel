from sqlalchemy.orm import declarative_base
from enum import Enum as PyEnum

Base = declarative_base()

class RiskProfileEnum(str, PyEnum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    BLACKLISTED = 'BLACKLISTED'

class RiskBandEnum(str, PyEnum):
    SAFE = 'SAFE'
    MONITOR = 'MONITOR'
    SUSPICIOUS = 'SUSPICIOUS'
    FRAUD = 'FRAUD'

class ActionTakenEnum(str, PyEnum):
    APPROVED = 'APPROVED'
    HELD = 'HELD'
    BLOCKED = 'BLOCKED'
    FROZEN = 'FROZEN'

class ReviewerStatusEnum(str, PyEnum):
    PENDING = 'PENDING'
    REVIEWED = 'REVIEWED'
    ESCALATED = 'ESCALATED'
    CLEARED = 'CLEARED'

class AttackScenarioEnum(str, PyEnum):
    # FIXED: Match PRD specification exactly
    GEO_SPOOFING = 'GEO_SPOOFING'         # Simulate login from new country, VPN
    BURST_MICRO = 'BURST_MICRO'            # 50 transactions under ₹999 in 3 minutes
    ACCOUNT_TAKEOVER = 'ACCOUNT_TAKEOVER'  # New device, new geo, unknown recipients
