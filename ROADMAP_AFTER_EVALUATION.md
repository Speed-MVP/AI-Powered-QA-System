## Post-Evaluation Implementation Roadmap (Excludes Coaching, Disputes, and Integrations)

Scope: This roadmap lists high-impact features to implement after evaluation testing. It explicitly excludes Coaching & Goals, Human‑in‑the‑Loop & Disputes, Integrations (CRM/ticketing/dialers/WFM/BI/webhooks), and coaching queues.

## 1) Agent and Team Directory

### Objective
Enable org-wide dashboards keyed by `agent_id`/`team_id` and granular drill-downs. Establish a scalable, audit-compliant agent/team data model that serves as the foundation for all downstream analytics.

### Critical Context: Philippine BPO Market Reality

**Important:** The agent/team data ingestion strategy must account for the actual technology landscape of Philippine BPOs. Unlike enterprise SaaS targeting Global 500 companies, Philippine BPOs (especially SMEs) operate in a significantly different environment:

- **Enterprise BPOs (500+ agents):** Using Genesys Cloud, Five9, or NICE CXone, but these are primarily contact center platforms with minimal HR system integration. Agent rosters are typically manually created within these platforms, not synced from HR systems.
- **Medium BPOs (100-300 agents):** Hybrid of cloud and legacy systems; inconsistent or non-existent HR system infrastructure. Limited expectations for advanced integrations.
- **Small BPOs (30-100 agents):** Primarily manual operations using spreadsheets and Excel; no formal HR system; no SCIM/API infrastructure.

**Critical finding:** SCIM 2.0 and API-first integrations are not feasible for 80%+ of Philippine BPO market in MVP phase. Most small-to-medium operations still rely on manual spreadsheet-based agent management. Modern integration patterns (Okta, Azure AD, Workday syncs) exist in the enterprise market but are absent in Philippine BPOs.

### Recommended Ingestion Strategy

**Phase 1 (MVP):** Manual UI + Bulk CSV/Excel Import (Non-Source-of-Truth)
- **Manual UI:** Supervisors can create agents/teams one-by-one in your system via forms.
- **CSV Bulk Import:** Provide a validated bulk import interface with:
  - Column mapping (so they map "Employee Name" to `agent_name`)
  - Preview and validation before commit
  - Conflict resolution (duplicate detection, update vs. insert logic)
  - Full audit trail logging who uploaded what, when, and what changed
- **Key principle:** CSV is a **convenience tool for onboarding**, not the source of truth. Once data enters your system, you own it and track all changes.
- **Audit Trail:** Every agent/team creation, update, and deletion is immutably logged with timestamp, user, and change details (required for compliance).

**Phase 2 (6-12 months, based on customer requests):** Platform-Specific Integrations
- Monitor which systems your customers request integrations with (likely Genesys Cloud, Five9, basic HR systems if they exist).
- Build adapters for the top 3 platforms your paying customers request.
- Focus on one-way sync (pull agent roster from their platform on schedule or manual trigger).

**Phase 3 (18+ months):** SCIM 2.0 and Identity Provider Support
- Implement SCIM 2.0 protocol for enterprise customers with mature identity infrastructure.
- This is a **long-tail feature** for the Philippine market; deprioritize in MVP.

### Data Model

- agents/teams represented by `users` with roles; add `teams` and `agent_team_memberships` tables.
- Add `agent_id`, `team_id` to `recordings`/`evaluations` if not already derivable.
- Add audit columns to `teams` and `agent_team_memberships`: `created_by`, `created_at`, `updated_by`, `updated_at`, `deleted_at`.
- Maintain immutable change log: `agent_team_changes(id, agent_id, team_id, change_type, old_value, new_value, changed_by, changed_at)`.

### API Endpoints

- `GET /agents` — List all agents with filters (team, status, created_date range)
- `GET /teams` — List all teams
- `GET /agents/{id}/summary` — Agent KPI snapshot (QA score, FCR%, CSAT, recent evaluations)
- `GET /teams/{id}/summary` — Team KPI snapshot
- `GET /teams/{id}/agents` — List agents in a specific team
- `POST /agents/bulk-import` — Initiate CSV bulk import (returns import job ID for polling)
- `GET /agents/bulk-import/{job_id}` — Poll import status, validation errors, preview
- `GET /agents/audit-log` — Immutable audit trail of all agent/team changes (for compliance reporting)

### Dashboard

- Leaderboards by team/agent (QA score, FCR%, CSAT, AHT); cohort comparisons
- Filters by timeframe, channel, language, team, agent
- Quick drill-down from dashboard to individual agent/team performance page
- Audit trail visibility for supervisors (who created/modified agent assignments, when)

---
### 2) CSAT/NPS Capture and Correlation
- Objective: Tie QA outcomes to customer feedback.
- Data model:
  - `customer_feedback(recording_id, agent_id, source, csat, nps, comment, created_at)`.
- API:
  - POST `/feedback/csat`, `/feedback/nps`; GET `/analytics/csat-nps?by=agent|team`.
- Analytics:
  - Correlate CSAT/NPS with QA score, FCR, sentiment; trend lines; outlier detection.

### 3) FCR and Efficiency Metrics
- Objective: Quantify first-contact resolution and operational efficiency.
- Derive FCR% from existing `evaluations.resolution_detected` per agent/team/timeframe.
- Additional speech/ops metrics to compute and store per call:
  - AHT, hold time, silence percent, talk/listen ratio, overlap/interruptions, filler rate, pace (wpm), transfer/escalation flags.
