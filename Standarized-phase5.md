PHASE 5 — RUBRIC BUILDER (LINKED TO SOP)

Objective: Implement a Rubric/Criteria system that no longer floats as abstract text but is explicitly mapped to SOP stages and steps. Rubrics define scoring bands, weights, and aggregations — they do not define procedural rules. This phase turns stage-level deterministic results and LLM feedback into category scores and the overall score used for pass/fail and reporting.

Below are full, implementation-grade instructions for an AI coder — no code, exact behaviors, validations, UI expectations, integration points, acceptance tests, and rollout notes.

1 — High-level summary (non-negotiable)

Rubrics must reference SOP steps/stages by ID.

Rubrics control: category names, weights, level thresholds, mapping to steps, and aggregation rules.

Rubric evaluation occurs after Phase 3 rule engine and Phase 4 LLM stage evaluations.

Rubrics must be versioned and tied to a FlowVersion.

Rubrics produce numeric category scores and text-level feedback (from LLM) and are the basis for overall scoring.

2 — New / updated entities (conceptual)

RubricTemplate (per policy_template / flow_version)

id

policy_template_id

flow_version_id (tie to specific SOP)

version_number

created_by / created_at

is_active

description

RubricCategory

id

rubric_template_id

name (e.g., Accuracy_Process, Communication, Empathy, Resolution)

description

weight (percentage, total across categories must sum to 100; validate)

pass_threshold (integer 0–100; overall pass uses policy-level threshold later)

level_definitions: array of { name, min_score, max_score, label } — ensure bands non-overlapping

RubricMapping

id

rubric_category_id

target_type: "stage" | "step"

target_id: reference to stage_id OR step_id

contribution_weight: relative weight within category (for aggregating multiple steps/stages)

required_flag: boolean (if a mapped target is required, failing it should be treated as critical to the category)

RubricRuleOverrides (optional)

category-specific penalty adjustments (e.g., missing required step subtract 20 points in this category vs global penalty)

3 — UI: Rubric Builder screen (detailed UX)

Add a Rubrics tab to the layered Policy Editor. Key panels:

3.1 Rubric List Panel

Shows active rubric templates per policy/flow version.

Buttons: Create Rubric Template, Edit, Duplicate, Publish.

3.2 Rubric Template Editor (main panel)

Sections:

Header (name, description, associated FlowVersion, version controls)

Category Grid — list of categories with weight and pass_threshold (editable inline)

Allow drag-to-reorder categories (UI only)

Validate total weights sum to 100 before publish

Category Detail Pane (when selecting a category)

Name, description, weight, pass_threshold, level_definitions

Mapping Area: attach stages/steps from FlowVersion (drag from SOP builder area into mapping list)

For each mapping entry: select target (stage or step), set contribution_weight, mark required_flag if applicable

Override Section: optional penalty overrides for this category

Preview Area: shows how a category score will be calculated from mapped steps (example with hypothetical step results)

Publish/Save: Save draft, Validate, Publish as versioned rubric template.

3.3 Quick mapping UX specifics

Permit quick-map: select one or more steps and assign to a category with a single action.

Show warnings if mapped steps belong to multiple categories (allowed but warn about overlap).

Show tooltip: If a mapped step is required in SOP and category does not mark it required_flag, warn.

4 — Behavior & computation rules (exact)
4.1 Aggregation within category

Category score calculation (exact algorithm):

Collect mapped targets T = {t1..tn}. Each target has:

target_result_score (0–100) derived from stage_evaluations / step_evaluations:

If target_type == "stage": use stage_score

If target_type == "step": compute step_score = 100 if step.passed == true; else 100 - penalty_per_missed_step (configurable) OR use LLM step confidence to scale

contribution_weight (CWi)

Normalize contribution weights so ΣCWi = 1 for that category:

normalized_CWi = CWi / ΣCWi

Category raw score = Σ(normalized_CWi × target_result_score)

Apply category-level overrides:

If any required_flag target failed and rubric_override specifies "fail_on_required" → set category score = min(category score, fail_floor) or mark for human review (configurable)

Clamp to 0–100

Default penalties / rules (sensible defaults; make configurable per policy):

Missing required step penalty at step level = 100 (step fails)

Step-level score if failed = 0 (simpler deterministic behavior)

If using LLM step confidence, step_score = round(confidence × 100) where confidence = LLM step_confidence * deterministic_evidence_confidence (only if enabled)

4.2 Category weights to overall score

Overall score = Σ(category_score × (category_weight / 100))

Respect category pass_thresholds when reporting pass/fail per category, but overall pass/fail is controlled by policy-level pass threshold.

4.3 Pass / fail logic

Policy-level overall_pass_threshold exists (e.g., 85).

If any critical compliance violation → overall fail regardless of score (auto-fail).

If requires_human_review → do not auto-close pass; flag as review (but optionally allow auto-pass if policy setting enabled).

4.4 Handling overlaps and conflicts

