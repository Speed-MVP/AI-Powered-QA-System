## Post-Evaluation Implementation Roadmap (Excludes Coaching, Disputes, and Integrations)

Scope: This roadmap lists high-impact features to implement after evaluation testing. It explicitly excludes Coaching & Goals, Human‑in‑the‑Loop & Disputes, Integrations (CRM/ticketing/dialers/WFM/BI/webhooks), and coaching queues.

### 1) Agent and Team Directory
- Objective: Enable org-wide dashboards keyed by `agent_id`/`team_id` and granular drill-downs.
- Data model:
  - agents/teams may be represented by existing `users` with roles; add `teams` and `agent_team_memberships` if needed.
  - Add `agent_id`, `team_id` to `recordings`/`evaluations` if not already derivable.
- API:
  - GET `/agents`, `/teams`, `/agents/{id}/summary`, `/teams/{id}/summary`.
- Dashboard:
  - Leaderboards by team/agent; cohort comparisons; filter by timeframe, channel, language.

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


