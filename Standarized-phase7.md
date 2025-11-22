PHASE 6 — FINAL EVALUATION PIPELINE (BARE-MINIMUM, COMPLETE IMPLEMENTATION SPEC)

This phase connects everything:
Audio upload → transcription → deterministic engine → LLM stage evaluation → rubric scoring → final evaluation result.

This is the end-to-end pipeline your whole product depends on.

This version contains only the minimal features you actually need, with exact flow, API contracts, JSON structures, failure handling, and required logic.

Your AI coder can implement this with zero guesswork.

0 — PURPOSE OF PHASE 6

Turn an uploaded audio file into a completed evaluation object by chaining:

Transcription

Deterministic Rule Engine (Phase 3)

LLM Stage Evaluation (Phase 4)

Rubric Scoring (Phase 5)

Final evaluation storage

No extra features.
No analytics.
No version selectors.
No coaching.

Just: Upload → Evaluate → Return Score.

1 — INPUTS & REQUIRED COMPONENTS
Components required:

FlowVersion (from Phase 1)

ComplianceRule[] (from Phase 2)

Deterministic Rule Engine (Phase 3)

LLM Stage Evaluator (Phase 4)

Rubric Scoring Engine (Phase 5)

Transcription Service (Deepgram, Whisper, etc.)

Input from user:

uploaded audio file (wav/mp3)

Input from database:

active FlowVersion for company

all ComplianceRule for that FlowVersion

RubricTemplate for that FlowVersion

2 — HIGH-LEVEL PIPELINE FLOW (MUST FOLLOW EXACT ORDER)
AUDIO → TRANSCRIPT → DETERMINISTIC ENGINE → LLM (per stage)
→ COMBINE → RUBRIC SCORER → FINAL EVALUATION → RETURN JSON


Exactly in that order. No shortcuts.

3 — STEP-BY-STEP DETAILED PIPELINE
STEP 1 — Audio Upload

Frontend uploads audio via:

POST /api/recordings/upload


Backend stores file (GCP, S3, etc.) and creates:

Recording {
  id,
  company_id,
  file_url,
  status: "queued"
}


Then queues background evaluation job:

evaluate_recording(recording_id)

STEP 2 — Transcription

Backend fetches the file, sends to transcription service, receives:

Transcript {
  transcript_text: "<full text>",
  segments: [
    {
      speaker: "agent"|"customer",
      text: "<string>",
      start_time: <seconds>,
      end_time: <seconds>
    }
  ],
  confidence: <0-1>
}


Store in DB.

If transcription fails:

Set eval status = failed

Return error to UI

Stop pipeline.

STEP 3 — Load Active Policy Components

Determine which policy to use:

flow_version = FlowVersion.active(company_id)
rules = ComplianceRules.where(flow_version_id)
rubric = RubricTemplate.active(flow_version_id)


IF ANY OF THESE ARE MISSING → fail evaluation:

requires_human_review = true
overall_score = 0
error = "Missing policy"

STEP 4 — Deterministic Rule Engine (Phase 3)

Call:

deterministic = run_deterministic_engine(
    flow_version,
    rules,
    transcript
)


Expect output:

DeterministicResult {
  stage_results: { ... },
  rule_evaluations: [ ... ],
  deterministic_score: <0-100>,
  overall_passed: boolean
}


If engine crashes →
evaluation is marked failed → requires human review.

STEP 5 — LLM Stage Evaluation (Phase 4)
Split evaluation per stage

For each stage in FlowVersion:

llm_stage_eval[stage_id] = call_llm_stage_evaluator(
    stage_id,
    stage_segments,
    deterministic.stage_results[stage_id],
    deterministic.rule_evaluations,
    flow_version.stages[stage_id],
    rubric.category_mapping_for_stage(stage_id),
    transcript
)

LLM stage evaluator returns:
{
  evaluation_id,
  stage_id,
  stage_score: <0-100>,
  step_evaluations: [...],
  stage_feedback: [...],
  stage_confidence: <0-1>,
  critical_violation: true|false
}


If LLM returns invalid JSON →
fallback to:

LLMFallbackStage {
  stage_score = deterministic_score or 0
  stage_confidence = 0.5
  critical_violation = deterministic has critical
  note = "LLM failed — deterministic fallback"
}


And mark:

requires_human_review = true

STEP 6 — Combine LLM stage evaluations

Assemble:

stage_scores = {
  stage_id: {
    score: stage_score,
    confidence: stage_confidence,
    critical_violation
  }
}


Persist this intermediate result.

STEP 7 — Rubric Scoring Engine (Phase 5)

Call:

final_scores = rubric_scorer(
    rubric,
    stage_scores,
    deterministic
)


Rubric engine returns:

{
  overall_score: <int>,
  overall_passed: true|false,
  category_scores: [
    { id, name, weight, score, passed }
  ],
  stage_scores: { stage_id: { score, confidence, critical_violation } },
  requires_human_review: true|false
}


Critical rule failures override everything (fail automatically).

STEP 8 — Final Evaluation Assembly

Create:

Evaluation {
  id,
  recording_id,
  flow_version_id,
  rubric_id,
  overall_score,
  overall_passed,
  category_scores,
  stage_scores,
  rule_evaluations,
  deterministic_score,
  llm_stage_evaluations,
  requires_human_review,
  transcript_text,
  created_at,
}


Store to DB.

STEP 9 — Mark Recording as Completed
recording.status = "completed"
recording.processed_at = now()


Return to frontend:

{
  evaluation_id,
  overall_score,
  passed,
  category_scores,
  stage_scores,
  violations: deterministic.rule_evaluations,
  step_results: deterministic.stage_results,
  llm: llm_stage_evaluations
}


This is what frontend displays.

4 — FAILURE HANDLING RULES (MANDATORY)
TYPE A — Hard failures

If ANY of these happen:

No FlowVersion found

No RubricTemplate found

Deterministic engine crashed

Transcription failed

Database error

→ evaluation_status = failed
→ requires_human_review = true
→ overall_score = 0
→ overall_passed = false

TYPE B — LLM failure

If:

invalid JSON

low confidence

missing required fields

hallucinated rule IDs

Use deterministic fallback for that stage.
Flag:

requires_human_review = true

TYPE C — Critical compliance violation

If deterministic.result contains a critical fail:

LLM may NOT overturn it

Category scores still computed

But overall_passed = false

5 — API CONTRACTS (BACKEND INBOUND/OUTBOUND)
POST /api/recordings/upload

Uploads audio, returns recording_id.

POST /api/recordings/{id}/evaluate

Internal job triggered automatically.

GET /api/evaluations/{id}

Returns FinalEvaluation object:

{
  evaluation_id,
  overall_score,
  overall_passed,
  requires_human_review,
  category_scores,
  stage_scores,
  rule_violations,
  transcript,
}

6 — PERFORMANCE REQUIREMENTS (REALISTIC MINIMUM)
Parallelizable:

LLM per stage ⇒ run them in parallel

Deterministic engine is cheap ⇒ CPU only

Time expectations:

Transcription: 2–6 seconds

Deterministic: < 0.2 seconds

LLM per stage: 1–3 seconds

Rubric scoring: < 0.1 seconds

Total expected: 3–12 seconds per evaluation.

7 — ACCEPTANCE CRITERIA FOR PHASE 6
Must pass 100%:

 Audio upload → evaluation returns valid JSON

 Deterministic engine always runs before LLM

 LLM outputs are validated using strict schema

 Fallback logic works

 Rubric scoring produces correct total

 Critical rule fails auto-fail whole evaluation

 All JSON fields match contract

 Evaluation stored in DB correctly

 Recording status moves queued → processing → completed

 Evaluations always reference FlowVersion + RubricTemplate used

8 — BLUNT SUMMARY

Phase 6 makes your entire system work end-to-end.
This spec provides:

Exact order of operations

Exact data flow

Exact JSON structures

Exact fallbacks

Exact pass/fail rules

Required integrations

Expected outputs

Zero extra features

This is the minimal product, fully functional and production-capable.