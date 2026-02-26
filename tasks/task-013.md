# Task 013: Frontend Attack Simulation Lab

pending / P1 / medium / 3 hours / frontend, ui, simulation

## Description
Build the simulation UI allowing users to trigger attack scenarios and view events streaming via NDJSON.

## PRD Reference
- Section 7.4 Attack Simulation Laboratory
- Dictates 3 core scenarios: Geo-Spoofing, Burst Micro-Transaction, Account Takeover.

## Design Document Reference
- Section 6.4 AttackTimeline.tsx - NDJSON Streaming
- Requires `fetch` readers streaming multiple parsed payloads into condition states for timelines.

## AGENT_RULES Reference
- Rule 9. FRONTEND RULES
- Ensures semantic HTML tags use sectioning accurately for these complex layout blocks.

## Authority Compliance Plan
- **PRD**: Exposes interactive control over mock sequences driving the "Heist and Catch" narrative layout.
- **DesignDoc**: Implements custom JS `fetch` streams natively supporting NDJSON (Newline Delimited JSON).
- **AGENT_RULES**: Avoids arbitrary `eval` or weak string concatenation bugs mapping server pushes to state actions securely.

## Acceptance Criteria
- Choosing an attack scenario initiates `POST` fetching NDJSON responses.
- Timeline accurately sequentially mounts new event components displaying risk bands increasing.
- "Heist and Catch" presentation is fluidly playable locally without backend manual setup mapping.

## Dependencies
- task-010, task-008

## Implementation Approach
1. Build high-quality interactive selection panels `ScenarioSelector` holding the 3 target concepts.
2. Develop standard HTTP streaming processor decoding chunked `UTF-8` on newline characters.
3. Manage active simulation `isRunning` states via Zustand.
4. Animate timeline entries with `Framer Motion` for engaging hackathon demos.

## Files to Modify/Create
- frontend/app/attack-simulation/page.tsx
- frontend/components/simulation/*.tsx

## Testing Requirements
- None specific outside visually mapping correctly.

## Edge Cases
- Malformed NDJSON chunking splitting string payloads incorrectly requires buffered reading to prevent `JSON.parse` exceptions mid-transmission.

## Notes & Considerations
- Use browser `ReadableStreamDefaultReader` carefully ensuring `cancel()` calls on components unmounting.

## Questions/Clarifications
- None at this time.
