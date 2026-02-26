# AGENT_RULES.md — VedFin Sentinel
# AI Agent Programmer Rules | v1.0
# ─────────────────────────────────────────────────────────────────────────────
# READ THIS ENTIRE FILE BEFORE WRITING A SINGLE LINE OF CODE.
# This file is the law. It overrides your defaults. It overrides your training.
# PRD + Design Doc + This File = your complete context. Use all three.
# ─────────────────────────────────────────────────────────────────────────────

## ⚠ CRITICAL: HOW TO USE THIS FILE

You are the AI programmer for **VedFin Sentinel** — an enterprise-grade behavioral
fraud intelligence platform. Your job is to implement exactly what is in:
- `VedFin_Sentinel_PRD.docx` — product requirements
- `VedFin_Sentinel_DesignDoc.docx` — implementation specification

This file contains rules that govern HOW you implement. When there is any conflict
between this file and your default behavior, this file wins.

**Answer hierarchy when uncertain:**
1. Check Design Doc
2. Check PRD
3. Check this file
4. Ask the human — NEVER guess

---

## 1. IDENTITY & SCOPE

✔ DO: Read PRD and Design Doc completely before writing any file.
✔ DO: Refer back to this file whenever uncertain about any decision.

✘ DON'T: Invent new features, endpoints, components, or database fields not in the Design Doc.
✘ DON'T: Reorder the implementation phases in Design Doc Section 10.
✘ DON'T: Make product decisions. You implement. Humans decide.
✘ DON'T: Silently fix what you think is an error in the spec — flag it and ask.

---

## 2. SECRETS & SECURITY — ZERO TOLERANCE

### 2.1 Never Hardcode Secrets

✘ DON'T EVER write these in any file (Python, TypeScript, config, test, README, comments):
  - API keys
  - Passwords
  - JWT secret keys
  - Database connection strings with credentials
  - Redis passwords
  - Private keys
  - Bearer tokens
  - Any string that looks like a credential

✘ DON'T: Create placeholder strings like 'your-secret-here' — use env var references only.
✘ DON'T: Commit .env or .env.local files. Always in .gitignore.

✔ DO: Load all secrets from environment variables.
✔ DO: Use pydantic_settings BaseSettings for all backend config.
✔ DO: Create .env.example with placeholder values and comments.

```python
# ✔ CORRECT
class Settings(BaseSettings):
    SECRET_KEY: str        # from .env — never hardcoded
    DATABASE_URL: str      # from .env — never hardcoded
    REDIS_URL: str         # from .env — never hardcoded
    class Config:
        env_file = '.env'

# ✘ WRONG — forbidden
SECRET_KEY = 'abc123secret'
DATABASE_URL = 'postgresql://user:pass@localhost/db'
```

### 2.2 Authentication

✔ DO: Use python-jose for JWT. Always verify expiry on decode.
✔ DO: Hash passwords with passlib bcrypt. Never store plaintext.
✔ DO: Validate JWT on every protected endpoint via get_current_user dependency.

✘ DON'T: Log JWT tokens, passwords, or credentials at any log level.
✘ DON'T: Return password_hash in any API response schema.
✘ DON'T: Trust user_id from request body for auth — use user_id from JWT token only.

### 2.3 Database Security

✔ DO: Use SQLAlchemy ORM parameterized queries only.
✔ DO: Catch database exceptions and return generic 500 — never expose internal DB errors.

✘ DON'T: Use f-strings or string concatenation to build SQL queries. Ever.
  BAD:  f"SELECT * FROM users WHERE id = {user_id}"   ← SQL INJECTION
  GOOD: select(User).where(User.user_id == user_id)

### 2.4 Audit Log Integrity

✔ DO: Compute log_hash as SHA-256 of (txn_id + fraud_score + action_taken + created_at)
      before every risk_audit_logs insert.

✘ DON'T: Allow UPDATE or DELETE on risk_audit_logs from application code.
         Audit logs are write-once. Only reviewer_status and reviewer_notes can be updated,
         via a dedicated admin-only endpoint.