- API:
  - GET `/analytics/fcr`, `/analytics/efficiency`, `/analytics/fcr-trends`.
- Dashboard:
  - FCR% by agent/team; scatter plots (AHT vs Score, FCR vs CSAT); target lines.

### 4) Advanced Speech Analytics
- Objective: Richer insights beyond transcript text.
- Features:
  - Dead-air detection; overlap/interruptions; prosody-based stress spikes; empathy cues; escalation detection.
  - Topic/intent tagging and issue taxonomy.
- Storage:
  - `speech_metrics` table keyed by `recording_id` for numeric/time-series metrics.
- Visualization:
  - Call timeline overlays for sentiment, interruptions, silence; per-category heatmaps.

### 5) Compliance Packs and Risk Center
- Objective: Out-of-the-box compliance checks and reporting.
- Packs:
  - TCPA/FDCPA/HIPAA baselines, PCI redaction flags, jurisdictional rules.
- Features:
  - Compliance score, pass rate by pack/jurisdiction, critical violation alerts, monthly compliance report exports.
- API:
  - GET `/compliance/reports?period=...`, `/compliance/stats`, `/compliance/violations/top`.

### 6) QA Calibration and Sampling
- Objective: Maintain evaluation consistency and scale coverage.
- Features (no coaching/disputes):
  - Multi-rater calibration sessions; score variance analytics; rubric drift detection.
  - Automated sampling policies (random/stratified/high-risk); coverage dashboards.
- API:
  - GET `/calibration/sessions`, POST `/calibration/sessions` (session creation, participants, assigned calls).

### 7) Knowledge Assist and RAG
- Objective: Connect evaluations to knowledge quality and gaps.
- Features:
  - Link frequent misses to KB articles; suggest improvements; article effectiveness analytics (post‑update delta in violations/scores).
- API:
  - GET `/knowledge/opportunities`, `/knowledge/article-impact`.

### 8) Security, Privacy, and Governance
- Objective: Enterprise readiness.
- Features:
  - PII/PCI redaction pipeline; configurable retention by data type; RBAC policies; immutable audit logs; SSO/SCIM readiness (models and toggles).
- Reporting:
  - Access audit reports, retention policy audits, export controls.

### 9) Model Ops, Confidence, and Cost Controls
- Objective: Reliability and cost transparency.
- Features:
  - Confidence distribution, fallback thresholds, failure/timeout monitoring; Flash/Pro routing policies; per-call cost estimation.
- Dashboard:
  - Cost usage split, confidence vs accuracy (using human-reviewed ground truth when available), error rates.

### 10) Multilingual and Localization
- Objective: Global coverage.
- Features:
  - Language detection; multilingual transcription; locale-aware rubrics and compliance; per-language analytics.
- Dashboard:
  - Breakdowns by language/region; translation toggles for transcripts and summaries.

### 11) Benchmarking and Targets
- Objective: Drive performance with clear goals.
- Features:
  - Metric targets per org/team/agent; on‑track/off‑track flags; lightweight alerts; industry/tenant benchmark overlays.

### 12) Dashboard Specifications (No Coaching/Disputes)
- UI Navigation (Navbar):
  - Role/Session-aware menu.
    - Unauthenticated/marketing: `Home`, `Features`, `Pricing`, `Login`, `Sign up`.
    - Authenticated QA (agent): `Dashboard`, `My Evaluations`, `Analytics`, `Recordings`, `Profile`.
    - Authenticated Supervisor/Manager: `Dashboard`, `Agents`, `Teams`, `Analytics`, `Compliance`, `Settings`.
  - Behavior:
    - On login, navbar switches to the authenticated set based on role/claims.
    - Preserve deep links and active state; responsive/mobile menu parity.
    - Hide or disable routes without permission (RBAC).
- Supervisor (Org‑wide):
  - KPIs: FCR%, Avg QA score, CSAT, NPS, AHT, Compliance pass rate, Top violations, Confidence distribution, Model usage/cost.
  - Views: Agent and Team leaderboards; Trends (7/30/90 days); Heatmaps (category scores vs team/agent); Risk Center (critical violations by pack/region).
  - Drill‑downs: filters by timeframe, team, agent, channel, language, campaign; quick link to evaluated call with timeline overlays.
- Agent (Personal):
  - KPIs vs targets and peers (no coaching tasks); strengths/gaps by rubric; recent evaluated calls with sentiment/violation highlights.
- QA Analyst:
  - Sampling coverage, calibration sessions (no coaching/disputes), rubric version comparisons, variance and drift indicators.

### 13) Minimal Backend Work Plan
1. Schema: add `teams`, membership, `customer_feedback`, `speech_metrics`; add `agent_id`/`team_id` where needed.
2. Services: compute speech metrics during processing; FCR aggregation; CSAT/NPS correlation.
3. APIs: analytics endpoints for overview, trends, FCR, efficiency, CSAT/NPS, compliance, calibration.
4. Dashboards: supervisor/agent/analyst pages with filters and drill‑downs; timeline overlays from transcript+metrics.
5. Governance: redaction, retention, RBAC, audit views.

Notes:
- Coaching, coaching queues, goals, disputes, reviewer queues, side‑by‑side AI vs Human views, and external integrations are explicitly out of scope for this phase and intentionally omitted from this document.


