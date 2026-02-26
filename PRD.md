# VedFin Sentinel — Product Requirements Document
**Enterprise & Government-Grade Behavioral Fraud Intelligence Platform**
`v1.0 | InnVedX Code Hackathon 2026 | BBD University, Lucknow`

---

| Field | Value |
|---|---|
| Hackathon | InnVedX Code Hackathon — BBD University, Lucknow |
| Problem Statement | PS 6 — FinTech Fraud Detection Using Behavioral Analysis |
| Section | Section A: Open Innovation \| Track 2: FinTech, Governance & Security |
| Vedic Integration | PS 21 (Checksum Validation) + PS 18 (Nikhilam Compute Engine) |
| Document Version | v1.0 — Initial Full PRD |
| Status | Ready for Development |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Vision & Core Objectives](#3-product-vision--core-objectives)
4. [System Architecture](#4-system-architecture)
5. [Vedic Mathematics Integration](#5-vedic-mathematics-integration)
6. [Behavioral Intelligence Engine](#6-behavioral-intelligence-engine)
7. [Core Product Modules](#7-core-product-modules)
8. [Database Design](#8-database-design)
9. [ML Model Strategy](#9-ml-model-strategy)
10. [Live Demo Narrative — The Heist & Catch](#10-live-demo-narrative--the-heist--catch)
11. [Competitive Landscape & Differentiation](#11-competitive-landscape--differentiation)
12. [API Specification](#12-api-specification-core-endpoints)
13. [Non-Functional Requirements](#13-non-functional-requirements)
14. [Risks & Mitigation](#14-risks--mitigation)
15. [Why VedFin Sentinel Wins](#15-why-vedfin-sentinel-wins)

---

## 1. Executive Summary

India processed over **131 billion UPI transactions in FY2024**. Even a 0.01% fraud rate translates to over **₹1,400 crore in annual losses**. Existing fraud prevention systems are largely rule-based, opaque, and unable to adapt to evolving attacker behavior in real time.

**VedFin Sentinel** is a real-time behavioral fraud intelligence platform built for banks, UPI payment systems, NBFCs, and government digital infrastructure. It combines a multi-index behavioral scoring engine with an ensemble ML core, an explainable AI layer, and — uniquely — a **Vedic Mathematics computational layer** for ultra-fast threshold calibration and pre-filter validation.

The result is a system that:
- Detects fraud in **under 340 milliseconds**
- Explains every decision in plain language for compliance
- Is architected for enterprise-grade government audit readiness

---

## 2. Problem Statement

### 2.1 The Scale of the Problem

Digital financial fraud in India is growing faster than the infrastructure designed to stop it. The challenge is not just detection — it is detection at scale, with explainability, and without disrupting legitimate transactions.

| Metric | Current Reality |
|---|---|
| UPI Transactions FY2024 | 131 Billion+ |
| Reported Financial Fraud (FY2024) | ₹14,000+ crore |
| Average Detection Lag (Rule-Based) | 4–6 hours post-transaction |
| False Positive Rate (Industry Avg) | 15–30% |
| Transactions with No Explainability | ~95% of flagged transactions |

### 2.2 Why Existing Systems Fail

- **Rule-based systems are static** — attackers learn and adapt within days of deployment
- **No behavioral baseline per user** — a ₹50,000 transaction flagged for one user is normal for another
- **Black-box ML models** are rejected by RBI compliance auditors due to lack of explainability
- **No real-time geo or device intelligence** — account takeovers go undetected for hours
- **Zero cross-domain fraud intelligence** — subsidy fraud, tax anomalies, and UPI fraud are handled in silos

### 2.3 Target Problem (PS 6 + PS 21 + PS 18)

VedFin Sentinel directly addresses **PS 6** (FinTech Fraud Detection Using Behavioral Analysis) as its primary problem statement, and integrates **PS 21** (Vedic Checksum & Validation System) and **PS 18** (Vedic Financial Compute Engine) as embedded architectural components — making it the **only cross-track solution** in this hackathon.

---

## 3. Product Vision & Core Objectives

VedFin Sentinel aims to become **India's behavioral fraud intelligence layer** — a platform that any UPI system, bank, or government financial infrastructure can plug into via API to get real-time, explainable, audit-ready fraud intelligence.

### 3.1 Core Objectives

- Real-time fraud probability scoring under 340ms per transaction
- 9-dimensional behavioral anomaly detection with per-user baselines
- Vedic Mathematics integration for pre-filter validation and threshold calibration
- Explainable AI (SHAP-based) for every flagged transaction
- Precision/Recall performance reporting with live dashboard
- Government audit-ready logging and compliance PDF export
- Enterprise-ready REST API with JWT authentication
- Attack simulation laboratory for testing and demonstration

### 3.2 Success Metrics

| KPI | Target |
|---|---|
| Fraud Detection Recall | > 92% |
| False Positive Rate | < 5% |
| End-to-End Prediction Latency | < 340ms |
| Vedic Pre-Filter Speed Gain | > 30% faster than standard baseline computation |
| SHAP Explanation Generation | < 50ms per transaction |
| System Uptime | 99.9% (Kubernetes-ready) |
| Compliance Report Export | < 3 seconds PDF generation |

---

## 4. System Architecture

### 4.1 High-Level Architecture Overview

The VedFin Sentinel pipeline is a **7-stage processing chain** from raw UPI transaction input to final risk score, audit log, and optional transaction freeze:

```
┌─────────────────────────────────────────────────────────────┐
│                  UPI Transaction Stream                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Stage 1: Transaction Ingestion                       │
│         FastAPI WebSocket / REST Endpoint                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│   Stage 2: Vedic Checksum Pre-Filter  ◄── NEW               │
│   Python — Anurupyena Sutra (Vedic Divisibility)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Stage 3: Behavioral Feature Engine                   │
│   ADI · GRI · DTS · TRC · MRS · BFI · BDS · VRI · SGAS     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│   Stage 4: Nikhilam Threshold Calibrator  ◄── NEW           │
│   Python — Nikhilam Sutra (Vedic Near-Base Subtraction)     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Stage 5: Ensemble ML Core                            │
│         XGBoost + Isolation Forest                           │
│         (Hybrid Sentinel Ensemble)                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Stage 6: SHAP Explainability Layer                   │
│         Human-readable fraud reasoning                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Stage 7: Risk Score Output                           │
│         GREEN / AMBER / RED + Audit Log + API Response       │
└─────────────────────────────────────────────────────────────┘
```

| Stage | Component | Technology |
|---|---|---|
| 1 | UPI Transaction Ingestion | FastAPI WebSocket / REST Endpoint |
| 2 | Vedic Checksum Pre-Filter | Python — Anurupyena Sutra (Vedic Divisibility) |
| 3 | Behavioral Feature Engine | Python — 9 Custom Behavioral Indices |
| 4 | Nikhilam Threshold Calibrator | Python — Nikhilam Sutra (Vedic Near-Base Subtraction) |
| 5 | Ensemble ML Core | XGBoost + Isolation Forest (Hybrid Sentinel Ensemble) |
| 6 | Explainability Layer | SHAP (SHapley Additive Explanations) |
| 7 | Risk Scoring & Output | Green / Amber / Red + Audit Log + API Response |

### 4.2 Frontend Architecture

| Component | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Styling | TailwindCSS + Custom Design System |
| Charts & Viz | Recharts + D3.js (Fraud Heatmaps) |
| Animations | Framer Motion (Gauge, Risk Transitions) |
| Theme | Dark FinTech — Glassmorphism cards, Risk color coding |
| State Management | Zustand |
| API Client | Axios + React Query |

### 4.3 Backend Architecture

| Component | Technology |
|---|---|
| Framework | FastAPI (Python 3.11) |
| Auth | JWT (JSON Web Tokens) + API Key rotation |
| Rate Limiting | SlowAPI middleware |
| API Docs | Swagger UI (auto-generated) |
| Async Processing | asyncio + background task queue |
| Caching | Redis (real-time inference optimization) |
| PDF Export | WeasyPrint / ReportLab |

### 4.4 ML & Data Architecture

| Component | Technology |
|---|---|
| Supervised Model | XGBoost Classifier (labeled transaction fraud dataset) |
| Unsupervised Model | Isolation Forest (anomaly detection, no labels required) |
| Ensemble Strategy | Weighted probability averaging — Hybrid Sentinel Ensemble |
| Calibration | Nikhilam Sutra near-base threshold computation |
| Explainability | SHAP TreeExplainer (fast, tree-model optimized) |
| Dataset | Synthetic + Kaggle Credit Card Fraud + IEEE-CIS Fraud |
| Feature Count | 9 behavioral indices + 12 transaction metadata features |

### 4.5 Infrastructure

| Component | Technology |
|---|---|
| Containerization | Docker (all services containerized) |
| Orchestration | Kubernetes-ready (Helm charts defined) |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Deployment Target | Any cloud (AWS / GCP / Azure) or on-premise |
| CI/CD | GitHub Actions |

---

## 5. Vedic Mathematics Integration (Unique Differentiator)

VedFin Sentinel is the **only fraud detection system** that integrates Vedic computational sutras as active processing layers — not as decoration, but as functional speed optimizations that can be benchmarked against standard approaches.

### 5.1 Module 1 — Vedic Checksum Pre-Filter

| Field | Value |
|---|---|
| Vedic Sutra | Anurupyena (Proportionality Principle) + Vedic Divisibility Rules |
| PS Covered | PS 21 — Vedic Checksum & Validation System |
| Position in Pipeline | Stage 2 — before any ML inference |
| Purpose | Pre-validate every incoming transaction before it enters the ML pipeline |

**How it works:** Every transaction carries metadata fields (amount, account number, merchant ID, timestamp). The Vedic Checksum Pre-Filter applies digit-sum based divisibility rules (derived from Vedic number theory) to detect structurally anomalous or tampered transaction metadata — corrupted payloads, replayed transactions, or synthetic injection attacks — before they consume expensive ML compute.

**Performance benefit:** Pre-filtering structurally invalid transactions at this stage reduces the ML inference load by an estimated 8–15%, directly improving system throughput under high transaction volume.

### 5.2 Module 2 — Nikhilam Threshold Calibrator

| Field | Value |
|---|---|
| Vedic Sutra | Nikhilam Navatashcaramam Dashatah (All from 9, Last from 10) |
| PS Covered | PS 18 — Vedic Financial Compute Engine |
| Position in Pipeline | Stage 4 — between Behavioral Feature Engine and ML Core |
| Purpose | Fast computation of per-user fraud threshold baselines |

**How it works:** Each user has a behavioral baseline — their typical transaction amount, frequency, and location patterns. Computing the deviation from this baseline traditionally uses standard deviation calculations. The Nikhilam Sutra enables near-base subtraction for numbers close to powers of 10 (e.g., 98, 997, 10003), which covers a large portion of typical transaction amounts (₹100, ₹500, ₹1000, ₹10000).

This allows the threshold calibration step to be computed significantly faster for in-base amounts, with a measurable benchmark comparison shown in the analytics dashboard as proof of concept.

---

## 6. Behavioral Intelligence Engine

The behavioral engine computes **9 indices** per transaction. Each index captures a distinct dimension of behavioral deviation from the user's established baseline. Together they form the feature vector fed into the Hybrid Sentinel Ensemble.

| Index | Full Name | What It Detects | Alert Condition |
|---|---|---|---|
| ADI | Amount Deviation Index | Transaction amount vs user's historical average and std dev | Amount > 3σ from baseline |
| GRI | Geo-Shift Risk Index | Geographic distance from user's typical transaction locations | New city/country in < 2hrs |
| DTS | Device Trust Score | Transaction from known vs unknown device fingerprint | New device, no prior history |
| TRC | Time Risk Coefficient | Transaction time vs user's historical active hours | 3AM for a 9AM–9PM user |
| MRS | Merchant Risk Score | Merchant category risk combined with user's history with merchant | First-time high-risk merchant |
| BFI | Burst Frequency Index | Number of transactions in short rolling time windows | > 5 txns in 60 seconds |
| BDS | Behavioral Drift Score | Long-term drift in overall behavioral pattern over 30 days | Sudden baseline shift |
| VRI | Velocity Reversal Index | Rapid send-and-reverse patterns (money mule indicator) | Reversal within 10 minutes |
| SGAS | Social Graph Anomaly Score | Transaction to accounts with zero prior interaction history | First-ever interaction, high amount |

### 6.1 Ensemble Fraud Score Computation

Each index produces a normalized score between 0 and 1. These 9 scores, combined with 12 transaction metadata features (amount, category, timestamp, device OS, IP subnet, etc.), form a **21-dimensional feature vector**.

The Hybrid Sentinel Ensemble combines XGBoost's supervised fraud probability with Isolation Forest's unsupervised anomaly score using a weighted average calibrated by the Nikhilam Threshold Calibrator. The final score maps to:

| Risk Band | Score Range | Action | Display Color |
|---|---|---|---|
| SAFE | 0.00 – 0.35 | Transaction approved, logged normally | 🟢 Green |
| MONITOR | 0.36 – 0.65 | Transaction approved, flagged for review queue | 🟡 Amber |
| SUSPICIOUS | 0.66 – 0.85 | Transaction held, user notified for confirmation | 🟠 Orange |
| FRAUD | 0.86 – 1.00 | Transaction blocked, freeze triggered, audit log created | 🔴 Red |

---

## 7. Core Product Modules

### 7.1 Real-Time Fraud Intelligence API

- `POST /predict` — single transaction scoring, < 340ms response
- `POST /bulk_predict` — batch scoring for end-of-day reconciliation
- `GET /user/{id}/baseline` — retrieve user's behavioral baseline stats
- `POST /simulate/attack` — trigger predefined attack scenarios
- `GET /audit/export` — generate compliance PDF for a date range
- `GET /metrics` — live precision, recall, F1, ROC-AUC stats
- All endpoints: JWT authentication, rate limiting, Swagger docs

### 7.2 Analytics Dashboard

- Live fraud score gauge — animated, color-coded Green/Amber/Red
- Real-time transaction feed with per-row risk badges
- Fraud rate over time — line chart (hourly, daily, weekly)
- Confusion matrix visualization — TP, FP, TN, FN breakdown
- ROC curve — interactive AUC visualization
- Precision-Recall tradeoff curve
- Fraud heatmap — geographic distribution of flagged transactions
- User behavioral timeline — per-user index history
- Vedic compute benchmark panel — Nikhilam vs standard computation speed

### 7.3 Explainable AI Layer

- SHAP TreeExplainer for XGBoost model
- Per-transaction feature attribution — which indices triggered the alert
- Human-readable fraud reason generation (e.g., *"Transaction flagged: new device + geo-shift of 1,200km in 45 minutes + burst of 7 transactions in 2 minutes"*)
- Audit-ready explanation JSON stored per transaction
- Compliance-safe: explanations meet RBI's Model Risk Management guidelines

### 7.4 Attack Simulation Laboratory

- **Scenario 1: Geo-Spoofing Attack** — simulate login from new country, transactions from VPN
- **Scenario 2: Burst Micro-Transaction Attack** — 50 transactions under ₹999 in 3 minutes (below typical alert threshold)
- **Scenario 3: Account Takeover** — new device, new geo, unknown recipients, high-value transfers
- Each simulation shows real-time index scores, SHAP explanations, and risk band progression
- Used as the primary live demo mechanism during jury presentation

### 7.5 Government & Compliance Module

- Subsidy fraud detection mode — flag anomalous subsidy claim patterns
- Tax anomaly detection mode — flag unusual income/expense behavioral patterns
- Tamper-proof audit trail — all logs hashed and write-once
- Compliance report export — PDF with transaction list, risk scores, SHAP explanations, and Vedic checksum validation log
- RBI-compliant model documentation (Model Risk Management framework)

---

## 8. Database Design

### 8.1 Users Table

| Field | Type | Description |
|---|---|---|
| user_id | UUID PRIMARY KEY | Unique user identifier |
| risk_profile | ENUM (LOW/MED/HIGH) | Current assigned risk tier |
| baseline_stats | JSONB | 9-index behavioral baseline (mean, std dev per index) |
| account_age_days | INTEGER | Days since account creation |
| trusted_devices | TEXT[] | Array of verified device fingerprints |
| trusted_locations | JSONB | Array of lat/long clusters for known locations |
| avg_transaction_amount | DECIMAL | Rolling 90-day average transaction amount |
| created_at | TIMESTAMP | Account creation timestamp |
| last_updated | TIMESTAMP | Last baseline recalculation timestamp |

### 8.2 Transactions Table

| Field | Type | Description |
|---|---|---|
| txn_id | UUID PRIMARY KEY | Unique transaction identifier |
| user_id | UUID FK → users | Transacting user |
| amount | DECIMAL(12,2) | Transaction amount in INR |
| txn_timestamp | TIMESTAMP WITH TZ | Transaction initiation time |
| geo_lat | DECIMAL(9,6) | Latitude of transaction origin |
| geo_lng | DECIMAL(9,6) | Longitude of transaction origin |
| device_id | VARCHAR(256) | Hashed device fingerprint |
| device_os | VARCHAR(64) | Operating system |
| ip_subnet | VARCHAR(45) | /24 subnet of originating IP |
| merchant_category | VARCHAR(64) | MCC code + category label |
| merchant_id | VARCHAR(128) | Merchant identifier |
| recipient_id | UUID | Recipient account identifier |
| fraud_label | BOOLEAN | Ground truth (null for unseen transactions) |
| vedic_checksum | VARCHAR(64) | Anurupyena checksum result |
| vedic_valid | BOOLEAN | Whether transaction passed Vedic pre-filter |

### 8.3 Risk Audit Log Table

| Field | Type | Description |
|---|---|---|
| log_id | UUID PRIMARY KEY | Unique audit log entry |
| txn_id | UUID FK → transactions | Associated transaction |
| fraud_score | DECIMAL(4,3) | Final ensemble fraud probability (0.000–1.000) |
| risk_band | ENUM | SAFE / MONITOR / SUSPICIOUS / FRAUD |
| index_scores | JSONB | All 9 behavioral index scores |
| shap_explanation | JSONB | Full SHAP feature attributions |
| human_explanation | TEXT | Auto-generated human-readable reason |
| nikhilam_threshold | DECIMAL | Computed threshold value (Vedic) |
| action_taken | VARCHAR(64) | approved / held / blocked / frozen |
| reviewer_status | ENUM | pending / reviewed / escalated / cleared |
| log_hash | VARCHAR(256) | SHA-256 hash of log entry (tamper-proof) |
| created_at | TIMESTAMP WITH TZ | Log creation timestamp |

---

## 9. ML Model Strategy

### 9.1 Why This Model Combination

Fraud detection requires handling two fundamentally different scenarios: known fraud patterns (supervised) and novel, never-before-seen attack vectors (unsupervised). Using either model alone leaves critical gaps.

| Model | Type | Role | Why It's Here |
|---|---|---|---|
| XGBoost | Supervised | Primary fraud probability scorer | Best-in-class performance on tabular financial data; handles class imbalance with scale_pos_weight |
| Isolation Forest | Unsupervised | Anomaly detector for novel attacks | Detects out-of-distribution transactions with no labels — catches zero-day fraud patterns |
| Hybrid Sentinel Ensemble | Combined | Final risk score | Weighted average of both; Nikhilam calibrator adjusts weights per user risk tier |

### 9.2 Why Recall Over Precision

This is a **deliberate and documented design choice**. Missing a fraudulent transaction (False Negative) costs the bank and victim an average of ₹42,000 in direct losses plus regulatory penalties. Incorrectly flagging a legitimate transaction (False Positive) inconveniences the user for 2–5 minutes while the hold is reviewed.

> **Therefore: we optimize for Recall (minimize False Negatives) while maintaining False Positive Rate below 5% through the Isolation Forest's calibrated anomaly threshold.**

### 9.3 Evaluation Metrics Reported

- **Accuracy** — overall correctness
- **Precision** — of all flagged transactions, how many are actually fraud
- **Recall** — of all actual fraud, how many did we catch *(PRIMARY METRIC)*
- **F1 Score** — harmonic mean of Precision and Recall
- **ROC-AUC** — area under the receiver operating characteristic curve
- **False Positive Rate** — proportion of legitimate transactions incorrectly flagged
- **Confusion Matrix** — TP, FP, TN, FN with visualization
- **Vedic Pre-Filter Throughput** — transactions filtered per second vs standard approach

---

## 10. Live Demo Narrative — The Heist & Catch

The jury presentation follows a **cinematic narrative structure**. Every feature of VedFin Sentinel is introduced through the story of a real attack being executed and caught in real time.

| Step | Narrative Beat | System Action Shown |
|---|---|---|
| 1 | India's UPI Fraud Reality — ₹14,000 crore in FY2024 | Opening statistics dashboard |
| 2 | Meet Rahul — Established UPI User | User behavioral timeline — normal baseline shown |
| 3 | Attacker compromises Rahul's credentials at 2:47 AM | New device fingerprint detected (DTS → 0.94) |
| 4 | Attacker initiates transfer from Bengaluru — Rahul is in Delhi | GRI spikes to 0.91 (1,847km geo-shift in 40 minutes) |
| 5 | 7 burst transactions fired in 90 seconds under ₹999 each | BFI hits 0.97, Vedic checksum flags pattern anomaly |
| 6 | 8th transaction: ₹49,500 to unknown recipient | SGAS: 0.99 (zero prior interaction), VRI triggers |
| 7 | Ensemble score: 0.94 — FRAUD band triggered | Red gauge animation, transaction blocked in 285ms |
| 8 | SHAP explanation generated | Human-readable explanation displayed |
| 9 | Compliance report auto-exported | PDF generation shown — RBI-ready audit trail |
| 10 | The Punchline | *"Traditional systems: 4 hours. VedFin Sentinel: 285 milliseconds."* |

---

## 11. Competitive Landscape & Differentiation

| Feature | Razorpay Shield | BankBazaar | Generic ML Model | VedFin Sentinel |
|---|---|---|---|---|
| Real-time Behavioral Scoring | Partial | No | No | ✅ Yes — 9 indices |
| Explainable AI (SHAP) | No | No | No | ✅ Yes — per transaction |
| Vedic Compute Layer | No | No | No | ✅ Yes — unique |
| Attack Simulation Lab | No | No | No | ✅ Yes — 3 scenarios |
| Government Audit Ready | Partial | No | No | ✅ Yes — full trail |
| Unsupervised Anomaly Detection | No | Partial | Varies | ✅ Yes — Isolation Forest |
| Open REST API | Proprietary | No | No | ✅ Yes — JWT + Swagger |
| Recall Optimized | Unknown | Unknown | Varies | ✅ Yes — documented |
| Cross-track (PS 6 + 21 + 18) | N/A | N/A | N/A | ✅ Yes — unique |

---

## 12. API Specification (Core Endpoints)

### POST /predict
Single transaction real-time fraud scoring.

| Field | Value |
|---|---|
| Auth | Bearer JWT token |
| Request Body | `{ user_id, amount, timestamp, geo_lat, geo_lng, device_id, merchant_category, recipient_id }` |
| Response | `{ txn_id, fraud_score, risk_band, index_scores, shap_explanation, human_explanation, action_taken, latency_ms }` |
| SLA | < 340ms p95 |

### POST /bulk_predict
Batch scoring for historical or reconciliation analysis.

| Field | Value |
|---|---|
| Auth | Bearer JWT token |
| Request Body | Array of transaction objects (max 10,000 per request) |
| Response | Array of scoring results + aggregate precision/recall stats |
| SLA | < 5 seconds for 1,000 transactions |

### POST /simulate/attack
Trigger a predefined attack simulation scenario.

| Field | Value |
|---|---|
| Auth | Bearer JWT token |
| Request Body | `{ scenario: 'geo_spoofing' \| 'burst_micro' \| 'account_takeover', target_user_id }` |
| Response | Real-time stream of scoring events as attack unfolds |
| Use | Demo and testing purposes only |

### GET /audit/export
Generate a compliance PDF report for a date range.

| Field | Value |
|---|---|
| Auth | Bearer JWT token |
| Query Params | start_date, end_date, user_id (optional), risk_band (optional) |
| Response | Binary PDF stream — RBI-compliant format |
| SLA | < 3 seconds |

---

## 13. Non-Functional Requirements

| Category | Requirement | Target |
|---|---|---|
| Performance | Single transaction scoring latency | < 340ms p95 |
| Performance | Batch throughput | > 1,000 txns/second |
| Reliability | System availability | 99.9% uptime |
| Security | All API communications | HTTPS + JWT auth + rate limiting |
| Security | Audit logs | SHA-256 hashed, write-once, tamper-proof |
| Scalability | Horizontal scaling | Kubernetes-ready, stateless services |
| Compliance | Explainability standard | RBI Model Risk Management guideline compatible |
| Compliance | Data retention | Audit logs retained minimum 7 years |
| Observability | Logging | Structured JSON logs, OpenTelemetry compatible |
| Portability | Deployment | Any cloud or on-premise via Docker Compose |

---

## 14. Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Insufficient labeled fraud data | Medium | High | Use Kaggle IEEE-CIS + synthetic data generation via SMOTE for class balancing |
| High false positive rate disrupting UX | Medium | High | Isolation Forest anomaly threshold tuning + human-in-loop review queue for MONITOR band |
| Attacker adaptation to model | High | Medium | Isolation Forest handles novel patterns; model retraining pipeline defined |
| Vedic compute benchmark inconclusive | Low | Medium | Benchmark scoped to specific near-base transaction amounts where Nikhilam advantage is provable |
| API latency spikes under load | Low | High | Redis caching of user baselines; async FastAPI; Kubernetes horizontal pod autoscaling |
| SHAP generation adding latency | Medium | Medium | Pre-compute SHAP for cached baselines; async explanation generation post-response |

---

## 15. Why VedFin Sentinel Wins

VedFin Sentinel is not a fraud detection project. It is a **behavioral intelligence infrastructure platform** with the following properties that no other hackathon submission in this event will have simultaneously:

1. **The only solution covering three problem statements** (PS 6, PS 21, PS 18) in a single coherent architecture
2. **The only fraud detection system with Vedic Mathematics as a functional, benchmarked computational layer** — not decoration
3. **A 9-dimensional behavioral engine** with two newly defined indices (VRI, SGAS) that address money mule networks and social graph attacks — emerging fraud vectors not covered by existing systems
4. **Full explainability via SHAP** — the only approach that survives RBI Model Risk Management scrutiny
5. **A live Attack Simulation Laboratory** — no other team will demo a live attack being executed and caught in real time
6. **Enterprise-grade architecture**: PostgreSQL, Redis, FastAPI, Next.js, Docker, Kubernetes-ready
7. **A cinematic demo narrative** that judges will remember hours after the presentation ends

> **This is not a student project. This is what ₹14,000 crore in annual fraud loss demands.**

---

## ❌ What VedFin Sentinel Does NOT Do (Out of Scope)

> This section exists to prevent scope creep, implementation confusion, and AI agent hallucination. Read before building anything.

- ❌ **No user self-registration** — accounts are admin-provisioned only. No signup flow.
- ❌ **No payment processing** — this is a detection platform. No Stripe, Razorpay, or UPI SDK.
- ❌ **No chatbot or conversational UI** — dashboard only. No LLM chat interface in the product.
- ❌ **No email or SMS notifications** — alerts surface in the dashboard UI only.
- ❌ **No multi-tenancy** — single-tenant only. No org_id or tenant_id in any table.
- ❌ **No mobile app** — web-responsive Next.js only.
- ❌ **No custom cryptography** — use python-jose, passlib, hashlib. No custom crypto implementations.
- ❌ **No third-party analytics** — no Google Analytics, Mixpanel, or tracking pixels in frontend.
- ❌ **No external API calls inside /predict** — scoring pipeline is fully self-contained.
- ❌ **No SQLite** — PostgreSQL 15 always. Not even for development.
- ❌ **No real UPI integration** — all transactions are ingested via our own REST API. No direct UPI hook.
- ❌ **No blockchain** — audit log tamper-proofing is via SHA-256 hashing in PostgreSQL. Not a blockchain.
- ❌ **No model retraining via API** — model training is offline only. No /retrain endpoint.
- ❌ **No dark patterns** — no auto-subscriptions, no hidden charges, no data selling features.

---

*VedFin Sentinel | PRD v1.0 | InnVedX Code Hackathon 2026 | BBD University*
*Where Vedic Intelligence Meets Modern Fraud*