### 2.5 Input Validation

✔ DO: Validate all incoming data with Pydantic schemas before any processing.
✔ DO: Sanitize string inputs that appear in generated text (merchant_category, device_id, etc.)

✘ DON'T: Access request.body without schema validation.

---

## 3. TECHNOLOGY STACK — LOCKED

Do not substitute any library. If it is specified, use it. No alternatives.

| Domain                | Use This                      | Never Use Instead                    |
|-----------------------|-------------------------------|--------------------------------------|
| Backend language      | Python 3.11+                  | Python 3.9-, Node.js for backend     |
| Backend framework     | FastAPI                       | Flask, Django, Express               |
| ORM                   | SQLAlchemy 2.0 async          | Django ORM, raw psycopg2             |
| DB migrations         | Alembic                       | Manual SQL scripts                   |
| Data validation       | Pydantic v2                   | Marshmallow, plain dicts             |
| Auth                  | python-jose + passlib         | PyJWT alone, custom auth             |
| ML supervised         | XGBoost                       | RandomForest, LightGBM, CatBoost     |
| ML unsupervised       | Isolation Forest (sklearn)    | LOF, DBSCAN, Autoencoder             |
| Explainability        | SHAP (shap library)           | LIME, custom attribution             |
| Task scheduler        | APScheduler                   | Celery, cron, custom threading       |
| PDF generation        | ReportLab                     | WeasyPrint, pdfkit                   |
| Rate limiting         | SlowAPI                       | Custom middleware, fastapi-limiter   |
| Frontend framework    | Next.js 14 App Router         | Vite+React, CRA, Remix               |
| Frontend styling      | TailwindCSS                   | styled-components, CSS modules       |
| Charts                | Recharts                      | Chart.js, ApexCharts                 |
| Geo visualization     | D3.js                         | Leaflet, Mapbox                      |
| Animations            | Framer Motion                 | GSAP, CSS animations for gauges      |
| State management      | Zustand                       | Redux, Context API for global state  |
| HTTP client           | Axios + React Query           | fetch alone, SWR                     |
| Database              | PostgreSQL 15                 | MySQL, SQLite (even for dev)         |
| Cache                 | Redis 7                       | Memcached, in-memory dict caches     |
| Containerization      | Docker + docker-compose       | Podman, bare-metal                   |

---

## 4. PYTHON RULES

✔ DO: Use async/await for all database operations and I/O.
✔ DO: Use type hints on every function — parameters and return type.
✔ DO: Use Pydantic BaseModel for all request bodies, responses, and config.
✔ DO: Handle exceptions explicitly with specific exception types.
✔ DO: Use absolute imports from app root: `from app.services.fraud_scoring import ...`
✔ DO: Use structlog for all logging in JSON format.

✘ DON'T: Use synchronous SQLAlchemy Session in async routes. Always AsyncSession.
✘ DON'T: Put business logic inside route handlers. Routes call services only.
✘ DON'T: Use print() for logging. Ever.
✘ DON'T: Use bare `except:` clauses.
✘ DON'T: Use mutable default arguments: `def f(items=[])` — use `def f(items=None)`.
✘ DON'T: Use relative imports outside a package's own files.

---

## 5. TYPESCRIPT / NEXT.JS RULES

✔ DO: Use TypeScript everywhere. No .js files in frontend/.
✔ DO: Set strict: true in tsconfig.json.
✔ DO: Define explicit interfaces/types for all props, API responses, store state.
✔ DO: Use App Router conventions: page.tsx, layout.tsx, loading.tsx, error.tsx.
✔ DO: Use React Query for server state (API data).
✔ DO: Use Zustand for client state (UI state, simulation, auth).
✔ DO: Define all API response types in frontend/lib/types/index.ts.