If one step maps to multiple categories, it contributes to each as per assigned contribution_weight. Warn user during mapping if the same step contributes >50% total across categories (potential double-counting risk).

5 — Integration with prior phases (exact)

When evaluating a recording:

Load active FlowVersion and its RubricTemplate (matching flow_version_id).

Consume rule_engine_output (Phase 3) and llm_stage_evaluations (Phase 4).

For each mapped target, extract target_result_score using rules in 4.1.

Compute category scores and overall score via algorithms above.

Prepare output payload for persistence and UI: include per-category breakdown, per-target contributions, and evidence pointers.

Store mapping references (rubric_template_id → flow_version_id) in evaluation record for audit.

6 — UI for viewing evaluation result (how to present computed rubric results)

On evaluation detail page:

Show overall score and pass/fail banner.

Show category tiles: score, weight, pass_threshold, small graph of contributions.

Expand category to show mapped targets with:

target name (stage or step), contribution weight, target_result_score, evidence link(s), pass/fail.

Show list of violations prioritized by severity with evidence.

Show LLM feedback snippets per stage alongside matching rubric categories.

7 — Validations & warnings (enforced at publish time)

Sum(weights) == 100 → Block publish if false.

Categories must have at least one mapped target → Warn or block (configurable).

Mapped target must exist in linked FlowVersion → Block.

If a mapped target is marked required in SOP but not flagged required_flag in mapping → Warn.

Level_definitions must cover 0–100 with no gaps/overlaps → Block publish.

8 — Acceptance tests (must pass)

Test A — Mapping & calculation

FlowVersion: Discovery has 3 steps mapped to Accuracy category with contribution weights 1,1,2; stage scores: step1 100, step2 0, step3 80. Expected Accuracy score: normalize weights (1/4,1/4,2/4) => score = 0.25×100 + 0.25×0 + 0.5×80 = 25 + 0 + 40 = 65.

Test B — Weight sum enforcement

Create rubric with weights summing to 95 → publishing blocked with clear error.

Test C — Required step fail impact

A step marked required in mapping failed -> category flagged and if configured must trigger human review or floor score.

Test D — Overlap mapping

Same step mapped to two categories; both categories reflect step result appropriately.

Test E — Version tie

Publish new FlowVersion and new RubricTemplate. Older evaluations still reference older RubricTemplate and produce same results when reloaded.

Test F — Edge: no mapped targets

Category with no mapped targets → either blocked on publish or results in category_score = 100 by default? (Decide: block publish; explicit map required).

9 — Edge cases & behavior rules

If RubricTemplate absent for a FlowVersion, fallback to default template (system admin must define a default). Warn and require admin confirmation to evaluate.

If a mapped target has no step_result (engine failed to evaluate), treat its target_result_score as 0 and mark coverage deficiency; set requires_human_review = true.

If multiple RubricTemplates exist for a FlowVersion, only one may be active. Published RubricTemplate must be tied to a specific FlowVersion version.

10 — Audit & versioning

Like FlowVersion, RubricTemplate must be immutable after publish. Store version_id in evaluations.

Keep change diff & audit trail for rubric publishes (who changed, what changed).

Allow copying an older RubricTemplate to create a new draft.

11 — Admin tools & calibration UI (recommended)

Offer a Calculator/Preview: sample input (mock step results) to show how category and overall scores compute.

Provide a What-if tool: toggle a specific step pass/fail to see impact on category and overall score (useful for policy authors).

Show coverage metrics: percent of mapped targets with evidence in recent evaluations (help tune mapping).

12 — Documentation & user guidance

Documentation must clearly state:

Rubrics reference steps/stages — they do not create rules.

If you want a procedural enforcement, add a ComplianceRule in Phase 2.

How to map steps to categories effectively (best practices).

Explanation of aggregation algorithm and default penalties.

How to interpret coverage and missing evidence.

13 — Acceptance checklist (deliverables)

 Rubric Template Editor UI with category mapping to SOP steps/stages.

 Backend persistence for RubricTemplate, RubricCategory, RubricMapping with versioning.

 Weight sum validation and level definition validation.

 Aggregation algorithm implementation producing category and overall scores.

 Integration test connecting Phase 3 & 4 outputs into rubric scoring pipeline.

 UI for viewing per-category breakdown with evidence links.

 Audit logs and versioning.

 Documentation and sample "what-if" calculator UI.

14 — Timeline estimate

(1 AI coder + 1 frontend + 1 backend):

Data model & API: 2 days

Rubric UI + mapping UX: 4 days

Aggregation implementation & config: 2 days

Integration tests & acceptance tests: 2 days

Docs & polish: 1 day
Total: ~11 working days.

15 — Final blunt note

If you don’t map rubrics explicitly to SOP steps, you will keep getting meaningless category scores that can’t drive coaching or be trusted by clients. Phase 5 fixes this root problem: rubrics become precise aggregators of procedural compliance and quality. Implement exactly as specified; do not shortcut the mapping or versioning rules.