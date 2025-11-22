PHASE 2 — COMPLIANCE RULES BUILDER (BARE-MINIMUM, FULL SPEC)

Purpose:
Provide a minimal, structured Compliance Rule Builder so the evaluation pipeline can deterministically enforce legal/mandatory behaviors (auto-fail or penalties). These rules are independent from rubrics and must be evaluated before or alongside SOP checks. No extras — only what’s necessary for deterministic enforcement.

0 — Summary of what to deliver

A single UI page/tab to create/edit/delete compliance rules tied to an active FlowVersion from Phase 1.

A minimal set of rule types that cover the most common compliance needs.

Structured storage format (JSON) for each rule.

Deterministic semantics (exact behavior defined) so the rule engine (Phase 3) can enforce rules reliably.

Validation and simple preview text for each rule.

Clear integration contract so rule engine consumes them unambiguously.

No permission/roles, no versioning beyond linking to FlowVersion (FlowVersion already exists), no auditing UI, no analytics.

1 — Minimal rule types to support (cover required functionality)

required_phrase — must say X (e.g., recording disclosure).

forbidden_phrase — must NOT say X (e.g., no promises).

sequence_rule — step A must occur before step B (ties to Phase 1 step IDs).

timing_rule — phrase or step must occur within N seconds of call start or previous step.

verification_rule — KBA/identity verification must be performed before resolution steps (pre-configured as question_count and verification_step_id).

conditional_rule — if condition Y (customer sentiment negative OR mention of billing), then required action Z must occur.

These cover 95% of required compliance checks for minimal QA.

2 — Data model (exact JSON shape for each rule)

Each rule stored as one JSON object. Example schema (fields required unless noted):

ComplianceRule {
  id: "<string>",                    // unique
  flow_version_id: "<string>",       // required: ties rule to specific FlowVersion
  title: "<string>",                 // short
  description: "<string>",           // human readable
  severity: "critical"|"major"|"minor",
  rule_type: "required_phrase"|"forbidden_phrase"|"sequence_rule"|"timing_rule"|"verification_rule"|"conditional_rule",
  applies_to_stages: [ "<stage_id>", ... ],   // optional, empty => apply to whole call
  params: { ... },                   // see rule_type-specific params below
  active: true|false                 // allow enabling/disabling rule
}

params per rule_type
a) required_phrase
params: {
  phrases: [ "<string>", ... ],      // exact or normalized phrases
  match_type: "exact"|"contains"|"regex", // default "contains"
  case_sensitive: false,             // default false
  scope: "stage"|"call",             // stage uses applies_to_stages
  allowed_variants: [ "<string>" ]   // optional list of acceptable variants
}

b) forbidden_phrase
params: {
  phrases: [ "<string>", ... ],
  match_type: "contains"|"regex",
  case_sensitive: false,
  scope: "stage"|"call"
}

c) sequence_rule
params: {
  before_step_id: "<step_id>",       // e.g., verify_identity
  after_step_id: "<step_id>",        // e.g., propose_solution
  allow_equal_timestamps: false,     // if true, same timestamp is acceptable
  message_on_violation: "<string>"   // optional
}

d) timing_rule
params: {
  target: "step"|"phrase",
  target_id_or_phrase: "<step_id or phrase>",
  within_seconds: <number>,          // must occur within X seconds
  reference: "call_start"|"previous_step",
  scope_stage_id: "<stage_id>"       // optional to limit check
}

e) verification_rule
params: {
  verification_step_id: "<step_id>", // which step is defined in FlowVersion as verification
  required_question_count: <int>,    // e.g., 2
  must_complete_before_step_id: "<step_id>", // step before which verification must occur (e.g., any resolution step)
  allow_partial: false               // if true, partial verification may be acceptable (not recommended)
}

f) conditional_rule
params: {
  condition: {                       // minimal condition types supported
    type: "sentiment"|"phrase_mentioned"|"metadata_flag",
    operator: "equals"|"contains",
    value: "<string>"                // e.g., "negative" for sentiment
  },
  required_actions: [
    { action_type: "step_completed", step_id: "<step_id>" },
    { action_type: "phrase_spoken", phrase: "<string>" }
  ],
  failure_severity: "major"|"minor",
  scope_stage_id: "<stage_id>"
}

3 — UI: Compliance Rules Builder (bare-minimum, exact interactions)
Page layout (single column)

Header: FlowVersion selector (read-only if only one active), “Add Rule” button.

List of Rules: title | severity badge | rule_type | quick summary (generated from params) | toggle (active/inactive)

Rule Editor (modal or inline): form fields described above.

Creating a rule (step-by-step)

Click Add Rule.

Enter Title (required).

Enter Description (required).

Select Severity (required).

Select Rule Type (required).

Select Applies to Stages (optional; multiselect; default = call-wide).

Fill params fields (form fields adjust depending on type). Provide helpful tooltips showing example values.

