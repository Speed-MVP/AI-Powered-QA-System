Phase 10 — Rollout, Migration, Quality Gates, Monitoring, Operational Playbooks, and Final Launch Checklist

Purpose: define everything needed to deploy the full QA Blueprint System safely into production for real call-center usage. This includes migration plans, feature-flag rollout, soft-launch workflows, training, monitoring, and post-launch improvement loops. This phase ensures you don’t break existing customers, don’t introduce failures in the real evaluation pipeline, and deliver a predictable and controlled launch.

This is the phase companies screw up most often — this eliminates the mistakes.

1 — Strategic Rollout Plan (Zero-Risk Deployment)
1.1 Feature Flags (must exist)

Introduce these flags in backend config so you can turn features on/off per company without redeployment:

Flag	Purpose
enable_blueprints	Lets a company use Blueprints system
enable_blueprint_publish	Allows blueprint compile/publish
enable_blueprint_sandbox	Sandbox access for company
enable_blueprint_production_eval	Whether production evaluation pipeline uses the new Blueprint engine
enable_legacy_pipeline_fallback	Force fallback to legacy system

Always keep legacy fallback operational until full migration is complete.

1.2 Phased Rollout (recommended)

Rollout in 4 stages:

Stage A — Internal Alpha

Only your team sees Blueprints (flags enabled only for your company).

Sandbox heavily tested.

Production pipeline still legacy.

Stage B — Closed Beta (1–2 friendly companies)

These customers get Blueprint Editor + Sandbox.

Their production still uses legacy pipeline but you run the Blueprint pipeline in “shadow mode” to compare.

No risk — Blueprint output never affects real scores yet.

Stage C — Open Beta

More companies invited.

Enable Blueprint production evaluation per company after confirmation and template import.

Still allow instant rollback to legacy via feature flags.

Stage D — Full Launch

Default blueprint system for all new customers.

Legacy available only via “compatibility mode”.

Rollout should not be big-bang.
This ensures no data loss or accuracy surprises.

2 — Migration Plan (Existing Customers)
2.1 Understanding existing customers

Current deployments have:

Policy Templates

Evaluation Criteria

Rule Engine settings

Rubric levels

These must be converted into:

Blueprint (stages + behaviors)

Detection rules

Behavior weights

Stage weights

Scoring configuration

2.2 Migration Assistant (required tool)

A backend service to generate Blueprint drafts from legacy templates:

Parse existing Evaluation Criteria

Convert each criterion into a Stage

Convert rubric levels into detection rules & behaviors

Map old rule-engine settings into Behavior definitions

Suggest weights based on old weighting rules

Flag ambiguous places for manual editing

Output:

{
  "draft_blueprint_id": "uuid",
  "mapping_report": { ... },
  "warnings": [
    "criteria 'Empathy' had vague rules — requires manual mapping",
    "rule 'Must say X' had more than 10 variants"
  ]
}

2.3 Customer Migration Workflow

Customer enters Migration Dashboard

System auto-generates a draft Blueprint from old template

QA manager reviews stages/behaviors, adjusts weights

Customer runs Sandbox on sample calls

Once satisfied → publish Blueprint

Enable “Blueprint in production” flag

2.4 Rollback

Any customer can one-click:
“Switch back to legacy pipeline”
You must maintain backward-compatible endpoints for at least 6 months.

3 — Quality Gates (Hard Requirements Before Launch)

These are mandatory checkpoints. If any fails, do not allow Blueprint in production.

3.1 Evaluation Accuracy Gate

Your blueprint pipeline must achieve:

Metric	Requirement
Score delta vs human QA	≤ ±5 points average
Category consistency	≥ 92% agreement
Critical detection false positives	< 2%
Critical detection false negatives	< 1%
LLM hallucination rate	< 0.5% (via schema validation)

These are not optional.
If you fail these, customers will immediately distrust the system.

3.2 Performance Gate

Sync transcript sandbox < 2 seconds median

Async audio sandbox < 2× audio length P95

Production evaluation < 4–7 seconds median

Worker queue backlog < 50 jobs P95

CPU cost per evaluation < $0.02, tokens < 1500

If performance is poor, uptime collapses under load.

3.3 Safety Gate

All PII is redacted before LLM

Zero-data-retention enabled by default

Prompt injection attempts neutralized

Behavior weights validated (exact 100%)

Critical rules require double confirmation

Blueprints locked after publish (versioned & immutable)

4 — Monitoring & Observability (Real-World Ops)
4.1 Core Metrics (must track)

Evaluation Pipeline

evaluations_per_minute

eval_latency_p50/p95

