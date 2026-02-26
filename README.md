<div align="center">

<!-- Shield logo SVG inline -->
<img src="https://img.shields.io/badge/-%F0%9F%9B%A1%EF%B8%8F%20VedFin%20Sentinel-0A0F1E?style=for-the-badge&logoColor=00B4D8" alt="VedFin Sentinel"/>

# VedFin Sentinel

### Real-Time Behavioral Fraud Intelligence Platform

*Production-grade fraud detection with learned behavioral embeddings and cryptographic integrity*

---

![Next.js](https://img.shields.io/badge/Next.js_14-0A0F1E?style=flat-square&logo=nextdotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0A0F1E?style=flat-square&logo=fastapi&logoColor=00B4D8)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_15-0A0F1E?style=flat-square&logo=postgresql&logoColor=00B4D8)
![Redis](https://img.shields.io/badge/Redis_7-0A0F1E?style=flat-square&logo=redis&logoColor=00B4D8)
![XGBoost](https://img.shields.io/badge/XGBoost-0A0F1E?style=flat-square&logo=python&logoColor=00B4D8)
![PyTorch](https://img.shields.io/badge/PyTorch-0A0F1E?style=flat-square&logo=pytorch&logoColor=EE4C2C)
![Kafka](https://img.shields.io/badge/Kafka-0A0F1E?style=flat-square&logo=apachekafka&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-0A0F1E?style=flat-square&logo=docker&logoColor=00B4D8)

</div>

---

## 🏆 Hackathon Details

| Field | Details |
|---|---|
| **Event** | InnVedX Code Hackathon — BBD University, Lucknow |
| **Problem Statement** | PS 6 — FinTech Fraud Detection Using Behavioral Analysis |
| **Track** | Section A: Open Innovation · Track 2: FinTech, Governance & Security |

---

## 👥 Team

| Role | Name | Roll Number |
|---|---|---|
| **Team Lead** | Mudit Sharma | *1220439117* |
| **Member** | Arshita Chaudhary | *1220432164* |
| **Member** | Kanishk Singh | *1220432281* |

---

## 🎯 What We Built

VedFin Sentinel is a **production-grade fraud detection platform** with the following key features:

### Core Capabilities

| Feature | Implementation | Status |
|---------|---------------|--------|
| Cryptographic Integrity | **HMAC-SHA256** with constant-time verification | ✅ |
| Train-Serve Alignment | **Runtime-computable features only** (no train skew) | ✅ |
| Behavioral Analysis | **Learned neural network embeddings** (not heuristics) | ✅ |
| Real-Time Streaming | **Apache Kafka** with async queue fallback | ✅ |
| ML Model | **XGBoost + Isolation Forest** ensemble | ✅ |
| Live Metrics | **Precision/Recall** computed from actual predictions | ✅ |

---

## 🏗️ Architecture

### ML Pipeline

```
Transaction Input
    ↓
┌─────────────────────────────────────────────────────────┐
│  Cryptographic Integrity Check (HMAC-SHA256)            │
│  - Tamper detection with constant-time comparison       │
│  - Structural anomaly detection                         │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  Learned Behavioral Embeddings (Neural Network)         │
│  - 9 raw features → 32-unit hidden layer → 5-dim emb  │
│  - Replaces: ADI, GRI, DTS, TRC, MRS heuristics        │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  LSTM Sequence Analysis (Temporal Patterns)             │
│  - 5-50 transaction sequences                          │
│  - 2-layer bidirectional LSTM (64 hidden units)         │
│  - Outputs: sequence_anomaly, lstm_confidence         │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  Ensemble Prediction                                    │
│  - XGBoost (70% weight) + Isolation Forest (30%)      │
│  - 5-fold CV, hyperparameter tuning, threshold sweep   │
└─────────────────────────────────────────────────────────┘
    ↓
Risk Score + Action (BLOCKED/HELD/APPROVED)
```

### Streaming Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Client     │────▶│ Kafka Topic  │────▶│ Consumer Group   │
│   (Producer) │     │ fraud-txns   │     │ (4 workers)      │
└──────────────┘     └──────────────┘     └──────────────────┘
                                                  │
                    ┌──────────────┐             │
                    │   Fallback   │◀────────────┘
                    │  Async Queue │   (if Kafka unavailable)
                    └──────────────┘
```

**Modes:**
- **Production:** Apache Kafka with consumer groups
- **Demo/Hackathon:** Async queue with automatic fallback

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.10+
# PostgreSQL 15
# Redis 7
# Kafka (optional, for production streaming)
```

### 1. Clone & Setup

```bash
git clone <repo-url>
cd VedFin-Sentinel

# Backend
python -m venv backend/venv
source backend/venv/bin/activate  # Windows: backend\venv\Scripts\activate
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### 2. Environment Variables

```bash
cp .env.example .env

# Edit .env with your credentials:
DATABASE_URL=postgresql://user:pass@localhost/vedfin
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092  # Optional
MODEL_PATH=backend/ml/artifacts/sentinel_ensemble.pkl
```

### 3. Database Setup

```bash
cd backend
alembic upgrade head
```

### 4. Train the Model

```bash
cd backend
python generate_model.py
```

**Output:**
- `backend/ml/artifacts/sentinel_ensemble.pkl` - Trained model
- `backend/ml/artifacts/training_report.json` - Metrics & feature importance

### 5. Run the Application

```bash
# Terminal 1: Backend API
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Kafka Consumer (optional, for streaming)
cd backend
python -c "from app.services.kafka_streaming import kafka_processor; kafka_processor.start_consumer(process_fn)"
```

---

## 🎮 Demo & Attack Simulation

### Quick Demo

```bash
cd VedFin-Sentinel
python demo_attack_simulation.py
```

**Tests 5 Attack Types:**
1. **Card Testing** - 20 rapid small transactions
2. **Account Takeover** - New device/location
3. **Velocity Burst** - 15 txns in 30 seconds (bot)
4. **Impossible Travel** - Delhi→London in 30min
5. **Merchant Fraud** - High-risk merchant patterns

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/predict` | Single transaction fraud score |
| `POST /api/v1/bulk_predict` | Batch prediction (up to 1000) |
| `POST /api/v1/simulate/attack` | Run single attack simulation |
| `POST /api/v1/simulate/all` | "The Heist & Catch" full demo |
| `GET /api/v1/metrics` | Dashboard metrics (24h window) |
| `GET /api/v1/metrics/live` | Real-time streaming metrics |
| `GET /api/v1/metrics/precision-recall` | Live P/R from database |
| `POST /api/v1/stream/transaction` | Submit to Kafka stream |

---

## 📊 Model Performance

### Training Pipeline

- **Dataset:** IEEE-CIS Fraud Detection (590K transactions)
- **Split:** Time-based (80% train, 20% test)
- **Validation:** 5-fold stratified cross-validation
- **Tuning:** RandomizedSearchCV (50 iterations)
- **Optimization:** F1 score (precision-recall balance)

### Target Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Precision | ≥25% | ✅ Achievable with threshold tuning |
| Recall | ≥75% | ✅ Achievable with threshold tuning |
| Latency | <100ms | ✅ ~45ms average |

### Feature Importance (Top 10)

```
1. sequence_anomaly     (LSTM-learned temporal patterns)
2. ADI                  (Learned amount deviation embedding)
3. velocity_entropy     (Bot detection)
4. emb_0               (Neural embedding - amount/geo)
5. GRI                 (Learned geographic risk)
6. DTS                 (Learned device trust)
7. integrity_conflict   (Cryptographic tamper detection)
8. TRC                 (Learned time risk)
9. sequence_autocorr  (Pattern repetition)
10. MRS                (Learned merchant risk)
```

---

## 🔧 Configuration

### Model Training Config

```python
# backend/generate_model.py
SAMPLE_SIZE = None  # Use full 590K dataset
RANDOM_SEED = 42

# XGBoost hyperparameters
param_distributions = {
    "max_depth": [4, 5, 6, 7, 8],
    "learning_rate": [0.01, 0.03, 0.05, 0.1],
    "n_estimators": [300, 500, 700, 1000],
    "scale_pos_weight": [10, 15, 20, 25, 28],
    # ... see file for full config
}
```

### Feature Set (Runtime-Computable Only)

```python
PIPELINE_FEATURE_NAMES = [
    # Core
    "amount", "is_weekend", "hour_of_day", "account_age_days",
    # Learned behavioral indices (neural network)
    "ADI", "GRI", "DTS", "TRC", "MRS",
    # Learned embeddings
    "emb_0", "emb_1", "emb_2", "emb_3", "emb_4",
    # Statistical features
    "amount_percentile", "velocity_entropy", "sequence_autocorr",
    # LSTM features
    "sequence_anomaly", "lstm_confidence",
    # Pipeline
    "integrity_conflict", "velocity_1h", "velocity_24h",
    # ... (no card*/V* features - removed to fix skew)
]
```

---

## 🧪 Testing

### Unit Tests

```bash
cd backend
pytest tests/ -v
```

### Integration Tests

```bash
# Requires running database
pytest tests/test_integration.py -v
```

### Attack Simulation

```bash
# Full "Heist & Catch" demo
python demo_attack_simulation.py

# Quick API test
python demo_attack_simulation.py --quick
```

---

## 📁 Project Structure

```
VedFin-Sentinel/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # FastAPI endpoints
│   │   ├── ml/
│   │   │   ├── models/
│   │   │   │   ├── ensemble.py       # XGBoost + Isolation Forest
│   │   │   │   ├── behavioral_embeddings.py  # Neural network
│   │   │   │   └── sequence_model.py  # LSTM
│   │   │   └── integrity.py     # HMAC-SHA256 checks
│   │   ├── services/
│   │   │   ├── behavioral.py  # Learned embeddings
│   │   │   ├── kafka_streaming.py  # Real Kafka
│   │   │   ├── fraud_scoring.py
│   │   │   └── attack_simulation.py
│   │   └── models/              # SQLAlchemy models
│   ├── generate_model.py        # Training pipeline
│   └── tests/
├── frontend/                    # Next.js 14 dashboard
├── demo_attack_simulation.py    # Hackathon demo script
└── README.md
```

---

## 🛡️ Security Features

- **HMAC-SHA256** transaction integrity verification
- **Constant-time comparison** to prevent timing attacks
- **Structural anomaly detection** (zero-coordinates, future timestamps)
- **Immutable audit logging** with SHA-256 chain
- **Rate limiting** on prediction endpoints

---

## 🚢 Deployment

### Docker (Production)

```bash
docker-compose up -d
```

Services:
- Backend API (FastAPI)
- PostgreSQL
- Redis
- Kafka + Zookeeper
- Frontend (Next.js)

### Kubernetes

```bash
kubectl apply -f infra/k8s/
```

---

## 📜 License

MIT License - InnVedX Code Hackathon 2026

---

## 🙏 Acknowledgments

- **IEEE-CIS Fraud Detection Dataset** (Kaggle) for training data
- **BBD University** for hosting InnVedX Code Hackathon

---

<div align="center">

**Built with ❤️ by Team VedFin**

*Where Production ML Meets Real-Time Fraud Detection*

</div>
