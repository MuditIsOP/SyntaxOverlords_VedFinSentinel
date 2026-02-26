# VedFin Sentinel — PPT Content (4 Slides)

> Based on the InnVedX Code Hackathon PPT Template and the PRD.

---

## SLIDE 1 — Title Slide

**Title:** VedFin Sentinel

**Subtitle:** Real-Time Behavioral Fraud Intelligence Platform

- **Team Lead:** [Your Name]
- **Members:** [Member 1], [Member 2], [Member 3]
- **Problem Statement:** PS 6 — FinTech Fraud Detection Using Behavioral Analysis
- **Track:** Section A: Open Innovation | Track 2: FinTech, Governance & Security

---

## SLIDE 2 — Problem & Solution

### The Problem

- India processed **131 Billion+ UPI transactions** in FY2024
- Digital financial fraud cost **₹14,000+ crore** in the same year
- Current systems are **rule-based, static, and opaque** — attackers adapt within days
- **No per-user behavioral baseline** — a ₹50,000 transaction flagged for one user is normal for another
- Average fraud detection lag: **4–6 hours** post-transaction
- Industry false positive rate: **15–30%**, disrupting legitimate users
- **~95% of flagged transactions** have zero explainability — rejected by RBI compliance auditors

### Our Solution — VedFin Sentinel

- A **real-time behavioral fraud intelligence platform** that detects anomalies in **under 340 milliseconds** (SQLite local benchmark — PostgreSQL+Redis production latency may vary)
- Computes a **9-dimensional behavioral fingerprint** per user per transaction — each index outputs a **continuous 0–1 spectrum** (not binary flags):
  - Amount Deviation (ADI), Geo-Shift Risk (GRI), Device Trust (DTS), Time Risk (TRC), Merchant Risk (MRS), Burst Frequency (BFI), Behavioral Drift (BDS), Velocity Reversal (VRI), Social Graph Anomaly (SGAS)
- **Real behavioral modeling features**: EWMA deviation tracking (exponentially weighted moving average), behavioral drift detection (comparing recent vs historical baselines), and **sequence-based analysis** (amount escalation detection, time-gap acceleration, category diversity tracking) — genuine temporal pattern analysis across transaction sequences
- **Hybrid ML Ensemble**: XGBoost (50% weight, supervised — catches known fraud) + Isolation Forest (20% weight, unsupervised — catches novel anomalies, percentile-calibrated against training distribution) + Behavioral signals (30% weight)
- **Vedic Mathematics Layer** *(Cultural Innovation & Algorithmic Diversity)*:
  - **Anurupyena Beejank Checksum**: A lightweight sanity check inspired by Vedic arithmetic verification (casting out nines). Produces a digital root (1-9) for fast pre-screening — not a replacement for cryptographic integrity (SHA-256 handles that in audit logs). Think of it as a quick "does this look right?" test using an elegant ancient algorithm.
  - **Nikhilam Sutra**: Demonstrates Vedic near-base multiplication for threshold calibration — mathematically equivalent to standard multiplication but showcases an alternative computational approach from Indian mathematical heritage.
- **SHAP Explainability**: Every flagged transaction comes with human-readable explanations (e.g., "Transaction amount is 3.2× above user baseline average") meeting RBI Model Risk Management guidelines
- **Attack Simulation Lab**: Live demo of 3 attack scenarios (Velocity Burst, Impossible Travel, Vedic Checksum Collision) detected in real time

---

## SLIDE 3 — Tech Stack & Methodology

### Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14 (App Router), TailwindCSS, Recharts, Framer Motion |
| **Backend** | FastAPI (Python 3.11), Async SQLAlchemy, JWT Auth |
| **ML Engine** | XGBoost + Isolation Forest (Hybrid Sentinel Ensemble), trained on IEEE-CIS Fraud Detection dataset (590K transactions) |
| **ML Rigor** | 5-fold stratified cross-validation, RandomizedSearchCV hyperparameter tuning, logistic regression baseline comparison |
| **Explainability** | SHAP TreeExplainer with human-readable output |
| **Vedic Compute** | Anurupyena Beejank Checksum (lightweight pre-filter sanity check) + Nikhilam Sutra (cultural demonstration of alternative multiplication algorithm for threshold calibration) |
| **Database** | PostgreSQL 15 + Redis 7 (production via docker-compose) — SQLite for local demo. Latency claims measured on SQLite; production latency may differ. |
| **Infrastructure** | Docker Compose (PostgreSQL + Redis + Backend + Frontend), Helm chart templates |

### Methodology — 7-Stage Pipeline

```
Transaction → Vedic Pre-Filter → Behavioral Feature Engine (9 indices + EWMA + Drift)
→ Nikhilam Threshold Calibration → Ensemble ML Inference
→ SHAP Explainability → Risk Score Output (GREEN / AMBER / RED)
```