Validate: UI must run client-side checks (see validations) and show human-readable rule preview sentence like:

“Required: agent must say one of ['I confirm your account is recorded'] in Opening stage.”

“Forbidden: Agent must not say phrases matching /we will definitely/ anywhere in call.”

Save → stores rule JSON.

Edit/Delete/Toggle

Edit opens same form prepopulated; delete removes rule after confirmation. Toggle activates/deactivates rule (no deletion required).

4 — Validations (must enforce)
Form validation

title and description non-empty.

severity must be one of allowed values.

rule_type must be selected.

For sequence_rule: both before_step_id and after_step_id must be valid step IDs in the FlowVersion. Block save if referenced step is missing.

For timing_rule: within_seconds must be positive number.

For verification_rule: verification_step_id must be a valid step in FlowVersion.

For required_phrase and forbidden_phrase: each phrase must be non-empty string. Block duplicates.

applies_to_stages entries must be valid stage IDs in FlowVersion.

For conditional_rule: condition.type must be one of supported minimal types; required_actions must be non-empty.

Cross validations

Do not allow a forbidden_phrase that exactly matches a required_phrase for the same stage (warn and block).

If a sequence_rule references steps from different FlowVersions or missing steps → block.

5 — Deterministic semantics (exact behaviors the rule engine will implement)

These semantics must be deterministic and documented for the rule engine implementer.

A. Phrase matching

All phrase matching uses normalized transcription (lowercase, trimmed, collapse whitespace).

match_type = contains → pass if normalized phrase substring found anywhere in the defined scope.

match_type = exact → pass if contiguous token sequence exact match appears.

match_type = regex → pass if regex matches.

For stage scope: only search transcript segments labeled with that stage. For call scope: search entire transcript.

B. Forbidden phrase

If any occurrence found → violation. Severity = rule.severity. Evidence = exact snippet + timestamp + match_type.

C. Required phrase

If no matching occurrence found in scope → violation. Severity = rule.severity. Evidence: expected phrases list.

D. Sequence rule

The engine will find timestamps for occurrences of before_step_id and after_step_id (via step detection based on FlowVersion step expected_phrases or step evidence).

Violation if earliest after timestamp < latest before timestamp (i.e., after occurred before before).

If either step has no evidence → violation (severity per rule or escalate to human review if both missing).

E. Timing rule

Resolve timestamp for target (step occurrence time via step evidence or phrase time).

Violation if (target_time - reference_time) > within_seconds. Reference_time for call_start = 0, for previous_step = timestamp of previous step's evidence.

F. Verification rule

Engine must count KBA questions and mark verification done only if required_question_count questions of expected pattern appear and at least one affirmative answer exists (answer detection can be basic: customer non-empty utterance following question within 10s).

Violation if verification not satisfied before must_complete_before_step_id occurs. Critical severity often used here.

G. Conditional rule

Evaluate condition first. If true, check that at least one required_action occurred in scope_stage_id (or call if none). Violation if absent.

6 — Output JSON contract for a single rule evaluation (how rule engine should return findings)

When the rule engine evaluates a recording, it will produce an array of rule evaluation results; each item:

RuleEvaluation {
  rule_id: "<string>",
  title: "<string>",
  rule_type: "<string>",
  severity: "critical"|"major"|"minor",
  passed: true|false,
  evidence: [
    {
      type: "transcript_snippet"|"timestamp"|"phrase_match"|"step_presence",
      text: "<string>",                // excerpt when applicable
      start_time: <seconds|null>,
      end_time: <seconds|null>,
      match_type: "<contains|exact|regex|null>",
      confidence: <0-1>                 // optional, for fuzzy matching later
    }
  ],
  violation_reason: "<string|null>"   // human readable if failed
}


The final evaluation pipeline aggregates these with SOP step results to produce final score.

7 — Integration usage (how other phases consume rules)
Rule engine (Phase 3)

Input: FlowVersion + recording_transcript + ComplianceRule[]

For each rule in ComplianceRule[] (where active == true and flow_version_id matches), apply deterministic semantics (Section 5) and produce a RuleEvaluation item per rule.

LLM (Phase 4)

LLM receives rule_engine_output.rule_evaluations and must not override critical failures. LLM can use non-critical rule outcomes as context for stage feedback.

Rubric scoring (Phase 5)

Compliance violations map to penalties or auto-fail. If any critical rule failed → overall fail (unless policy explicitly differs; keep default auto-fail behavior).

8 — UI preview wording (human-friendly sentence generator)

For each saved rule, show a one-line preview that exactly explains deterministic enforcement; examples:

Required phrase: “Agent must speak one of: ‘I confirm your account…’ within Opening stage.”

Forbidden phrase: “Agent must not say: ‘I guarantee’ anywhere in call.”

Sequence rule: “Agent must perform step verify_identity before step propose_solution.”

Timing rule: “Agent must greet within 10 seconds of call start.”