llm_tokens_used

model_errors_per_minute

fallback_rate (LLM → deterministic)

confidence_distribution

human_review_rate

Blueprint Editor

blueprint_saves

blueprint_publishes

compile_job_failures

validation_failure_counts

Sandbox

sandbox_runs

sandbox_failures

average_cost_per_run

avg_transcription_confidence

Workers / Infrastructure

worker_cpu/memory

queue_depth

queue_wait_time

worker_failures

4.2 Alerts (must configure)

Trigger on:

LLM error rate > 1% for 10 min

Transcription vendor error > 2%

Confidence score anomaly (drop > 10%)

Human review rate > 20% unexpectedly

Sandbox run failures > 5%

Cost anomaly: tokens spike > 40%

Queue backlog > 200 jobs

These prevent silent degradations.

4.3 Logs & Debugging

Store:

Pipeline trace for every evaluation

Transcript hash or redacted transcript

JSON snapshots for each stage

Detection evidence

Prompt version + seed

Worker logs with correlation IDs

5 — Company Training & Onboarding Materials
5.1 Customer-facing documentation

“How Blueprints Work”

“How to Build Your Flow”

“How to set up weights properly”

“What Critical does vs Required”

“How Sandbox results differ from Production”

“Why scores change sometimes (model updates)”

5.2 Internal playbooks

How to debug a complaint:

Pull evaluation snapshot

Compare to human review

Re-run sandbox

Inspect behavior evidence

Check prompt version changes

How to resolve sandbox run failures

How to increase customer quotas

How to perform a blueprint version rollback

How to test new model releases before rollout

6 — Model & Prompt Versioning Strategy
6.1 Every evaluation must record:

prompt_version

model_version

temperature

seed

blueprint_compiled_version_id

6.2 Prompt lifecycle

Draft → Internal Test → Customer Beta → Stable → Deprecated

Never break a customer by upgrading prompts without warning.

For prompt updates, use progressive rollout:

10% → 25% → 50% → 100% of customers

Always allow customer to pin to older version for 30–60 days.

7 — Pipeline Version Compatibility
7.1 Requirements

Allow Blueprint v1, v2, v3… compiled flows to coexist.

Evaluation references exact version of compiled blueprint.

Never mutate a compiled version.

Auto-create new compiled version on publish.

7.2 Legacy pipeline coexistence

Legacy continues operating fully independent.

Blueprints output stored under different column in evaluations.

Supervisor dashboards merge legacy and blueprint results seamlessly.

8 — Business Readiness
8.1 Pricing model (optional suggestions)

Free Sandbox runs up to X per month

Pay-as-you-go tokens for LLM

Per-seat pricing for QA teams

Enterprise plan: unlimited Blueprints, SLA, onboarding

Optional fine-tuning add-on

8.2 SLAs

Evaluation availability: 99.9%

Sandbox availability: 99.5%

Support response: 4–24 hours depending on plan

Worker queue processing: < 5 min delay P95

9 — Final Launch Checklist (do not skip)
Technical

 All migrations applied without downtime

 Feature flags working per-company

 Blueprint editor fully functional (Phase 8)

 Sandbox fully functional (Phase 9)

 Detection engine stable on your corpus

 Stage LLM evaluator stable

 Scoring engine (Phase 7) deterministic & tested

 Audit logs & snapshots stored properly

 No transcript PII leak into logs or LLM

Accuracy

 At least 200 real calls tested via sandbox

 Score drift validated vs human QA

 Critical detection validated by QA managers

 Pass/fail thresholds finalized with customer input

Monitoring

 Alerts configured

 Token usage dashboard active

 Worker queue dashboard active

 Error dashboards operational

UX

 Publish validation errors friendly & actionable

 Sandbox results fast & explainable

 Human review UI smooth

 Error/retry flows tested

Business

 Documentation written

 Sales materials updated

 Pricing configured

 SLAs published

Go-Live

 Migrate 1 test company first

 Enable Blueprints for pilot customers

 Monitor for 1–2 weeks

 Roll out gradually to rest

10 — Post-Launch Continuous Improvement Process
Every month:

Track score drift between AI and human.

Re-run sandbox on sample dataset to detect LLM/model changes.

Run prompt version A/B tests.

Update templates.

Add new default behaviors from real customer calls.

Evaluate customer-reported false positives/negatives.

Improve detection model or add new semantic patterns.

Every quarter:

Compile “Blueprint Accuracy Report” per customer.

Suggest updates to their Blueprint automatically (detected issues, missing behaviors).

Calibrate scoring weights based on performance data.

Update LLM model version (only after testing).