1. **Ingest** — Transaction received via REST API
2. **Vedic Pre-Filter** — Anurupyena checksum as a lightweight sanity check; blocks structurally anomalous payloads (zero-coordinate injection) before ML compute
3. **Behavioral Feature Engine** — Computes 9 continuous behavioral indices (0–1 spectra) + EWMA deviation + behavioral drift against user's historical baseline
4. **Nikhilam Calibration** — Vedic near-base multiplication computes dynamic classification threshold adjusted by user risk profile (higher risk → lower threshold → more sensitive detection)
5. **Ensemble Inference** — XGBoost probability (50%) + Isolation Forest anomaly score (20%, percentile-calibrated) + Behavioral signals (30%) → combined score evaluated against Nikhilam-calibrated threshold
6. **SHAP Explanation** — Top contributing features translated into human-readable reasons with transaction-specific context
7. **Risk Decision** — SAFE (✅ Approve) / MONITOR (⚠️ Flag) / SUSPICIOUS (🟠 Hold) / FRAUD (🔴 Block) + immutable audit log

> **Note on CV Methodology**: 5-Fold cross-validation was performed on the training partition only. This is correct ML practice — the test set is held out as purely unseen future data to evaluate generalization.

---

## SLIDE 4 — USP & Key Features

### Unique Selling Points

1. **Only Cross-Track Solution** — Integrates PS 6 (Fraud Detection) + PS 21 (Vedic Checksum) + PS 18 (Vedic Compute) into a single coherent architecture
2. **Vedic Mathematics as Cultural Innovation** — Anurupyena Beejank checksum with HMAC-SHA256 backup provides two-layer integrity checking (Vedic first-gate + cryptographic second-gate). Nikhilam near-base multiplication showcases an elegant alternative algorithm from Indian mathematical heritage. These are presented as **algorithmic diversity** demonstrations.
3. **12-Dimensional Continuous Behavioral Intelligence** — 9 core indices (ADI, GRI, DTS, TRC, MRS, BFI, BDS, VRI, SGAS) plus EWMA deviation, behavioral drift, and **3 sequence-based features** (amount escalation, time-gap acceleration, category diversity) for genuine temporal pattern analysis across transaction history
4. **Full Explainability** — Every decision explained in plain language via SHAP (e.g., "Recipient has 67% involvement in prior flagged transactions"), meeting RBI compliance standards
5. **Trained on Real Data with ML Rigor** — Model trained on **590,540 real transactions** from IEEE-CIS Fraud Detection dataset (Kaggle) with 5-fold cross-validation, hyperparameter optimization, and baseline comparison
6. **Production-Ready Architecture** — 7 API routers, Docker Compose orchestration, Helm charts, audit logging, and compliance module demonstrate the ML model is embedded in a deployable, auditable system — not just a Jupyter notebook. Architecture supports regulatory compliance, real-time serving, and monitoring.

### Key Features

| Feature | What It Does |
|---|---|
| **Real-Time Fraud Scoring** | < 340ms end-to-end per transaction (local benchmark) |
| **Behavioral Fingerprinting** | 9 continuous indices + EWMA deviation + behavioral drift + 3 sequence-based features (escalation, acceleration, diversity) — genuine temporal behavior modeling |
| **Hybrid ML Ensemble** | XGBoost catches known patterns (50%); Isolation Forest catches novel anomalies (20%, percentile-calibrated); Behavioral signals (30%) |
| **SHAP Explainability** | Human-readable reasons with transaction-specific context for every flagged transaction |
| **Attack Simulation Lab** | Live demo: 3 attack scenarios detected and blocked in real time |
| **Audit & Compliance** | SHA-256 hashed tamper-proof logs, compliance PDF export, RBI-ready |
| **Vedic Compute Layer** | Anurupyena two-layer checksum (Beejank + HMAC-SHA256) + Nikhilam algorithmic diversity demonstration |
| **Analytics Dashboard** | Live gauge, fraud heatmap, confusion matrix, ROC curve, precision/recall charts |

### Performance Metrics (on IEEE-CIS Dataset — Full 590K)

| Metric | Result |
|---|---|
| Precision | **Improved** (F1-optimized threshold — see eval_report.json) |
| Recall | **≥50%** (balanced with precision via F1 optimization) |
| F1 Score | **Improved** (primary optimization target) |
| ROC-AUC | **89%+** |
| 5-Fold CV (on train partition) | See eval_report.json for exact figures |
| Prediction Latency (p95) | < 340ms (SQLite local benchmark) |
| Dataset | IEEE-CIS Fraud Detection (**590,540 real transactions**) |
| Split Method | Time-based (last 20% as test — purely future data) |
| Inference Features | Population medians from training set (not hardcoded zeros) |
| Baseline Comparison | XGBoost vs Logistic Regression comparison |

---

*VedFin Sentinel — Where Vedic Heritage Meets Modern Fraud Intelligence*