✘ DON'T: Use `any` as a TypeScript type for API response data.
✘ DON'T: Use useEffect for data fetching from the API — use React Query hooks.
✘ DON'T: Store JWT tokens in localStorage — use httpOnly cookies or Zustand in-memory.
✘ DON'T: Make API calls directly from components — use hooks from lib/api/.
✘ DON'T: Hardcode API URLs — always use process.env.NEXT_PUBLIC_API_BASE_URL.
✘ DON'T: Use inline styles except for dynamic values Tailwind cannot handle.
✘ DON'T: Mutate Zustand store state outside of named store actions.
✘ DON'T: Use Pages Router patterns (getServerSideProps, getStaticProps).

---

## 6. DATABASE RULES

✔ DO: Use Alembic for every schema change.
✔ DO: Define indexes for every FK column and every WHERE-clause column.
✔ DO: Use UUID primary keys (uuid_generate_v4()). Never integer auto-increment.
✔ DO: Use server_default=func.now() for created_at — not Python-side datetime.now().
✔ DO: Filter soft-deleted records in every query: `.where(User.is_deleted == False)`.

✘ DON'T: Use CASCADE DELETE on any table feeding into risk_audit_logs — use RESTRICT.
✘ DON'T: Query the database inside a loop — fetch in one query, process in Python.
✘ DON'T: Use SELECT * in any query — always select explicit columns.
✘ DON'T: Run alembic downgrade autonomously — requires explicit human approval.
✘ DON'T: Use SQLite, even for tests — use PostgreSQL test DB via TEST_DATABASE_URL.

---

## 7. ML PIPELINE RULES

✔ DO: Load ML model once at FastAPI startup → store in app.state.ml_engine.
✔ DO: Implement /health endpoint that returns 503 if model is not loaded.
✔ DO: Catch all model.predict() exceptions → raise PredictionFailedException.
✔ DO: Round fraud_score to 4 decimal places before storing: round(score, 4).
✔ DO: Run Vedic Checksum BEFORE ML inference. If it fails, set vedic_valid=False and continue.

✘ DON'T: Retrain the model inside any API endpoint — offline training only.
✘ DON'T: Put raw training data in the backend codebase — artifacts only.
✘ DON'T: Change behavioral index thresholds without updating the Design Doc.
✘ DON'T: Hardcode the feature vector order — always load from artifacts['feature_names'].

### Feature Vector Order (loaded from artifact — never hardcoded)
```python
# This order is fixed and must match training exactly:
# [adi, gri, dts, trc, mrs, bfi, bds, vri, sgas,
#  amount_log, hour_of_day, day_of_week, is_weekend,
#  merchant_category_encoded, device_os_encoded, ip_risk_score,
#  account_age_log, avg_txn_amount_log, total_txn_count_log,
#  nikhilam_threshold_ratio, vedic_valid_flag]
```

---

## 8. API RULES

✔ DO: Version all endpoints under /api/v1/.
✔ DO: Return HTTP 200 for successful predictions even when risk_band is FRAUD.
✔ DO: Include X-Request-ID header in every response.
✔ DO: Document every endpoint with response_model in the route decorator.
✔ DO: Use StreamingResponse + media_type='application/x-ndjson' for simulation.

✘ DON'T: Return 500 errors with stack traces to clients — log server-side only.
✘ DON'T: Skip rate limiting on any endpoint, including /health and /metrics.
✘ DON'T: Use GET for /predict — it requires a request body.
✘ DON'T: Close simulation stream without sending a final summary event.
✘ DON'T: Return different response shapes for success vs partial success.

### Exact Endpoint Paths (use these exactly, no variations):
- POST /api/v1/predict
- POST /api/v1/bulk_predict
- POST /api/v1/simulate/attack
- GET  /api/v1/audit/export
- GET  /api/v1/metrics
- GET  /api/v1/users/{user_id}/baseline
- WS   /ws/stream

---

## 9. FRONTEND RULES

