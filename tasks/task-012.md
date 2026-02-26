# Task 012: Frontend Live Transactions Feed

pending / P1 / high / 4 hours / frontend, websockets, ui

## Description
Implement real-time transaction feed via WebSocket and single transaction detail view with SHAP waterfall.

## PRD Reference
- Section 7.2 Analytics Dashboard & 7.3 Explainable AI
- Covers transaction streaming and SHAP explanation reading.

## Design Document Reference
- Section 6.4 TransactionFeed.tsx - WebSocket Integration
- Reconnection logic definition for websockets. NDJSON event streaming concepts.

## AGENT_RULES Reference
- Rule 9. FRONTEND RULES
- Locks exponential backoff logic required for websockets.

## Authority Compliance Plan
- **PRD**: Brings the active stream logic into UI reality. Displays human explanations created by SHAP for every flagged transaction.
- **DesignDoc**: Matches exact hook schemas defining real-time components and the specific reconnect pattern.
- **AGENT_RULES**: Correct implementation ensures that component trees do not leak memory without closed sockets on demounts via `useEffect` cleaning.

## Acceptance Criteria
- Custom hook `useFraudStream` gracefully manages opening `ws://` to backend stream.
- WebSocket automatically reconnects when down tracking exponential limit (1s->30s).
- Transactions visually appear at the top of the feed mimicking infinite list behaviors.
- Deep links `/transactions/{id}` render static detailed data including SHAP Waterfall chart.

## Dependencies
- task-010, task-008

## Implementation Approach
1. Wire custom `useFraudStream` handling standard `WebSocket` browser API.
2. Store received `SimulationEvent` packets into global Zustand `transactionStore`.
3. Construct lists feeding off store state array holding slices of the most recent `~100`.
4. Build SHAP Explainer UI bridging raw tuple array values to ordered `Recharts` bar visualizations.

## Files to Modify/Create
- frontend/app/transactions/page.tsx
- frontend/app/transactions/[txn_id]/page.tsx
- frontend/hooks/useFraudStream.ts
- frontend/components/transactions/*.tsx

## Testing Requirements
- Mock WebSocket Server injections ensuring reconnect behavior scales properly on closed event statuses.

## Edge Cases
- Feed must limit bounds (i.e. > 500 nodes in DOM will drag page). List virtualization generally unnecessary if manually capping array slice.

## Notes & Considerations
- Strict strict mode react effect firing triggers double mounts, test correctly.

## Questions/Clarifications
- None at this time.
