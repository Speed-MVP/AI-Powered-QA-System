PHASE 3 — DETERMINISTIC RULE ENGINE (BARE-MINIMUM, FULL SPEC)

This is the most critical part of your entire QA system.
Below is the fully detailed, no extra features, minimal but production-viable deterministic rule engine spec — exactly what your AI coder needs to build with zero guesswork.

This phase consumes:

FlowVersion (from Phase 1)

ComplianceRule[] (from Phase 2)

Transcript + diarized segments + timestamps

And outputs deterministic evidence that later phases (LLM, scoring) will use.

0 — GOAL OF THIS PHASE

Implement a deterministic engine that performs all non-AI checks:

Detect each step (via expected phrases).

Check required steps.

Check step order.

Detect step timestamps.

Check compliance rules (required phrase, forbidden phrase, timing, sequence, verification, conditional).

Produce pure JSON results (no free text).

Feed the results into the LLM (Phase 4) and scoring (Phase 5).

1 — INPUT CONTRACT
Input A: FlowVersion

Generated from Phase 1:

FlowVersion {
  id,
  stages: [
    {
      id,
      name,
      order,
      steps: [
        {
          id,
          name,
          required,
          expected_phrases: [],
          timing_requirement: { enabled, seconds },
          order
        }
      ]
    }
  ]
}

Input B: ComplianceRule[]

Generated from Phase 2.

Input C: Transcript Data

Must include:

transcript_text: "<full text>"
segments: [
  {
    speaker: "agent" | "customer",
    text: "<string>",
    start_time: <seconds>,
    end_time: <seconds>
  }
]

Input D: Call metadata

call_start = 0 seconds

transcription_confidence (optional)

2 — OUTPUT CONTRACT (This must be exactly followed)

The rule engine returns:

DeterministicResult {
  stage_results: {
    <stage_id>: {
      step_results: [
        {
          step_id,
          passed,
          detected,
          timestamp,      // earliest match timestamp or null
          evidence: [
            {
              text,
              start_time,
              end_time
            }
          ],
          reason_if_failed: "<string|null>"
        }
      ],
      order_violations: [ "<step_id> appeared before <step_id>" ],
      timing_violations: [ "<step_id> exceeded <seconds>s requirement" ]
    }
  },
  rule_evaluations: [
    {
      rule_id,
      title,
      rule_type,
      severity,
      passed,
      evidence: [ { text, start_time } ],
      violation_reason: "<string|null>"
    }
  ],
  deterministic_score,         // optional minimal score (0–100)
  overall_passed               // boolean (all critical rules passed)
}


This result must be 100% deterministic, reproducible, and stable.

3 — STEP DETECTION LOGIC (MANDATORY)

This determines where in the transcript a step happened.

3.1 Step detection method

For each step:

Loop through transcript segments where speaker="agent".

Normalize text (lowercase, remove punctuation except apostrophes, collapse whitespace).

For each expected phrase in step.expected_phrases:

Normalize phrase the same way.

Check if phrase occurs in segment text.

If yes → record:

matched text snippet

timestamp = segment.start_time

evidence snippet

3.2 Step detection result

A step is detected if:

At least one expected phrase matched
OR

expected_phrases is empty → treat step as undetectable except required status (see below)

3.3 If step.expected_phrases is empty

Mark detected = false

Rule engine cannot detect it deterministically → LLM handles it later

If step.required = true → deterministic_failed = true (unless LLM overrides: depends on Phase 4 policy)

3.4 Multiple matches

Keep earliest match timestamp for order & timing checks

Keep all evidence snippets for debugging

4 — STEP ORDER CHECKING

You must enforce the stage & step flow as defined in Phase 1.

4.1 Stage order checking

Stages must appear in increasing stage.order.

Algorithm:

For each detected step, record step timestamp.

Determine stage index thresholds:

if step from stage 2 detected before any step in stage 1 → violation

Add violation:

order_violations: ["step Greet (stage_open) appeared after step AskQuestions (stage_discovery)"]

4.2 Step order checking inside stages

Within a stage:

Steps must follow order defined in step.order.

If step with order 3 is detected at time 120s, but step order 1 detected at 140s → violation.

Violations are added to the stage's order_violations.

5 — TIMING REQUIREMENTS (From Phase 1)

For any step that has:

timing_requirement: { enabled: true, seconds: X }


Check:

timestamp(step) - call_start <= X


If timestamp missing or > X:

timing_violations: ["Greeting must occur within 10s"]

6 — COMPLIANCE RULE CHECKING (From Phase 2)

Each rule type has exact deterministic semantics.

6.1 required_phrase

Search transcript for any of the phrases.

If found → passed = true.

If not → passed = false, violation.

6.2 forbidden_phrase

If phrase found anywhere → violation.

6.3 sequence_rule

Fail when:

timestamp(after_step) < timestamp(before_step)


If either step has no timestamp → rule fails (missing mandatory action).

6.4 timing_rule

Fail when:

timestamp(target_action) - reference_time > within_seconds


timestamp(target_action) = earliest time phrase or step detected
reference_time:

call_start always 0

or timestamp(previous_step)

6.5 verification_rule

Rule fails if:

Less than required number of verification questions detected

Or verification step appears after resolution step

Or verification evidence missing before must_complete_before_step_id

6.6 conditional_rule

If condition true → required_actions must be detected
If not detected → violation.

7 — DETERMINISTIC SCORING (BARE-MINIMUM)
7.1 When to auto-fail

If any critical rule fails → deterministic_score = 0.

7.2 Minimal scoring formula

Optional but recommended:

total_required_steps = count(required steps)
completed_required_steps = count(required steps detected)

step_score = (completed_required_steps / total_required_steps) * 100
rule_score = (#passed_compliance_rules / #total_compliance_rules) * 100

deterministic_score = (step_score * 0.7) + (rule_score * 0.3)

7.3 Final deterministic output for this phase

deterministic_score

list of violations

stage step breakdown

critical_pass (true/false)

This is fed to LLM.

8 — EXAMPLE OUTPUT (FULL EXAMPLE)
{
  "stage_results": {
    "stage_open": {
      "step_results": [
        {
          "step_id": "step_greet",
          "passed": true,
          "detected": true,
          "timestamp": 4.2,
          "evidence": [
            { "text": "good morning thanks for calling", "start_time": 4.2 }
          ],
          "reason_if_failed": null
        },
        {
          "step_id": "step_verify_identity",
          "passed": false,
          "detected": false,
          "timestamp": null,
          "evidence": [],
          "reason_if_failed": "required_step_missing"
        }
      ],
      "order_violations": [],
      "timing_violations": []
    }
  },
  "rule_evaluations": [
    {
      "rule_id": "r_001",
      "title": "Recording disclosure",
      "rule_type": "required_phrase",
      "severity": "critical",
      "passed": false,
      "evidence": [],
      "violation_reason": "Required phrase not found"
    }
  ],
  "deterministic_score": 52,
  "overall_passed": false
}

9 — ACCEPTANCE CRITERIA FOR PHASE 3
Deterministic engine must:

 Detect steps via expected phrases

 Produce earliest timestamps

 Enforce stage order

 Enforce step order

 Enforce timing requirements

 Enforce all compliance rule types

 Produce RuleEvaluation JSON

 Produce deterministic_score

 Handle missing detection cleanly

 Never contradict its own rules

 Guarantee consistent outputs for the same transcript

Everything must be:

deterministic

reproducible

free from randomness

consistent across evaluations

10 — PURPOSE OF PHASE 3
This phase ensures:

HARD RULES are enforced by logic, not by AI.

LLM cannot bypass compliance requirements.

The evaluation has structure → based on SOP steps.

Every violation has timestamped evidence.

Scoring becomes fair and repeatable.

Phase 3 is what makes your entire QA system reliable.