Verification rule: “Agent must ask 2 KBA questions and record an answer before resolving.”

Conditional rule: “If customer sentiment is negative, agent must apologize before resolving.”

This is just UI text; it must map 1:1 to the deterministic semantics.

9 — Acceptance tests (explicit, must pass)

Test 1 — Required phrase success

Rule: required_phrase { phrases: ["this call is recorded"], scope: "call" }

Transcript contains “This call is recorded…” → RuleEvaluation.passed == true; evidence contains snippet and timestamp.

Test 2 — Required phrase failure

Transcript lacks phrase → passed == false; violation_reason explains phrase missing.

Test 3 — Forbidden phrase detection

Rule: forbidden_phrase ["we will definitely"]

Transcript contains “we will definitely” → passed == false; evidence snippet present.

Test 4 — Sequence rule

FlowVersion steps: verify_identity (step_v), propose_solution (step_p)

Transcript has propose_solution at t=20s, verify_identity at t=30s → sequence_rule fails; evidence shows both timestamps.

Test 5 — Timing rule

Timing rule: greet within 5s of call_start

Greeting detected at 8s → violation

Test 6 — Verification rule

verification_rule requires 2 questions before propose_solution step. Transcript has only 1 question before propose_solution → violation.

Test 7 — Conditional rule

Condition: sentiment == negative. Transcript sentiment negative and agent did not apologize → violation.

Test 8 — Scope validation

Rule references non-existent step id → UI blocks save with clear error.

10 — Edge cases & minimal fallback behavior

Low transcription confidence: if transcript confidence < configured threshold (system default 0.4), mark rule checks as inconclusive (passed = false, but violation_reason = "transcript low confidence — human review recommended"). Do not auto-fail critical unless explicit evidence of violation exists. (This is a minimal safety net; implement only if transcription metadata available.)

Ambiguous phrase matches: use exact/contains/regex only. No fuzzy matching in minimal version. If uncertain, treat as missing.

Multiple matches: if phrase occurs multiple times, choose earliest occurrence for timing/sequence checks.

11 — Minimal persistence & API contracts (conceptual)

Storage: Compliance rules stored as part of the policy data linked to flow_version_id. Keep simple CRUD operations:

GET /policy/{id}/flow/{flow_version}/compliance-rules → returns array of ComplianceRule JSON objects.

POST /policy/{id}/flow/{flow_version}/compliance-rules → create rule.

PUT /.../{rule_id} → update rule.

DELETE .../{rule_id} → remove.

Rule Engine consumption: a single endpoint or internal method will accept FlowVersion + ComplianceRule[] + transcript and return array of RuleEvaluation JSON objects.

12 — Example rule objects (concrete)

Example A — Recording disclosure (required_phrase)

{
  id: "r_001",
  flow_version_id: "fv_001",
  title: "Recording disclosure",
  description: "Agent must inform customer that call is recorded in Opening stage",
  severity: "critical",
  rule_type: "required_phrase",
  applies_to_stages: ["stage_open"],
  params: {
    phrases: ["this call is being recorded", "this call is recorded"],
    match_type: "contains",
    case_sensitive: false,
    scope: "stage"
  },
  active: true
}


Example B — No guarantees (forbidden_phrase)

{
  id: "r_002",
  flow_version_id: "fv_001",
  title: "No guarantees",
  description: "Agent must not make promises beyond policy",
  severity: "major",
  rule_type: "forbidden_phrase",
  applies_to_stages: [],
  params: {
    phrases: ["I guarantee", "I promise you will get"],
    match_type: "contains",
    case_sensitive: false,
    scope: "call"
  },
  active: true
}


Example C — Verify before solution (sequence_rule)

{
  id: "r_003",
  flow_version_id: "fv_001",
  title: "Verify before solution",
  description: "Identity verification must happen before any solution",
  severity: "critical",
  rule_type: "sequence_rule",
  applies_to_stages: ["stage_open","stage_discovery"],
  params: {
    before_step_id: "step_verify_identity",
    after_step_id: "step_propose_solution",
    allow_equal_timestamps: false
  },
  active: true
}

13 — Acceptance checklist (deliverables)

 Compliance Rules Builder UI implemented (create/edit/delete/toggle).

 Client-side validations implemented and blocking where required.

 Rules persist to storage with exact JSON schema.

 Rule preview sentence generated correctly.

 Rule Engine consumption contract documented and tested locally.

 All acceptance tests (Section 9) pass.

 Minimal fallback for low transcription confidence implemented (optional but recommended).

14 — Purpose & usage recap (one-liners)

Purpose: enforce mandatory behaviors and auto-fails deterministically.

Usage: Author defines rules in the UI (tied to FlowVersion). On evaluation, the rule engine deterministically checks the transcript and returns rule results that feed scoring and LLM.

Outcome: clear violations (with evidence) that can auto-fail or reduce score.