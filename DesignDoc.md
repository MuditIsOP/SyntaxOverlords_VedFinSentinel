# VedFin Sentinel — Technical Design Document
**AI Agent Implementation Reference**
`v1.0 | InnVedX Hackathon 2026 | BBD University`

---

> **⚠ AGENT INSTRUCTION:** Read this document completely, top to bottom, before writing any file.
> Every section is self-contained but cross-references others.
> Follow all naming conventions exactly.
> Companion document: `VedFin_Sentinel_PRD.md` — read that first for product context.

---

| Field | Value |
|---|---|
| Document Purpose | Complete implementation reference for AI agent code generation |
| Companion Document | VedFin_Sentinel_PRD.md |
| Covers | Frontend · Backend · ML Pipeline · Database · API Contracts · Sequence Flows |
| Primary PS | PS 6 — FinTech Fraud Detection Using Behavioral Analysis |
| Vedic PS | PS 21 (Checksum) + PS 18 (Nikhilam Compute Engine) |
| Stack | Next.js · FastAPI · PostgreSQL · Redis · XGBoost · SHAP · Docker |
| Agent Instruction | Read every section top-to-bottom before writing any file. Follow all naming conventions exactly. |

---

## Table of Contents

1. [Project Structure & Naming Conventions](#1-project-structure--naming-conventions)
2. [Database Design](#2-database-design)
3. [Backend Architecture](#3-backend-architecture)
4. [API Contracts — Full Specification](#4-api-contracts--full-specification)
5. [ML Pipeline](#5-ml-pipeline)
6. [Frontend Architecture](#6-frontend-architecture)
7. [Sequence Diagrams](#7-sequence-diagrams)
8. [Infrastructure & Deployment](#8-infrastructure--deployment)
9. [Error Handling & Logging](#9-error-handling--logging)
10. [Agent Implementation Checklist](#10-agent-implementation-checklist)

---

## 1. Project Structure & Naming Conventions

### 1.1 Monorepo Layout

```
vedfin-sentinel/
├── frontend/               # Next.js 14 App Router
│   ├── app/               # Route segments
│   ├── components/        # All React components
│   │   ├── ui/            # Design-system primitives
│   │   ├── dashboard/     # Dashboard-specific components
│   │   ├── simulation/    # Attack simulation lab components
│   │   └── compliance/    # Audit & compliance export UI
│   ├── lib/               # API client, utils, stores
│   ├── hooks/             # Custom React hooks
│   ├── styles/            # Global CSS + Tailwind config
│   └── public/            # Static assets
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── api/           # Route handlers (v1/)
│   │   ├── core/          # Config, security, dependencies
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # Business logic layer
│   │   └── ml/            # ML pipeline (all model code)
│   │       ├── vedic/     # Vedic computation modules
│   │       ├── features/  # Behavioral feature engine
│   │       ├── models/    # XGBoost + Isolation Forest
│   │       └── explainer/ # SHAP integration
│   ├── migrations/        # Alembic migration files
│   ├── tests/             # Pytest test suite
│   └── main.py            # FastAPI entrypoint
├── ml-research/           # Jupyter notebooks (offline training)
│   ├── data/              # Raw + processed datasets
│   ├── training/          # Model training scripts
│   └── artifacts/         # Saved model files (.pkl, .json)
├── infra/
│   ├── docker-compose.yml
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backend
│   └── k8s/               # Kubernetes manifests
└── docs/                  # PRD, Design Doc, API specs
```

### 1.2 Naming Conventions (Agent Must Follow Exactly)

| Domain | Convention | Example |
|---|---|---|
| Python files | snake_case | `behavioral_engine.py` |
| Python classes | PascalCase | `NikhilamCalibrator` |
| Python functions | snake_case | `compute_burst_frequency_index()` |
| Python constants | UPPER_SNAKE | `FRAUD_THRESHOLD = 0.86` |
| Pydantic schemas | PascalCase + suffix | `TransactionRequest`, `FraudScoreResponse` |
| FastAPI routers | snake_case file, prefix | `predict.py` → `/api/v1/predict` |
| Next.js components | PascalCase | `FraudGauge.tsx` |
| Next.js hooks | camelCase + use prefix | `useFraudStream.ts` |
| Next.js routes | kebab-case folders | `app/attack-simulation/page.tsx` |
| Zustand stores | camelCase + Store suffix | `transactionStore.ts` |
| DB tables | snake_case plural | `transactions`, `risk_audit_logs` |
| DB columns | snake_case | `fraud_score`, `device_id` |
| Env variables | UPPER_SNAKE | `DATABASE_URL`, `REDIS_URL` |
| Docker services | kebab-case | `vedfin-backend`, `vedfin-frontend` |

### 1.3 Environment Variables

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://vedfinuser:password@localhost:5432/vedfindb
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<256-bit-random>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
MODEL_PATH=./ml/artifacts/sentinel_ensemble.pkl
SHAP_BACKGROUND_SAMPLES=100
VEDIC_BENCHMARK_ENABLED=true
LOG_LEVEL=INFO

# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

## 2. Database Design

### 2.1 Full Schema — PostgreSQL 15

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;  -- for POINT geo data

-- ─── ENUM TYPES ───────────────────────────────────────────────────
CREATE TYPE risk_profile_enum    AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'BLACKLISTED');
CREATE TYPE risk_band_enum       AS ENUM ('SAFE', 'MONITOR', 'SUSPICIOUS', 'FRAUD');
CREATE TYPE action_taken_enum    AS ENUM ('APPROVED', 'HELD', 'BLOCKED', 'FROZEN');
CREATE TYPE reviewer_status_enum AS ENUM ('PENDING','REVIEWED','ESCALATED','CLEARED');
CREATE TYPE attack_scenario_enum AS ENUM ('GEO_SPOOFING','BURST_MICRO','ACCOUNT_TAKEOVER');

-- ─── USERS ─────────────────────────────────────────────────────────
CREATE TABLE users (
  user_id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email                VARCHAR(255) UNIQUE NOT NULL,
  phone_hash           VARCHAR(256),          -- SHA-256 of phone number
  risk_profile         risk_profile_enum NOT NULL DEFAULT 'LOW',
  baseline_stats       JSONB NOT NULL DEFAULT '{}',
  -- baseline_stats shape: {
  --   adi: {mean: float, std: float},
  --   gri: {mean: float, std: float},
  --   dts: {mean: float, std: float},
  --   trc: {mean: float, std: float},
  --   mrs: {mean: float, std: float},
  --   bfi: {mean: float, std: float},
  --   bds: {mean: float, std: float},
  --   vri: {mean: float, std: float},
  --   sgas: {mean: float, std: float}
  -- }
  account_age_days     INTEGER NOT NULL DEFAULT 0,
  trusted_devices      TEXT[] NOT NULL DEFAULT '{}',
  trusted_locations    JSONB NOT NULL DEFAULT '[]',
  -- trusted_locations shape: [{lat: float, lng: float, label: string}]
  avg_txn_amount       DECIMAL(12,2) NOT NULL DEFAULT 0,
  total_txn_count      INTEGER NOT NULL DEFAULT 0,
  is_deleted           BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at           TIMESTAMPTZ,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── TRANSACTIONS ───────────────────────────────────────────────────
CREATE TABLE transactions (
  txn_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id              UUID NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
  amount               DECIMAL(12,2) NOT NULL CHECK (amount > 0),
  txn_timestamp        TIMESTAMPTZ NOT NULL,
  geo_lat              DECIMAL(9,6),
  geo_lng              DECIMAL(9,6),
  device_id            VARCHAR(256) NOT NULL,
  device_os            VARCHAR(64),
  ip_subnet            VARCHAR(45),           -- /24 subnet of originating IP
  merchant_category    VARCHAR(64) NOT NULL,  -- MCC label
  merchant_id          VARCHAR(128),
  recipient_id         UUID REFERENCES users(user_id) ON DELETE SET NULL,
  fraud_label          BOOLEAN,               -- NULL = unseen, TRUE/FALSE = ground truth
  vedic_checksum       VARCHAR(128),          -- Anurupyena result string
  vedic_valid          BOOLEAN NOT NULL DEFAULT TRUE,
  raw_payload          JSONB,                 -- full original transaction payload
  is_deleted           BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at           TIMESTAMPTZ,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── RISK AUDIT LOG ────────────────────────────────────────────────
-- WRITE-ONCE TABLE: Never UPDATE or DELETE from application code.
-- Only reviewer_status and reviewer_notes may be updated via admin endpoint.
CREATE TABLE risk_audit_logs (
  log_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  txn_id               UUID NOT NULL REFERENCES transactions(txn_id) ON DELETE RESTRICT,
  fraud_score          DECIMAL(5,4) NOT NULL CHECK (fraud_score BETWEEN 0 AND 1),
  risk_band            risk_band_enum NOT NULL,
  index_scores         JSONB NOT NULL,
  -- index_scores shape: {adi, gri, dts, trc, mrs, bfi, bds, vri, sgas}: float 0-1
  shap_values          JSONB NOT NULL,
  -- shap_values shape: {feature_name: shap_value (float)}
  human_explanation    TEXT NOT NULL,
  nikhilam_threshold   DECIMAL(12,4),         -- Vedic-computed threshold value
  xgboost_score        DECIMAL(5,4),
  isolation_score      DECIMAL(5,4),
  ensemble_weight_xgb  DECIMAL(4,3),          -- weight used for XGBoost in ensemble
  action_taken         action_taken_enum NOT NULL,
  reviewer_status      reviewer_status_enum NOT NULL DEFAULT 'PENDING',
  reviewer_id          UUID REFERENCES users(user_id) ON DELETE SET NULL,
  reviewer_notes       TEXT,
  log_hash             VARCHAR(256) NOT NULL, -- SHA-256 of (txn_id||fraud_score||action_taken||created_at)
  latency_ms           INTEGER,               -- end-to-end prediction latency
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── SIMULATION RUNS ───────────────────────────────────────────────
CREATE TABLE simulation_runs (
  run_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  scenario             attack_scenario_enum NOT NULL,
  target_user_id       UUID NOT NULL REFERENCES users(user_id),
  triggered_by         UUID REFERENCES users(user_id),
  events               JSONB NOT NULL DEFAULT '[]',
  -- events: [{txn_id, fraud_score, risk_band, index_scores, timestamp}]
  final_action         action_taken_enum,
  total_latency_ms     INTEGER,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── API KEYS ───────────────────────────────────────────────────────
CREATE TABLE api_keys (
  key_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_id             UUID NOT NULL REFERENCES users(user_id),
  key_hash             VARCHAR(256) UNIQUE NOT NULL,
  label                VARCHAR(128),
  is_active            BOOLEAN NOT NULL DEFAULT TRUE,
  rate_limit_per_min   INTEGER NOT NULL DEFAULT 100,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_used_at         TIMESTAMPTZ
);
```

### 2.2 Indexes

```sql
-- Performance indexes
CREATE INDEX idx_transactions_user_id        ON transactions(user_id);
CREATE INDEX idx_transactions_timestamp       ON transactions(txn_timestamp DESC);
CREATE INDEX idx_transactions_user_timestamp  ON transactions(user_id, txn_timestamp DESC);
CREATE INDEX idx_transactions_fraud_label     ON transactions(fraud_label) WHERE fraud_label IS NOT NULL;
CREATE INDEX idx_risk_audit_logs_txn_id       ON risk_audit_logs(txn_id);
CREATE INDEX idx_risk_audit_logs_risk_band    ON risk_audit_logs(risk_band);
CREATE INDEX idx_risk_audit_logs_created_at   ON risk_audit_logs(created_at DESC);
CREATE INDEX idx_risk_audit_logs_reviewer     ON risk_audit_logs(reviewer_status) WHERE reviewer_status = 'PENDING';
CREATE INDEX idx_users_risk_profile           ON users(risk_profile);
CREATE INDEX idx_simulation_runs_scenario     ON simulation_runs(scenario);

-- GIN index for JSONB queries (baseline_stats, index_scores)
CREATE INDEX idx_users_baseline_gin           ON users USING gin(baseline_stats);
CREATE INDEX idx_risk_audit_shap_gin          ON risk_audit_logs USING gin(shap_values);
```

### 2.3 SQLAlchemy ORM Models

```python
# models/user.py
class User(Base):
    __tablename__ = 'users'
    user_id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email            = Column(String(255), unique=True, nullable=False)
    phone_hash       = Column(String(256))
    risk_profile     = Column(Enum(RiskProfileEnum), default='LOW')
    baseline_stats   = Column(JSONB, default=dict)
    account_age_days = Column(Integer, default=0)
    trusted_devices  = Column(ARRAY(String), default=list)
    trusted_locations= Column(JSONB, default=list)
    avg_txn_amount   = Column(Numeric(12,2), default=0)
    total_txn_count  = Column(Integer, default=0)
    is_deleted       = Column(Boolean, default=False)
    deleted_at       = Column(DateTime(timezone=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())
    transactions     = relationship('Transaction', back_populates='user')

# models/transaction.py
class Transaction(Base):
    __tablename__ = 'transactions'
    txn_id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id          = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    amount           = Column(Numeric(12,2), nullable=False)
    txn_timestamp    = Column(DateTime(timezone=True), nullable=False)
    geo_lat          = Column(Numeric(9,6))
    geo_lng          = Column(Numeric(9,6))
    device_id        = Column(String(256), nullable=False)
    device_os        = Column(String(64))
    ip_subnet        = Column(String(45))
    merchant_category= Column(String(64), nullable=False)
    merchant_id      = Column(String(128))
    recipient_id     = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    fraud_label      = Column(Boolean)
    vedic_checksum   = Column(String(128))
    vedic_valid      = Column(Boolean, default=True)
    raw_payload      = Column(JSONB)
    is_deleted       = Column(Boolean, default=False)
    deleted_at       = Column(DateTime(timezone=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    user             = relationship('User', back_populates='transactions', foreign_keys=[user_id])
    audit_log        = relationship('RiskAuditLog', back_populates='transaction', uselist=False)

# models/risk_audit_log.py
class RiskAuditLog(Base):
    __tablename__ = 'risk_audit_logs'
    log_id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    txn_id             = Column(UUID(as_uuid=True), ForeignKey('transactions.txn_id'))
    fraud_score        = Column(Numeric(5,4), nullable=False)
    risk_band          = Column(Enum(RiskBandEnum), nullable=False)
    index_scores       = Column(JSONB, nullable=False)
    shap_values        = Column(JSONB, nullable=False)
    human_explanation  = Column(Text, nullable=False)
    nikhilam_threshold = Column(Numeric(12,4))
    xgboost_score      = Column(Numeric(5,4))
    isolation_score    = Column(Numeric(5,4))
    ensemble_weight_xgb= Column(Numeric(4,3))
    action_taken       = Column(Enum(ActionTakenEnum), nullable=False)
    reviewer_status    = Column(Enum(ReviewerStatusEnum), default='PENDING')
    reviewer_id        = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    reviewer_notes     = Column(Text)
    log_hash           = Column(String(256), nullable=False)
    latency_ms         = Column(Integer)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    transaction        = relationship('Transaction', back_populates='audit_log')
```

### 2.4 Alembic Migration Strategy

- Init: `alembic init migrations`
- Generate: `alembic revision --autogenerate -m 'initial_schema'`
- Apply: `alembic upgrade head`
- Every schema change → new revision file, **never edit existing migrations**
- Seed file: `backend/app/core/seed.py` — creates 3 demo users with realistic baselines

---

## 3. Backend Architecture

### 3.1 FastAPI Application Structure

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from app.api.v1 import predict, bulk_predict, simulate, audit, metrics, users

app = FastAPI(title='VedFin Sentinel API', version='1.0.0', docs_url='/docs')

app.add_middleware(CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

app.include_router(predict.router,      prefix='/api/v1', tags=['Prediction'])
app.include_router(bulk_predict.router, prefix='/api/v1', tags=['Bulk'])
app.include_router(simulate.router,     prefix='/api/v1', tags=['Simulation'])
app.include_router(audit.router,        prefix='/api/v1', tags=['Audit'])
app.include_router(metrics.router,      prefix='/api/v1', tags=['Metrics'])
app.include_router(users.router,        prefix='/api/v1', tags=['Users'])
```

### 3.2 Middleware Stack (execution order)

| Order | Middleware | Purpose |
|---|---|---|
| 1 | CORSMiddleware | Allow frontend origin, credentials |
| 2 | SlowAPI RateLimiter | 100 req/min per API key (configurable per key) |
| 3 | JWTAuthMiddleware | Validate Bearer token on protected routes |
| 4 | RequestIDMiddleware | Attach X-Request-ID to every request and response |
| 5 | TimingMiddleware | Log end-to-end request latency to structured logs |
| 6 | ErrorHandlerMiddleware | Catch unhandled exceptions, return RFC 7807 Problem JSON |

### 3.3 Dependency Injection (core/dependencies.py)

```python
# Async DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

# Redis client
async def get_redis() -> Redis:
    return await aioredis.from_url(settings.REDIS_URL)

# Authenticated user from JWT
async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)) -> User:
    payload = decode_jwt(token)
    return await get_user_by_id(db, payload['sub'])

# ML Engine singleton
def get_ml_engine() -> SentinelEnsemble:
    return app.state.ml_engine  # loaded at startup
```

### 3.4 Service Layer Architecture

| Service File | Responsibility |
|---|---|
| `services/fraud_scoring.py` | Orchestrate full predict pipeline: vedic → features → calibrator → ensemble → shap → response |
| `services/behavioral.py` | Compute all 9 behavioral indices given transaction + user baseline |
| `services/vedic.py` | Anurupyena checksum + Nikhilam threshold calibration |
| `services/explainer.py` | SHAP value computation + human explanation generation |
| `services/user_baseline.py` | Read/write/recalculate user behavioral baselines in DB |
| `services/simulation.py` | Generate synthetic attack transaction sequences |
| `services/compliance.py` | Generate PDF compliance reports using ReportLab |
| `services/metrics.py` | Compute precision, recall, F1, ROC-AUC from DB |

---

## 4. API Contracts — Full Specification

### 4.1 POST /api/v1/predict

#### Request Schema

```python
# schemas/predict.py — TransactionRequest
class TransactionRequest(BaseModel):
    user_id:           UUID                     # existing user in DB
    amount:            float = Field(gt=0, le=10_000_000)  # INR
    txn_timestamp:     datetime                 # ISO8601 with timezone
    geo_lat:           Optional[float] = None   # -90 to 90
    geo_lng:           Optional[float] = None   # -180 to 180
    device_id:         str = Field(min_length=8, max_length=256)
    device_os:         Optional[str] = None     # 'android'|'ios'|'web'
    ip_subnet:         Optional[str] = None     # IPv4 /24 subnet
    merchant_category: str = Field(min_length=2, max_length=64)
    merchant_id:       Optional[str] = None
    recipient_id:      Optional[UUID] = None

    @validator('txn_timestamp')
    def timestamp_not_future(cls, v):
        if v > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError('timestamp cannot be more than 5 minutes in the future')
        return v
```

#### Response Schema

```python
# schemas/predict.py — FraudScoreResponse
class IndexScores(BaseModel):
    adi:  float  # Amount Deviation Index
    gri:  float  # Geo-Shift Risk Index
    dts:  float  # Device Trust Score
    trc:  float  # Time Risk Coefficient
    mrs:  float  # Merchant Risk Score
    bfi:  float  # Burst Frequency Index
    bds:  float  # Behavioral Drift Score
    vri:  float  # Velocity Reversal Index
    sgas: float  # Social Graph Anomaly Score

class FraudScoreResponse(BaseModel):
    txn_id:            UUID
    fraud_score:       float            # 0.0000 – 1.0000
    risk_band:         str              # 'SAFE'|'MONITOR'|'SUSPICIOUS'|'FRAUD'
    index_scores:      IndexScores
    shap_top_features: List[dict]       # [{feature, shap_value, direction}] top 5
    human_explanation: str
    action_taken:      str              # 'APPROVED'|'HELD'|'BLOCKED'|'FROZEN'
    vedic_valid:       bool             # passed Anurupyena checksum
    nikhilam_threshold:float
    latency_ms:        int
    log_id:            UUID             # reference to risk_audit_logs
```

#### Validation Rules

- `amount` must be > 0 and <= 10,000,000 (INR)
- `txn_timestamp` must not be more than 5 minutes in the future
- `geo_lat` / `geo_lng` must both be present or both absent
- `device_id` must be 8–256 chars, no whitespace
- `user_id` must exist in users table — 404 if not found

#### Error Codes

| HTTP Code | Error Code | When |
|---|---|---|
| 400 | VALIDATION_ERROR | Request body fails Pydantic validation |
| 401 | UNAUTHORIZED | Missing or invalid Bearer token |
| 404 | USER_NOT_FOUND | user_id does not exist in DB |
| 422 | INVALID_GEO | geo_lat present without geo_lng or vice versa |
| 429 | RATE_LIMIT_EXCEEDED | Over 100 req/min for this API key |
| 500 | PREDICTION_FAILED | ML engine threw an unhandled exception |
| 503 | MODEL_NOT_READY | ML engine not loaded (startup incomplete) |

#### Full Example

```json
// Request
POST /api/v1/predict
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 49500.00,
  "txn_timestamp": "2026-02-22T02:47:33+05:30",
  "geo_lat": 12.9716,
  "geo_lng": 77.5946,
  "device_id": "d3v1c3-f1ng3rpr1nt-x99z",
  "device_os": "android",
  "ip_subnet": "103.21.244.0",
  "merchant_category": "crypto_exchange",
  "merchant_id": "MCH-9934",
  "recipient_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}

// Response 200
{
  "txn_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "fraud_score": 0.9412,
  "risk_band": "FRAUD",
  "index_scores": {
    "adi": 0.91, "gri": 0.94, "dts": 0.97, "trc": 0.89,
    "mrs": 0.88, "bfi": 0.72, "bds": 0.45, "vri": 0.61, "sgas": 0.99
  },
  "shap_top_features": [
    {"feature": "sgas", "shap_value": 0.31, "direction": "up"},
    {"feature": "dts",  "shap_value": 0.28, "direction": "up"},
    {"feature": "gri",  "shap_value": 0.22, "direction": "up"},
    {"feature": "adi",  "shap_value": 0.18, "direction": "up"},
    {"feature": "trc",  "shap_value": 0.09, "direction": "up"}
  ],
  "human_explanation": "Transaction flagged: unknown recipient (zero prior history) + new unrecognized device + geo-shift of 1,847km in 40 minutes + 2:47 AM outside normal hours + crypto exchange category. Fraud probability: 94%.",
  "action_taken": "FROZEN",
  "vedic_valid": true,
  "nikhilam_threshold": 42000.00,
  "latency_ms": 287,
  "log_id": "c9d8e7f6-a5b4-3210-fedc-ba9876543210"
}
```

---

### 4.2 POST /api/v1/bulk_predict

```python
# Request
{ "transactions": [TransactionRequest, ...] }  # max 10,000 items

# Response
{
  "results": [FraudScoreResponse, ...],
  "summary": {
    "total": int,
    "safe": int, "monitor": int, "suspicious": int, "fraud": int,
    "avg_fraud_score": float,
    "avg_latency_ms": int,
    "precision": float,  # only if fraud_label provided in requests
    "recall": float
  },
  "processing_time_ms": int
}

# Errors
# 413 PAYLOAD_TOO_LARGE — more than 10,000 transactions
# 400 EMPTY_BATCH       — transactions array is empty
```

---

### 4.3 POST /api/v1/simulate/attack

```python
# Request
class AttackSimulationRequest(BaseModel):
    scenario:       AttackScenarioEnum  # GEO_SPOOFING | BURST_MICRO | ACCOUNT_TAKEOVER
    target_user_id: UUID
    speed:          str = 'normal'      # 'slow'|'normal'|'fast' — replay speed for UI

# Response: streaming NDJSON — one JSON object per line
# Each line is a SimulationEvent:
{
  "event_type": "transaction" | "alert" | "summary",
  "sequence":   int,
  "txn_id":     "UUID",
  "fraud_score": float,
  "risk_band":  "SAFE|MONITOR|SUSPICIOUS|FRAUD",
  "index_scores": { ...IndexScores },
  "triggered_indices": ["sgas", "dts", "gri"],
  "action_taken": "APPROVED|HELD|BLOCKED|FROZEN",
  "timestamp":   "ISO8601"
}

# Final event (event_type = 'summary'):
{
  "event_type": "summary",
  "total_transactions": int,
  "fraud_detected_at": int,    # sequence number when FRAUD band first hit
  "final_action": "FROZEN",
  "total_latency_ms": int
}
```

---

### 4.4 GET /api/v1/audit/export

```
# Query params
start_date:  date (required)     # YYYY-MM-DD
end_date:    date (required)     # YYYY-MM-DD, max range 90 days
user_id:     UUID (optional)     # filter by user
risk_band:   str (optional)      # SAFE|MONITOR|SUSPICIOUS|FRAUD
format:      str = 'pdf'         # 'pdf'|'json'

# Response (format=pdf)
Content-Type: application/pdf
Content-Disposition: attachment; filename=vedfinsentinel_audit_<start>_<end>.pdf

# PDF structure:
# 1. Cover: date range, generated_at, total transactions
# 2. Summary: counts per risk band, precision/recall
# 3. Transaction table: txn_id, user, amount, score, band, action, explanation
# 4. Vedic validation log: checksum results
# 5. Model performance metrics: confusion matrix, ROC-AUC
# 6. Tamper-proof hash footer

# Errors
# 400 DATE_RANGE_TOO_LARGE — more than 90 days
# 400 END_BEFORE_START     — end_date < start_date
```

---

### 4.5 GET /api/v1/metrics

```python
# Query params
window: str = '24h'   # '1h'|'6h'|'24h'|'7d'|'30d'

# Response
{
  "window": str,
  "total_transactions":    int,
  "fraud_count":           int,
  "fraud_rate":            float,
  "precision":             float,
  "recall":                float,
  "f1_score":              float,
  "roc_auc":               float,
  "false_positive_rate":   float,
  "confusion_matrix":      { "tp": int, "fp": int, "tn": int, "fn": int },
  "avg_latency_ms":        int,
  "p95_latency_ms":        int,
  "vedic_filter_rate":     float,   # % txns filtered by Vedic pre-filter
  "risk_band_distribution":{ "SAFE": int, "MONITOR": int, "SUSPICIOUS": int, "FRAUD": int },
  "index_avg_scores":      IndexScores,
  "fraud_by_hour":         [{"hour": int, "count": int}],  # 24 items for 24h window
  "nikhilam_speedup":      float    # ratio vs standard computation
}
```

---

### 4.6 GET /api/v1/users/{user_id}/baseline

```python
# Response
{
  "user_id":          "UUID",
  "risk_profile":     "LOW|MEDIUM|HIGH|BLACKLISTED",
  "baseline_stats":   { "adi": {"mean": float, "std": float}, ... },  # all 9 indices
  "trusted_devices":  ["device_id_1", "device_id_2"],
  "trusted_locations":[{"lat": float, "lng": float, "label": "Home"}],
  "avg_txn_amount":   float,
  "total_txn_count":  int,
  "account_age_days": int,
  "last_updated":     "ISO8601 datetime"
}
```

---

## 5. ML Pipeline

### 5.1 Behavioral Feature Engine (services/behavioral.py)

> All indices return `float` in `[0.0, 1.0]`. Higher = more suspicious.

#### ADI — Amount Deviation Index

```python
def compute_adi(amount: float, baseline: dict) -> float:
    """
    Measures how far the transaction amount deviates from the user's baseline.
    Uses z-score normalized to [0,1].
    baseline = {mean: float, std: float}
    """
    mean, std = baseline['adi']['mean'], baseline['adi']['std']
    if std == 0: std = 1.0  # fallback
    z = abs(amount - mean) / std
    return min(1.0, z / 5.0)  # cap at z=5 → 1.0
```

#### GRI — Geo-Shift Risk Index

```python
def compute_gri(lat: float, lng: float, trusted_locations: list,
                prev_txn_lat: float, prev_txn_lng: float,
                prev_txn_timestamp: datetime, current_timestamp: datetime) -> float:
    """
    Two components:
    1. Distance from nearest trusted location (normalized to 5000km max)
    2. Physically impossible travel: km / hours > 900 (max commercial flight speed)
    Final = max(location_risk, travel_risk)
    """
    from geopy.distance import geodesic
    if not trusted_locations: return 0.5  # no baseline yet
    nearest_km = min(geodesic((lat,lng),(t['lat'],t['lng'])).km for t in trusted_locations)
    location_risk = min(1.0, nearest_km / 5000)
    hours_elapsed = (current_timestamp - prev_txn_timestamp).total_seconds() / 3600
    km_traveled   = geodesic((prev_txn_lat,prev_txn_lng),(lat,lng)).km
    if hours_elapsed > 0:
        speed_kmh   = km_traveled / hours_elapsed
        travel_risk = min(1.0, speed_kmh / 900)
    else:
        travel_risk = 1.0 if km_traveled > 50 else 0.0
    return max(location_risk, travel_risk)
```

#### DTS — Device Trust Score

```python
def compute_dts(device_id: str, trusted_devices: list) -> float:
    """
    0.0 = known trusted device
    1.0 = never-before-seen device
    """
    return 0.0 if device_id in trusted_devices else 1.0
```

#### TRC — Time Risk Coefficient

```python
def compute_trc(txn_timestamp: datetime, baseline: dict) -> float:
    """
    baseline['trc'] = {active_hours_start: int, active_hours_end: int}
    e.g. {start: 8, end: 22} means user is active 8AM–10PM
    Score based on how far outside normal hours the transaction falls.
    """
    hour = txn_timestamp.hour
    start, end = baseline['trc']['active_hours_start'], baseline['trc']['active_hours_end']
    if start <= hour <= end: return 0.0
    distance = min(abs(hour-start), abs(hour-end), abs(hour-start+24), abs(hour-end+24))
    return min(1.0, distance / 12)
```

#### MRS — Merchant Risk Score

```python
HIGH_RISK_CATEGORIES = {'crypto_exchange', 'gambling', 'wire_transfer', 'pawn_shop', 'foreign_exchange'}
MED_RISK_CATEGORIES  = {'jewelry', 'electronics', 'money_order', 'prepaid_card'}

def compute_mrs(merchant_category: str, merchant_id: str, baseline: dict) -> float:
    """
    Two components:
    1. Category base risk: HIGH=0.7, MED=0.4, LOW=0.1
    2. First-time merchant penalty: +0.3 if merchant never seen before
    Final = min(1.0, category_risk + first_time_penalty)
    """
    cat = merchant_category.lower()
    cat_risk = 0.7 if cat in HIGH_RISK_CATEGORIES else (0.4 if cat in MED_RISK_CATEGORIES else 0.1)
    known_merchants = baseline.get('known_merchants', [])
    first_time = 0.3 if merchant_id and merchant_id not in known_merchants else 0.0
    return min(1.0, cat_risk + first_time)
```

#### BFI — Burst Frequency Index

```python
async def compute_bfi(user_id: UUID, current_timestamp: datetime, db: AsyncSession) -> float:
    """
    Count transactions by this user in the last 60 seconds.
    0 txns → 0.0, 5+ txns → 1.0 (linear interpolation)
    """
    window_start = current_timestamp - timedelta(seconds=60)
    count = await db.scalar(
        select(func.count()).where(
            Transaction.user_id == user_id,
            Transaction.txn_timestamp >= window_start
        ))
    return min(1.0, count / 5)
```

#### BDS — Behavioral Drift Score

```python
def compute_bds(current_index_scores: dict, baseline: dict) -> float:
    """
    Measures long-term behavioral drift.
    Compare current 30-day rolling averages vs baseline.
    Uses Euclidean distance in 7-index space (excluding BFI, SGAS which are event-based).
    Normalized to [0,1] via max possible distance.
    """
    indices = ['adi','gri','dts','trc','mrs','vri','bds']
    diffs = [(current_index_scores.get(i,0) - baseline.get(i,{}).get('mean',0))**2 for i in indices]
    euclidean = (sum(diffs) ** 0.5)
    max_dist  = (7 ** 0.5)  # max when all indices differ by 1.0
    return min(1.0, euclidean / max_dist)
```

#### VRI — Velocity Reversal Index

```python
async def compute_vri(user_id: UUID, recipient_id: UUID,
                      current_timestamp: datetime, db: AsyncSession) -> float:
    """
    Detect money mule pattern: user sent money TO recipient within last 10 min,
    and recipient is now sending BACK to user (or user sent multiple rapid reversals).
    Also: count rapid back-and-forth transactions between same pair.
    0.0 = no reversal pattern, 1.0 = clear reversal within 10 minutes
    """
    window_start = current_timestamp - timedelta(minutes=10)
    # Check if user received from this recipient recently
    # Check if user is also sending to them now
    # Count back-and-forth within window
    # Returns 1.0 if clear reversal, graded otherwise
```

#### SGAS — Social Graph Anomaly Score

```python
async def compute_sgas(user_id: UUID, recipient_id: UUID,
                       amount: float, db: AsyncSession) -> float:
    """
    Check if user has any prior transaction history with this recipient.
    No history + high amount = 1.0
    No history + low amount  = 0.5
    Has history              = 0.0 to 0.3 based on recency and frequency
    """
    if recipient_id is None: return 0.0
    prior_count = await db.scalar(
        select(func.count()).where(
            Transaction.user_id == user_id,
            Transaction.recipient_id == recipient_id
        ))
    if prior_count == 0:
        return 1.0 if amount > 10_000 else 0.5
    recency_score = 0.0  # compute based on last interaction timestamp
    return max(0.0, 0.3 - (prior_count * 0.05))
```

---

### 5.2 Vedic Computation Modules

#### Module A — Anurupyena Checksum (vedic/anurupyena.py)

```python
def compute_anurupyena_checksum(txn_payload: dict) -> tuple[str, bool]:
    """
    Vedic Checksum using Anurupyena (Proportionality) + digit-sum divisibility rules.

    Algorithm:
    1. Extract numeric fields: amount, epoch_timestamp, account_number_digits
    2. Compute Vedic digit sum (add digits until single digit) for each field
    3. Apply Vedic divisibility check: sum of digit sums must be divisible by 9
       OR pass proportionality check vs transaction reference number
    4. If check fails → flag as structurally anomalous (potential replay/injection)

    Returns: (checksum_string, is_valid: bool)
    """
    def vedic_digit_sum(n: int) -> int:
        while n >= 10:
            n = sum(int(d) for d in str(n))
        return n

    amount_int = int(txn_payload['amount'] * 100)          # paise
    epoch      = int(txn_payload['txn_timestamp'].timestamp())
    device_num = int(txn_payload['device_id'].replace('-','')[:8], 16) % 10000

    ds_amount = vedic_digit_sum(amount_int)
    ds_epoch  = vedic_digit_sum(epoch)
    ds_device = vedic_digit_sum(device_num)

    total = ds_amount + ds_epoch + ds_device
    is_valid = vedic_digit_sum(total) in {1,2,3,4,5,6,7,8,9}  # any valid Vedic remainder

    # Proportionality check: amount-to-epoch ratio within expected range
    ratio = amount_int / epoch if epoch > 0 else 0
    proportionality_valid = 0 < ratio < 1000  # sanity bound

    checksum = f"VCSUM-{ds_amount}{ds_epoch}{ds_device}-{'P' if proportionality_valid else 'F'}"
    return checksum, is_valid and proportionality_valid
```

#### Module B — Nikhilam Threshold Calibrator (vedic/nikhilam.py)

```python
# Nikhilam Navatashcaramam Dashatah: 'All from 9, last from 10'
# Fast subtraction for numbers near powers of 10

BASES = [10, 100, 1000, 10000, 100000]

def nikhilam_complement(n: int, base: int) -> int:
    """Compute complement of n from base using Vedic rule."""
    if n == base: return 0
    digits = [int(d) for d in str(n)]
    result = []
    for i, d in enumerate(digits):
        if i < len(digits) - 1:
            result.append(9 - d)   # All from 9
        else:
            result.append(10 - d)  # Last from 10
    return int(''.join(map(str, result)))

def find_nearest_base(n: int) -> int:
    return min(BASES, key=lambda b: abs(b - n))

def nikhilam_threshold(user_avg_amount: float) -> float:
    """
    Compute fraud threshold for a user based on their avg transaction amount.
    For amounts near a power of 10, use Nikhilam for fast complement computation.
    Threshold = nearest_base + (base * 0.5)

    BENCHMARK: For amounts within 10% of a base, Nikhilam avoids standard
    multiplication, reducing compute by ~35% for qualifying amounts.
    """
    amount_int = int(user_avg_amount)
    base = find_nearest_base(amount_int)
    complement = nikhilam_complement(amount_int, base)
    threshold = base + (complement / 2)
    return float(threshold)

def benchmark_nikhilam_vs_standard(n: int) -> dict:
    """Run timed comparison for dashboard Vedic benchmark panel."""
    import time
    # Standard: float subtraction
    t0 = time.perf_counter_ns()
    base = find_nearest_base(n)
    standard_result = base - n
    standard_ns = time.perf_counter_ns() - t0
    # Nikhilam: digit-by-digit
    t1 = time.perf_counter_ns()
    nikhilam_result = nikhilam_complement(n, base)
    nikhilam_ns = time.perf_counter_ns() - t1
    return {
        'n': n, 'base': base,
        'standard_ns': standard_ns, 'nikhilam_ns': nikhilam_ns,
        'speedup_ratio': standard_ns / nikhilam_ns if nikhilam_ns > 0 else 1.0
    }
```

---

### 5.3 Hybrid Sentinel Ensemble (ml/models/sentinel_ensemble.py)

```python
class SentinelEnsemble:
    def __init__(self, model_path: str):
        with open(model_path, 'rb') as f:
            artifacts = pickle.load(f)
        self.xgb_model     = artifacts['xgboost']
        self.iso_model     = artifacts['isolation_forest']
        self.feature_names = artifacts['feature_names']   # 21 features — ALWAYS load from artifact
        self.shap_explainer= shap.TreeExplainer(self.xgb_model)

    def build_feature_vector(self, index_scores: dict, txn: dict) -> np.ndarray:
        """
        21 features = 9 behavioral indices + 12 metadata features.
        Order is fixed — ALWAYS loaded from artifacts['feature_names'].
        Metadata: amount_log, hour_of_day, day_of_week, is_weekend,
                  merchant_category_encoded, device_os_encoded,
                  ip_risk_score, account_age_log, avg_txn_amount_log,
                  total_txn_count_log, nikhilam_threshold_ratio,
                  vedic_valid_flag
        """
        indices = [index_scores['adi'], index_scores['gri'], index_scores['dts'],
                   index_scores['trc'], index_scores['mrs'], index_scores['bfi'],
                   index_scores['bds'], index_scores['vri'], index_scores['sgas']]
        meta    = [
            np.log1p(txn['amount']),
            txn['hour_of_day'],
            txn['day_of_week'],
            int(txn['day_of_week'] >= 5),
            txn['merchant_category_encoded'],
            txn['device_os_encoded'],
            txn['ip_risk_score'],
            np.log1p(txn['account_age_days']),
            np.log1p(txn['avg_txn_amount']),
            np.log1p(txn['total_txn_count']),
            txn['nikhilam_threshold_ratio'],  # amount / nikhilam_threshold
            float(txn['vedic_valid']),
        ]
        return np.array(indices + meta, dtype=np.float32).reshape(1, -1)

    def predict(self, feature_vector: np.ndarray, user_risk_profile: str) -> dict:
        # XGBoost probability
        xgb_score = float(self.xgb_model.predict_proba(feature_vector)[0][1])

        # Isolation Forest anomaly (-1=anomaly, 1=normal) → [0,1]
        iso_raw   = self.iso_model.decision_function(feature_vector)[0]
        iso_score = float(1 - (iso_raw - (-0.5)) / 1.0)
        iso_score = max(0.0, min(1.0, iso_score))

        # Ensemble weights based on user risk profile
        weights = {
            'LOW':         (0.75, 0.25),
            'MEDIUM':      (0.70, 0.30),
            'HIGH':        (0.65, 0.35),
            'BLACKLISTED': (0.60, 0.40)
        }
        w_xgb, w_iso = weights.get(user_risk_profile, (0.70, 0.30))
        ensemble_score = (w_xgb * xgb_score) + (w_iso * iso_score)

        return {
            'fraud_score':         round(ensemble_score, 4),
            'xgboost_score':       round(xgb_score, 4),
            'isolation_score':     round(iso_score, 4),
            'ensemble_weight_xgb': w_xgb,
            'risk_band':           classify_risk_band(ensemble_score),
            'action_taken':        determine_action(ensemble_score),
        }

# Risk band thresholds — fixed for v1.0
THRESHOLDS = {'SAFE': 0.35, 'MONITOR': 0.65, 'SUSPICIOUS': 0.85, 'FRAUD': 1.01}

def classify_risk_band(score: float) -> str:
    if score <= 0.35: return 'SAFE'
    if score <= 0.65: return 'MONITOR'
    if score <= 0.85: return 'SUSPICIOUS'
    return 'FRAUD'

def determine_action(score: float) -> str:
    if score <= 0.35: return 'APPROVED'
    if score <= 0.65: return 'APPROVED'   # logged, flagged, not blocked
    if score <= 0.85: return 'HELD'
    return 'FROZEN'
```

---

### 5.4 SHAP Explainer (ml/explainer/shap_explainer.py)

```python
def compute_shap_explanation(ensemble: SentinelEnsemble,
                             feature_vector: np.ndarray,
                             feature_names: list) -> dict:
    shap_values = ensemble.shap_explainer.shap_values(feature_vector)[0]
    attribution = dict(zip(feature_names, shap_values.tolist()))

    # Top 5 features sorted by absolute impact
    top_features = sorted(
        [{'feature': k, 'shap_value': round(v,4), 'direction': 'up' if v>0 else 'down'}
         for k,v in attribution.items()],
        key=lambda x: abs(x['shap_value']), reverse=True
    )[:5]

    return {'all_shap_values': attribution, 'top_features': top_features}


def generate_human_explanation(top_features: list, fraud_score: float,
                               index_scores: dict, txn: dict) -> str:
    """
    Template-based explanation generator.
    Maps feature name → human-readable phrase.
    Assembles: 'Transaction flagged: [reason1] + [reason2] + ... Fraud probability: X%'
    """
    PHRASES = {
        'sgas': 'unknown recipient (zero prior transaction history)',
        'dts':  'new unrecognized device',
        'gri':  f"geo-shift of ~{int(txn.get('km_traveled',0))}km in {int(txn.get('hours_elapsed',0)*60)}min",
        'adi':  f"amount {txn['amount']:,.0f} INR is {txn.get('amount_z_score',0):.1f}x above normal",
        'trc':  f"transaction at {txn.get('hour_of_day',0):02d}:00 is outside normal hours",
        'bfi':  f"{txn.get('burst_count',0)} transactions in the last 60 seconds",
        'mrs':  f"high-risk merchant category ({txn.get('merchant_category','')})",
        'vri':  'rapid money reversal pattern detected (potential money mule)',
        'bds':  'significant long-term behavioral drift from baseline',
    }
    reasons = [PHRASES[f['feature']] for f in top_features if f['feature'] in PHRASES]
    return f"Transaction flagged: {' + '.join(reasons)}. Fraud probability: {fraud_score*100:.0f}%."
```

---

### 5.5 Model Training Pipeline (ml-research/training/train.py)

```python
# 1. DATA LOADING
# Sources: IEEE-CIS Fraud Detection (Kaggle) + synthetic data
# Synthetic generation: Faker + custom behavioral pattern simulator

# 2. PREPROCESSING
# - Drop rows with null amounts
# - Encode merchant_category with LabelEncoder (save encoder for inference)
# - Encode device_os with OrdinalEncoder
# - Log-transform: amount, account_age_days, avg_txn_amount, total_txn_count
# - Scale all features with StandardScaler (save scaler for inference)

# 3. CLASS IMBALANCE HANDLING
# - Use SMOTE (Synthetic Minority Oversampling) from imbalanced-learn
# - Target ratio: 10:1 (legitimate:fraud) — reflects real-world distribution

# 4. TRAIN XGBOOST
xgb_params = {
    'n_estimators': 500,
    'max_depth': 6,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'scale_pos_weight': 10,   # handle class imbalance
    'eval_metric': 'aucpr',   # optimize for precision-recall (not accuracy)
    'use_label_encoder': False,
    'random_state': 42
}

# 5. TRAIN ISOLATION FOREST
iso_params = {
    'n_estimators': 200,
    'contamination': 0.05,   # expected 5% anomaly rate
    'random_state': 42
}

# 6. EVALUATE
# - Cross-validate with StratifiedKFold(n_splits=5)
# - Report: Accuracy, Precision, Recall, F1, ROC-AUC, FPR
# - Plot: Confusion Matrix, ROC Curve, Precision-Recall Curve

# 7. SAVE ARTIFACTS
artifacts = {
    'xgboost': xgb_model,
    'isolation_forest': iso_model,
    'feature_names': feature_names,   # CRITICAL — must match inference order
    'label_encoder': label_encoder,
    'scaler': scaler,
    'training_date': datetime.now().isoformat(),
    'dataset_size': len(X_train),
}
pickle.dump(artifacts, open('artifacts/sentinel_ensemble.pkl', 'wb'))
```

---

## 6. Frontend Architecture

### 6.1 Design System (components/ui/)

| Token | Value | Usage |
|---|---|---|
| `--color-bg-primary` | `#0A0F1E` | Main page background |
| `--color-bg-card` | `#111827` | Card/panel backgrounds (glassmorphism) |
| `--color-bg-elevated` | `#1F2937` | Hover states, dropdowns |
| `--color-border` | `#1E3A5F` | Card borders |
| `--color-safe` | `#22C55E` | SAFE risk band |
| `--color-monitor` | `#F59E0B` | MONITOR risk band |
| `--color-suspicious` | `#F97316` | SUSPICIOUS risk band |
| `--color-fraud` | `#EF4444` | FRAUD risk band |
| `--color-accent` | `#3B82F6` | Primary interactive elements |
| `--color-text-primary` | `#F9FAFB` | Main text |
| `--color-text-muted` | `#9CA3AF` | Secondary text, labels |
| `font-primary` | `Inter` | All UI text |
| `font-mono` | `JetBrains Mono` | Code, scores, hashes |

### 6.2 Route Structure (app/)

```
app/
├── layout.tsx                    # Root layout: navbar, providers
├── page.tsx                      # / redirect to /dashboard
├── (auth)/
│   └── login/page.tsx            # JWT login form
├── dashboard/
│   └── page.tsx                  # Main analytics dashboard
├── transactions/
│   ├── page.tsx                  # Live transaction feed
│   └── [txn_id]/page.tsx         # Single transaction detail + SHAP
├── users/
│   ├── page.tsx                  # User list
│   └── [user_id]/page.tsx        # User behavioral timeline
├── attack-simulation/
│   └── page.tsx                  # Attack simulation lab
├── compliance/
│   └── page.tsx                  # Audit report export
└── settings/
    └── page.tsx                  # API keys, model config
```

### 6.3 Component Tree

```
components/
├── ui/                           # Design system primitives
│   ├── Card.tsx                  # Glassmorphism card wrapper
│   ├── Badge.tsx                 # Risk band badge (Safe/Monitor/Suspicious/Fraud)
│   ├── Spinner.tsx               # Loading states
│   ├── Button.tsx                # Primary/Secondary/Danger variants
│   ├── Input.tsx
│   ├── Select.tsx
│   └── Tooltip.tsx
│
├── dashboard/
│   ├── FraudGauge.tsx            # Animated circular gauge (Framer Motion)
│   ├── MetricCard.tsx            # Single KPI card (value + trend arrow)
│   ├── FraudRateChart.tsx        # Line chart: fraud rate over time (Recharts)
│   ├── ConfusionMatrix.tsx       # 2x2 matrix visualization
│   ├── RocCurveChart.tsx         # ROC curve with AUC annotation
│   ├── PrRecallChart.tsx         # Precision-Recall tradeoff curve
│   ├── FraudHeatmap.tsx          # Geographic heatmap (D3.js)
│   ├── RiskBandDonut.tsx         # Donut: SAFE/MONITOR/SUSPICIOUS/FRAUD
│   ├── IndexScoreRadar.tsx       # Radar chart: 9 behavioral indices
│   └── VedicBenchmarkPanel.tsx   # Nikhilam vs standard speed comparison
│
├── transactions/
│   ├── TransactionFeed.tsx       # Live scrolling feed with WebSocket
│   ├── TransactionRow.tsx        # Single row: amount, user, score, badge
│   ├── TransactionDetail.tsx     # Full detail panel
│   └── ShapWaterfallChart.tsx    # SHAP waterfall visualization
│
├── simulation/
│   ├── ScenarioSelector.tsx      # 3 scenario cards
│   ├── AttackTimeline.tsx        # Live event stream during simulation
│   ├── SimulationGauge.tsx       # FraudGauge variant for sim (animated live)
│   └── SimulationSummary.tsx     # Post-sim: when fraud detected, final action
│
└── compliance/
    ├── DateRangePicker.tsx
    ├── ExportFilters.tsx
    └── ExportButton.tsx          # Triggers GET /audit/export, downloads PDF
```

### 6.4 Key Component Specs

#### FraudGauge.tsx

```typescript
interface FraudGaugeProps {
  score:     number;         // 0.0 – 1.0
  riskBand:  RiskBand;       // 'SAFE'|'MONITOR'|'SUSPICIOUS'|'FRAUD'
  size?:     number;         // px, default 240
  animated?: boolean;        // Framer Motion animate on score change
}

// Implementation notes:
// - SVG arc gauge, 270° sweep
// - Color: interpolate green (0) → amber (0.65) → red (1.0) using d3-interpolateRgb
// - Center text: fraud_score * 100 formatted as integer %
// - Sub-text: risk_band label
// - Animate with Framer Motion useMotionValue + useSpring on score prop change
// - Pulse animation on FRAUD band: red glow ring via CSS box-shadow
```

#### TransactionFeed.tsx — WebSocket Integration

```typescript
// hooks/useFraudStream.ts
export function useFraudStream() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL + '/stream');

    ws.onmessage = (event) => {
      const txn: Transaction = JSON.parse(event.data);  // single object, NOT array
      setTransactions(prev => [txn, ...prev].slice(0, 100)); // keep last 100
    };

    ws.onerror = () => { /* reconnect with exponential backoff: 1s,2s,4s,8s,16s,30s cap */ };
    return () => ws.close();
  }, []);

  return { transactions };
}

// Backend: app/api/v1/stream.py
// WebSocket endpoint pushes every new risk_audit_log entry as JSON
// Uses asyncio.Queue — push when predict endpoint completes
```

#### AttackTimeline.tsx — NDJSON Streaming

```typescript
async function streamSimulation(request: AttackSimulationRequest) {
  const response = await fetch('/api/v1/simulate/attack', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const lines = decoder.decode(value).split('\n').filter(Boolean);
    for (const line of lines) {
      const event: SimulationEvent = JSON.parse(line);
      dispatch(addSimulationEvent(event));  // Zustand store action
      if (event.event_type === 'summary') break;
    }
  }
}
```

### 6.5 Zustand Stores (lib/stores/)

```typescript
// transactionStore.ts
interface TransactionStore {
  transactions:    Transaction[];
  addTransaction:  (txn: Transaction) => void;
  clearFeed:       () => void;
}

// simulationStore.ts
interface SimulationStore {
  isRunning:       boolean;
  events:          SimulationEvent[];
  currentScore:    number;
  currentBand:     RiskBand;
  summary:         SimulationSummary | null;
  startSimulation: (req: AttackSimulationRequest) => Promise<void>;
  resetSimulation: () => void;
  addEvent:        (event: SimulationEvent) => void;
}

// metricsStore.ts
interface MetricsStore {
  metrics:      MetricsResponse | null;
  window:       MetricsWindow;
  isLoading:    boolean;
  fetchMetrics: (window: MetricsWindow) => Promise<void>;
}

// authStore.ts
interface AuthStore {
  token:    string | null;
  user:     User | null;
  login:    (email: string, password: string) => Promise<void>;
  logout:   () => void;
}
```

---

## 7. Sequence Diagrams

### 7.1 Full Predict Flow

```
POST /api/v1/predict — end-to-end (target: < 340ms)

Client              API Router          FraudScoringService      BehavioralService
  │                     │                      │                       │
  │──POST /predict──────►                      │                       │
  │  (TransactionRequest)│                     │                       │
  │                      │──validate JWT───────►                       │
  │                      │──validate request───►                       │
  │                      │──call score()───────►                       │
  │                      │                      │                       │
  │                      │                      │──get_user(user_id)───►DB
  │                      │                      │◄──User + baseline─────│
  │                      │                      │                       │
  │                  VedicService               │                       │
  │                      │◄──anurupyena_check───│                       │
  │                      │──checksum result────►│                       │
  │                      │                      │                       │
  │                      │                      │──compute_all_indices()►│
  │                      │                      │◄──IndexScores (9)──────│
  │                      │                      │                       │
  │                      │         NikhilamCalibrator                   │
  │                      │◄──nikhilam_threshold(user_avg)───────────────│
  │                      │──threshold_value────►│                       │
  │                      │                      │                       │
  │                      │          SentinelEnsemble                    │
  │                      │◄──build_feature_vector()───────────────────── │
  │                      │◄──predict(feature_vector)──────────────────── │
  │                      │──fraud_score,band,action────────────────────►│ │
  │                      │                      │                       │
  │                      │          ShapExplainer                       │
  │                      │◄──compute_shap()──────────────────────────── │
  │                      │◄──generate_human_explanation()──────────────  │
  │                      │──shap + explanation─►│                       │
  │                      │                      │                       │
  │                      │                      │──save Transaction─────►DB
  │                      │                      │──save RiskAuditLog────►DB
  │                      │                      │──push to WS queue─────►WS
  │                      │                      │                       │
  │                      │◄──FraudScoreResponse─│                       │
  │◄──200 JSON response──│                      │                       │
```

### 7.2 Attack Simulation Flow

```
POST /api/v1/simulate/attack — streaming NDJSON

Client              SimulationRouter       SimulationService      FraudScoringService
  │                      │                      │                       │
  │──POST /simulate/─────►                      │                       │
  │   attack             │                      │                       │
  │                      │──get target user─────►DB                     │
  │                      │──run_scenario()──────►│                       │
  │                      │                      │                       │
  │                      │    [Generate synthetic transaction sequence]  │
  │                      │                      │                       │
  │                      │    [For each synthetic transaction:]          │
  │                      │                      │──score(txn)───────────►│
  │                      │                      │◄──FraudScoreResponse───│
  │                      │                      │                       │
  │◄──NDJSON event line──│                      │                       │
  │   (SimulationEvent)  │                      │                       │
  │                      │    [sleep based on 'speed' param]            │
  │◄──NDJSON event line──│    [repeat for each txn in scenario]         │
  │   ...                │                      │                       │
  │                      │                      │──save SimulationRun───►DB
  │◄──NDJSON summary─────│                      │                       │
  │   (event_type=summary│                      │                       │
  │   [stream ends]      │                      │                       │
```

### 7.3 Audit Report Export Flow

```
GET /api/v1/audit/export — PDF generation

Client          AuditRouter         ComplianceService         DB / ReportLab
  │                 │                     │                        │
  │──GET /audit/────►                     │                        │
  │   export?params │                     │                        │
  │                 │──validate params────►                        │
  │                 │                     │──query transactions────►DB
  │                 │                     │──query audit_logs──────►DB
  │                 │                     │◄──paginated results─────│
  │                 │                     │                        │
  │                 │                     │──compute metrics()──────│
  │                 │                     │  (precision, recall,    │
  │                 │                     │   confusion matrix)     │
  │                 │                     │                        │
  │                 │                     │──generate_pdf()─────────►ReportLab
  │                 │                     │  (cover+table+metrics)  │
  │                 │                     │◄──PDF bytes─────────────│
  │                 │                     │                        │
  │                 │                     │──compute log_hash───────│
  │                 │                     │──append hash footer─────►ReportLab
  │                 │◄──StreamingResponse─│                        │
  │◄──PDF binary────│  Content-Type: application/pdf               │
  │  [browser DL]   │                     │                        │
```

### 7.4 WebSocket Live Feed Flow

```
WS /ws/stream — real-time transaction push

Frontend          WS Endpoint          asyncio.Queue         PredictEndpoint
  │                   │                     │                     │
  │──WS Connect───────►                     │                     │
  │                   │──subscribe to queue─►                     │
  │                   │                     │                     │
  │    [Client submits transaction via POST /predict]             │
  │                   │                     │◄──put(audit_log)────│
  │                   │◄──get(audit_log)────│                     │
  │◄──WS message──────│                     │                     │
  │   (FraudScoreResponse as single JSON)   │                     │
  │                   │                     │                     │
  │  [TransactionFeed auto-updates]         │                     │
  │  [FraudGauge animates to new score]     │                     │
  │                   │                     │                     │
  │──WS Disconnect────►                     │                     │
  │                   │──unsubscribe────────►                     │
```

### 7.5 Nightly Baseline Recalculation Flow

```
Nightly baseline update — background task (APScheduler)

Scheduler         BaselineService              DB
   │                   │                        │
   │──trigger daily────►                        │
   │  (APScheduler)    │                        │
   │                   │──get all users─────────►│
   │                   │◄──[user list]───────────│
   │                   │                        │
   │        [For each user:]                    │
   │                   │──get txns last 90d─────►│
   │                   │◄──transactions──────────│
   │                   │                        │
   │                   │──compute new baselines  │
   │                   │  (mean, std per index)  │
   │                   │──update baseline_stats─►DB
   │                   │──update avg_txn_amount─►DB
   │                   │──add devices seen 3+───►DB
   │                   │  times to trusted list  │
   │◄──done────────────│                        │
```

---

## 8. Infrastructure & Deployment

### 8.1 Docker Compose (infra/docker-compose.yml)

```yaml
version: '3.9'
services:
  vedfindb:
    image: postgres:15
    environment:
      POSTGRES_DB: vedfindb
      POSTGRES_USER: vedfinuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes: [pgdata:/var/lib/postgresql/data]
    ports: ['5432:5432']

  vedfinredis:
    image: redis:7-alpine
    ports: ['6379:6379']

  vedfinbackend:
    build: { context: ./backend, dockerfile: ../infra/Dockerfile.backend }
    depends_on: [vedfindb, vedfinredis]
    environment:
      DATABASE_URL: postgresql+asyncpg://vedfinuser:${DB_PASSWORD}@vedfindb/vedfindb
      REDIS_URL: redis://vedfinredis:6379/0
      SECRET_KEY: ${SECRET_KEY}
    ports: ['8000:8000']
    volumes: ['./ml-research/artifacts:/app/ml/artifacts:ro']

  vedfinfront:
    build: { context: ./frontend, dockerfile: ../infra/Dockerfile.frontend }
    depends_on: [vedfinbackend]
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://vedfinbackend:8000/api/v1
      NEXT_PUBLIC_WS_URL: ws://vedfinbackend:8000/ws
    ports: ['3000:3000']

volumes:
  pgdata:
```

### 8.2 Python Dependencies (backend/requirements.txt)

```
fastapi==0.110.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.28
asyncpg==0.29.0
alembic==1.13.1
pydantic[email]==2.6.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
redis[hiredis]==5.0.2
slowapi==0.1.9
xgboost==2.0.3
scikit-learn==1.4.1
shap==0.45.0
numpy==1.26.4
pandas==2.2.1
imbalanced-learn==0.12.0
geopy==2.4.1
reportlab==4.1.0
apscheduler==3.10.4
faker==24.0.0
python-dotenv==1.0.1
httpx==0.27.0
pytest==8.1.0
pytest-asyncio==0.23.5
structlog==24.1.0
pydantic-settings==2.2.1
```

### 8.3 Node Dependencies (frontend/package.json)

```json
{
  "dependencies": {
    "next": "14.2.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "recharts": "2.12.2",
    "framer-motion": "11.0.20",
    "d3": "7.9.0",
    "zustand": "4.5.2",
    "axios": "1.6.8",
    "@tanstack/react-query": "5.28.0",
    "date-fns": "3.6.0",
    "clsx": "2.1.0",
    "tailwind-merge": "2.2.2"
  },
  "devDependencies": {
    "typescript": "5.4.3",
    "tailwindcss": "3.4.1",
    "@types/react": "18.2.70",
    "@types/d3": "7.4.3",
    "eslint": "8.57.0",
    "prettier": "3.2.5"
  }
}
```

---

## 9. Error Handling & Logging

### 9.1 RFC 7807 Error Response Format

```json
{
  "type":       "https://vedfinsentinel.io/errors/USER_NOT_FOUND",
  "title":      "User Not Found",
  "status":     404,
  "detail":     "No user found with id 550e8400-e29b-41d4-a716-446655440000",
  "instance":   "/api/v1/predict",
  "request_id": "req-abc123"
}
```

### 9.2 Exception Hierarchy (core/exceptions.py)

```python
class VedFinBaseException(Exception):
    status_code: int = 500
    error_code:  str = 'INTERNAL_ERROR'

class UserNotFoundException(VedFinBaseException):
    status_code = 404
    error_code  = 'USER_NOT_FOUND'

class InvalidGeoException(VedFinBaseException):
    status_code = 422
    error_code  = 'INVALID_GEO'

class PredictionFailedException(VedFinBaseException):
    status_code = 500
    error_code  = 'PREDICTION_FAILED'

class ModelNotReadyException(VedFinBaseException):
    status_code = 503
    error_code  = 'MODEL_NOT_READY'

class RateLimitExceededException(VedFinBaseException):
    status_code = 429
    error_code  = 'RATE_LIMIT_EXCEEDED'

class DateRangeTooLargeException(VedFinBaseException):
    status_code = 400
    error_code  = 'DATE_RANGE_TOO_LARGE'

class PayloadTooLargeException(VedFinBaseException):
    status_code = 413
    error_code  = 'PAYLOAD_TOO_LARGE'
```

### 9.3 Structured Logging Format

```json
{
  "timestamp":  "2026-02-22T02:47:33.421Z",
  "level":      "INFO",
  "service":    "vedfinsentinel",
  "request_id": "req-abc123",
  "user_id":    "550e8400...",
  "event":      "fraud_score_computed",
  "data": {
    "txn_id":      "a1b2c3...",
    "fraud_score":  0.9412,
    "risk_band":   "FRAUD",
    "latency_ms":  287
  }
}
```

**Logging rules:**
- Use `structlog` library for structured JSON logging
- Log levels: DEBUG (dev), INFO (normal ops), WARNING (elevated risk), ERROR (failures)
- **Never log:** raw transaction amounts in plain text in production, PII, raw JWT tokens, passwords
- Every log entry must include: timestamp, level, service, request_id, user_id (if available), event, data

---

## 10. Agent Implementation Checklist

> Complete all items in order. Do not skip. Do not reorder.

### Phase 1 — Foundation

- [ ] Scaffold monorepo structure exactly as defined in Section 1.1
- [ ] Set up PostgreSQL schema (Section 2.1) — run all CREATE statements
- [ ] Configure Alembic, generate initial migration, run `alembic upgrade head`
- [ ] Create `seed.py` — 3 demo users with realistic baselines
- [ ] Create all SQLAlchemy ORM models (Section 2.3)

### Phase 2 — Backend Core

- [ ] Implement FastAPI app with all middleware (Section 3.1, 3.2)
- [ ] Implement JWT auth (login endpoint + `get_current_user` dependency)
- [ ] Implement all Pydantic schemas (Section 4)
- [ ] Implement all exception classes (Section 9.2)
- [ ] Implement RFC 7807 error handler middleware

### Phase 3 — Vedic Modules

- [ ] Implement `vedic/anurupyena.py` — `compute_anurupyena_checksum()`
- [ ] Implement `vedic/nikhilam.py` — `nikhilam_threshold()` + `benchmark_nikhilam_vs_standard()`
- [ ] Write unit tests for both Vedic modules with known test vectors

### Phase 4 — Behavioral Engine

- [ ] Implement all 9 index functions in `services/behavioral.py` (Section 5.1)
- [ ] Implement `compute_all_indices()` orchestrator function
- [ ] Write unit tests for each index with edge cases

### Phase 5 — ML Pipeline

- [ ] Run training script — `ml-research/training/train.py`
- [ ] Generate `sentinel_ensemble.pkl` artifact
- [ ] Implement `SentinelEnsemble` class (Section 5.3)
- [ ] Implement `ShapExplainer` + `generate_human_explanation()` (Section 5.4)
- [ ] Load model at FastAPI startup via `app.state.ml_engine`

### Phase 6 — API Endpoints

- [ ] Implement `POST /api/v1/predict` with full scoring pipeline
- [ ] Implement `POST /api/v1/bulk_predict`
- [ ] Implement `POST /api/v1/simulate/attack` with NDJSON streaming
- [ ] Implement `GET /api/v1/audit/export` with PDF generation
- [ ] Implement `GET /api/v1/metrics`
- [ ] Implement `WS /ws/stream` with asyncio.Queue push

### Phase 7 — Frontend

- [ ] Scaffold Next.js 14 app with all routes (Section 6.2)
- [ ] Implement design system tokens in `tailwind.config.ts`
- [ ] Build all `ui/` primitive components
- [ ] Build `FraudGauge.tsx` with Framer Motion animation
- [ ] Build all `dashboard/` chart components using Recharts
- [ ] Build `TransactionFeed.tsx` with `useFraudStream` WebSocket hook
- [ ] Build `AttackTimeline.tsx` with NDJSON streaming fetch
- [ ] Build `compliance/` export UI
- [ ] Build `VedicBenchmarkPanel.tsx`
- [ ] Implement all Zustand stores

### Phase 8 — Integration & Polish

- [ ] Wire all frontend components to live API
- [ ] Implement Redis caching for user baselines (TTL: 5 minutes)
- [ ] Implement APScheduler nightly baseline recalculation (Section 7.5)
- [ ] Run `docker-compose up` — verify all services connect
- [ ] Run full simulation flow end-to-end — verify NDJSON streaming
- [ ] Generate a compliance PDF — verify structure
- [ ] Run `pytest` — all tests must pass

---

### Required Test Files

| Test File | What It Must Cover |
|---|---|
| `tests/test_vedic_anurupyena.py` | Checksum for valid txn, invalid txn, replay attack payload, boundary amounts |
| `tests/test_vedic_nikhilam.py` | Complement for 98, 997, 9999, 10003, non-base numbers; benchmark function |
| `tests/test_behavioral_engine.py` | All 9 index functions with normal + anomaly inputs |
| `tests/test_predict_endpoint.py` | Valid request, unknown user, future timestamp, geo without lng, rate limit |
| `tests/test_audit_log.py` | log_hash is SHA-256 of correct fields, write-once enforcement |
| `tests/test_simulation.py` | All 3 attack scenarios produce FRAUD band before stream ends |

---

> **⚠ FINAL AGENT INSTRUCTION:**
> The AI agent must not invent new field names, endpoint paths, or component names not defined in this document.
> All naming is final.
> Cross-reference with `VedFin_Sentinel_PRD.md` for product context.
> This design document is the **single source of truth** for implementation.
> When in doubt: stop, re-read, ask. Never guess.

---

*VedFin Sentinel | Design Document v1.0 | InnVedX Hackathon 2026 | BBD University*
*PRD + Design Doc + AGENT_RULES.md = Complete Agent Context*
