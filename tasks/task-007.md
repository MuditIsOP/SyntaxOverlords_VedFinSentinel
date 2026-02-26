# Task 007: Core Prediction Endpoints

pending / P0 / high / 4 hours / backend, api

## Description
Implement the /api/v1/predict and /api/v1/bulk_predict endpoints including audit logging.

## PRD Reference
- Section 12. API Specification Core Endpoints
- Explicit requests and response signatures required.

## Design Document Reference
- Section 4.1 POST /predict & 4.2 POST /bulk_predict
- Section 7.1 Full Predict Flow

## AGENT_RULES Reference
- Rule 2.4 Audit Log Integrity
- Rule 8. API RULES

## Authority Compliance Plan
- **PRD**: Implements SLA of <340ms inference, generating structured `RiskAuditLog`.
- **DesignDoc**: Maps the 12 endpoints correctly and matches the schema for `TransactionRequest` and `FraudScoreResponse`.
- **AGENT_RULES**: Ensures that NO `UPDATE` or `DELETE` ever mutates the write-only audit_logs outside allowed properties. Hashes transactions.

## Acceptance Criteria
- `POST /api/v1/predict` successfully validates inputs, triggers the full flow (Vedic -> Feature Engine -> Ensemble -> Explainability).
- Database persists `Transaction` and securely hashed `RiskAuditLog`.
- WebSockets queue logic pushes `FraudScoreResponse`.

## Dependencies
- task-002, task-003, task-004, task-006

## Implementation Approach
1. Stub the FastAPI routing for predictability logic.
2. Structure the `fraud_scoring` service logic to chain all dependencies.
3. Validate Pydantic data strictly for things like past/future limits.
4. Calculate `log_hash` and commit logs safely securely.

## Files to Modify/Create
- backend/app/api/v1/predict.py
- backend/app/api/v1/bulk_predict.py
- backend/app/services/fraud_scoring.py
- backend/tests/test_predict_endpoint.py
- backend/tests/test_audit_log.py

## Testing Requirements
- Extensive `pytest` usage spanning edge cases: invalid coordinates, past timestamps, and rate limiting coverage.

## Edge Cases
- Extremely fast burst requests leading to database race conditions correctly mitigated by transaction isolation.

## Notes & Considerations
- Ensure transactions are accurately pushed to `asyncio.Queue` only AFTER standard database commits resolve via FastAPI BackgroundTasks or directly in the flow.

## Questions/Clarifications
- None at this time.
