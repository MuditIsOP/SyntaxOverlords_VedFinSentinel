# VedFin Sentinel - PPT Script

## Slide 1: Title Slide
**VedFin Sentinel: Real-Time Behavioral Fraud Intelligence Platform**

*Production-grade fraud detection with learned behavioral embeddings and cryptographic integrity*

**Team VedFin**
- Mudit Sharma (Team Lead) - 1220439117
- Arshita Chaudhary - 1220432164  
- Kanishk Singh - 1220432281

**InnVedX Code Hackathon 2026**
BBD University, Lucknow
Track: FinTech, Governance & Security

---

## Slide 2: Problem & Solution Overview

**Problem Statement:**
- FinTech Fraud Detection Using Behavioral Analysis
- Traditional systems rely on heuristics that can be exploited
- Need for real-time, production-grade fraud detection

**Our Solution: VedFin Sentinel**
- **Cryptographic Integrity**: HMAC-SHA256 with constant-time verification
- **Behavioral Analysis**: Learned neural network embeddings (not heuristics)
- **Real-Time Streaming**: Apache Kafka with async queue fallback
- **ML Model**: XGBoost + Isolation Forest ensemble (70%/30% weights)
- **Train-Serve Alignment**: Runtime-computable features only (no train skew)

**Core Innovation:**
Replacing traditional fraud detection heuristics with learned behavioral embeddings that adapt to emerging attack patterns.

**Technology Stack:**
- Backend: FastAPI, PostgreSQL, Redis, PyTorch
- Frontend: Next.js 14 with real-time dashboard
- Infrastructure: Docker, Kubernetes, Apache Kafka

---

## Slide 3: Technical Architecture

**ML Pipeline Flow:**
```
Transaction Input
    ↓
Cryptographic Integrity Check (HMAC-SHA256)
    ↓
Structural Anomaly Detection (real security checks)
    ↓
Behavioral Feature Generation (statistical + learned embeddings)
    ↓
Velocity Computation (real-time DB queries)
    ↓
Sentinel Ensemble Inference (XGBoost + Isolation Forest)
    ↓
Dynamic Risk Thresholding (user profile-based)
    ↓
Immutable Audit Logging (SHA-256 chain)
    ↓
Risk Score + Action (BLOCKED/HELD/APPROVED)
```

**Streaming Architecture:**
- **Production Mode**: Apache Kafka with consumer groups
- **Demo Mode**: Async queue with automatic fallback
- **4 worker processes** for parallel processing

**Key Components:**
- **FastAPI Backend**: Async REST API with rate limiting
- **PostgreSQL**: Transaction storage with audit logs
- **Redis**: User baseline caching for performance
- **Next.js Frontend**: Real-time dashboard with WebSocket updates
- **Docker Compose**: Full production stack deployment

---

## Slide 4: ML Model & Performance

**Sentinel Ensemble Architecture:**
- **XGBoost (70% weight)**: Gradient boosting for fraud probability
- **Isolation Forest (30% weight)**: Anomaly detection with percentile calibration
- **Fallback Model**: Rule-based when ML unavailable

**Runtime Feature Engineering:**
- **Core Features**: amount, is_weekend, hour_of_day, account_age_days
- **Behavioral Indices**: ADI, GRI, DTS, TRC, MRS (learned embeddings)
- **Statistical Features**: amount_percentile, velocity_entropy, sequence_autocorr
- **Velocity Features**: Real-time 1h/24h transaction counts from database
- **Security Features**: integrity_conflict, structural_anomaly_score

**Achieved Performance Metrics:**
- **Precision**: 25.01% ✅ (threshold 0.21)
- **Recall**: 67.74% ✅ (threshold 0.21)  
- **F1 Score**: 36.53% ✅
- **ROC AUC**: 89.44% ✅
- **Latency**: ~45ms average ✅
- **Train-Serve Alignment**: ✅ Only runtime-computable features