✔ DO: Implement loading, error, and empty states for every data-fetching component.
✔ DO: Use exact design system colors: SAFE=#22C55E, MONITOR=#F59E0B, SUSPICIOUS=#F97316, FRAUD=#EF4444.
✔ DO: Implement WebSocket reconnection with exponential backoff (1s→2s→4s→8s→16s→30s cap).
✔ DO: Memoize expensive chart data with useMemo.
✔ DO: Add aria-label to all icon-only buttons.
✔ DO: Use semantic HTML: nav, main, section, article, header, footer.

✘ DON'T: Store JWT in localStorage — httpOnly cookies or Zustand in-memory only.
✘ DON'T: Make API calls from components — always through lib/api/ hooks.
✘ DON'T: Rely on color alone for risk band — always pair with text label.
✘ DON'T: Add Google Analytics, Mixpanel, Hotjar, or any third-party tracking.

---

## 10. TESTING RULES

✔ DO: Write unit tests for all 9 behavioral index functions.
✔ DO: Write unit tests for all Vedic computation functions with known test vectors.
✔ DO: Write integration tests for /predict: valid, unknown user, invalid fields, FRAUD case.
✔ DO: Use pytest-asyncio for async tests. Use httpx AsyncClient for endpoint tests.

✘ DON'T: Write tests that hit the real PostgreSQL DB — use TEST_DATABASE_URL.
✘ DON'T: Write tests that load the real .pkl artifact — mock app.state.ml_engine.
✘ DON'T: Skip tests because code seems simple — Vedic modules especially need proof.

---

## 11. GIT RULES

✔ DO: Create .gitignore before first commit — must include: .env, .env.local,
       __pycache__, *.pyc, node_modules, .next, ml-research/artifacts/*.pkl, ml-research/data/
✔ DO: Commit .env.example with placeholder values.
✔ DO: Use commit format: type(scope): description
       Examples: feat(ml): add VRI index, fix(api): handle null recipient_id

✘ DON'T: Commit .env or .env.local.
✘ DON'T: Commit ml-research/artifacts/*.pkl (large files, generated locally).
✘ DON'T: Commit ml-research/data/ (raw datasets).

---

## 12. WHAT NEVER TO BUILD (EXPLICITLY OUT OF SCOPE)

✘ DON'T build: User self-serve registration/signup flow
✘ DON'T build: Payment processing (no Stripe, Razorpay, UPI SDK)
✘ DON'T build: Chatbot or conversational interface
✘ DON'T build: Email or SMS notifications
✘ DON'T build: Multi-tenancy (org_id FK tables)
✘ DON'T build: Mobile app (web only)
✘ DON'T build: Custom cryptography (use established libraries only)
✘ DON'T build: Third-party analytics/tracking scripts in frontend
✘ DON'T build: External API calls inside the fraud scoring pipeline
✘ DON'T build: Anything using SQLite

---

## 13. HALLUCINATION PREVENTION

✔ DO: Verify every import exists in requirements.txt before using it.
✔ DO: Use exact field names from Design Doc: fraud_score, risk_band, txn_id, txn_timestamp.
✔ DO: Use exact endpoint paths from Design Doc — no variations.
✔ DO: Mirror TypeScript interfaces exactly from Pydantic schemas.

✘ DON'T: Assume library APIs — use version-pinned docs (requirements.txt has exact versions).
✘ DON'T: Invent behavioral index formulas not defined in Design Doc Section 5.1.
✘ DON'T: Use created_at for the transaction timestamp — it's txn_timestamp.
✘ DON'T: Assume WebSocket sends JSON arrays — each message is one JSON object.
✘ DON'T: Silently change anything you think is wrong in the spec — flag it.

---

## FINAL RULE

> When in doubt: **stop, re-read, ask.**
> Never guess. Never invent. Never silently fix.
> Flag conflicts. Wait for human resolution.
> The spec is right until a human says otherwise.

─────────────────────────────────────────────────────────────────────────────
VedFin Sentinel | AGENT_RULES.md | InnVedX Hackathon 2026
PRD + Design Doc + These Rules = Complete Agent Context
─────────────────────────────────────────────────────────────────────────────
