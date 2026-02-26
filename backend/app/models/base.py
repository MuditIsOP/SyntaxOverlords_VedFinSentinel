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
    VELOCITY_BURST = 'VELOCITY_BURST'
    IMPOSSIBLE_TRAVEL = 'IMPOSSIBLE_TRAVEL'
    VEDIC_COLLISION = 'VEDIC_COLLISION'