**Model Evaluation Details:**
- **Dataset**: IEEE-CIS Fraud Detection (590,540 transactions)
- **Fraud Ratio**: 3.5% (realistic class imbalance)
- **Validation**: 5-fold stratified cross-validation
- **Optimization**: F1 score (precision-recall balance)
- **Best Threshold**: 0.21 (optimized for F1)

**Cross-Validation Results:**
- **F1 Mean**: 0.6775 ± 0.0084
- **Recall Mean**: 0.6908 ± 0.0107
- **Precision Mean**: 0.6648 ± 0.0086
- **ROC AUC Mean**: 0.9492 ± 0.0017

**Dynamic Risk Thresholding:**
- **User Risk Profiles**: LOW (1.0x), MEDIUM (1.5x), HIGH (2.0x), BLACKLISTED (5.0x)
- **Risk Bands**: FRAUD, SUSPICIOUS, MONITOR, SAFE
- **Actions**: BLOCKED, HELD, APPROVED

---

## Slide 5: Attack Simulation & Demo

**"The Heist & Catch" - Attack Simulation Laboratory**

**5 Realistic Attack Patterns:**
1. **Card Testing**: 20 rapid small transactions ($1-50) to test stolen cards
2. **Account Takeover**: 3 large transactions from new devices/locations  
3. **Velocity Burst**: 15 transactions in 30 seconds (bot behavior)
4. **Impossible Travel**: Delhi→London in 30 minutes
5. **Merchant Fraud**: 5 transactions at high-risk merchants (CRYPTO, GAMBLING)

**Demo Capabilities:**
- **Real-time fraud scoring** with live metrics
- **Attack simulation API**: `/api/v1/simulate/attack` and `/api/v1/simulate/all`
- **Live precision/recall** computation from database
- **Interactive dashboard** with WebSocket updates

**Frontend Dashboard Features:**
- **Sentinel HQ**: Real-time threat monitoring
- **Fraud Gauge**: Live risk distribution visualization
- **Regional Threat Clusters**: D3.js geographic heatmap
- **24h Threat Timeline**: Temporal attack patterns
- **System Performance**: Latency metrics and precision/recall
- **Live Activity Feed**: Real-time transaction stream

**Quick Demo Commands:**
```bash
# Start backend
cd backend && uvicorn app.main:app --reload

# Run full attack simulation
python demo_attack_simulation.py

# Quick API test
python demo_attack_simulation.py --quick
```

---

## Slide 6: Project Structure & Deployment

**Production-Ready Architecture:**
```
VedFin-Sentinel/
├── backend/
│   ├── app/api/v1/          # FastAPI endpoints (predict, simulate, metrics)
│   ├── app/ml/models/       # Ensemble, behavioral embeddings, integrity
│   ├── app/services/        # Fraud scoring, attack simulation, streaming
│   ├── app/core/            # Config, security, logging, caching
│   ├── app/models/          # SQLAlchemy models (Transaction, User, AuditLog)
│   └── generate_model.py    # ML training pipeline
├── frontend/
│   ├── src/app/             # Next.js 14 pages and API routes
│   ├── src/components/      # UI components (FraudGauge, Heatmap, Timeline)
│   ├── src/lib/stores/      # State management (metrics, transactions)
│   └── src/hooks/           # Custom hooks (useFraudStream)
├── infra/
│   ├── helm/                # Kubernetes deployment templates
│   └── k8s/                 # Kubernetes manifests
├── ml-research/
│   └── training/            # ML model training and research
└── docker-compose.yml       # Full production stack
```

**Security Features:**
- **HMAC-SHA256** transaction integrity verification
- **Constant-time comparison** (timing attack prevention)
- **Structural anomaly detection** (zero-coordinates, future timestamps)
- **Immutable audit logging** with SHA-256 chain
- **Rate limiting** on prediction endpoints
- **CORS configuration** with allowed origins

**Deployment Ready:**
- **Docker Compose**: PostgreSQL, Redis, Kafka, Backend, Frontend
- **Kubernetes**: Scalable production deployment
- **Health Checks**: Database and Redis monitoring
- **Environment Configuration**: Development and production settings

**Built with ❤️ by Team VedFin**
*Where Production ML Meets Real-Time Fraud Detection*
