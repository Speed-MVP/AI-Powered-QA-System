PHASE 5 — RUBRIC SCORING ENGINE (BARE-MINIMUM, COMPLETE SPEC)

This phase converts LLM stage evaluations + rubric categories into:

Category scores

Overall score

Pass/fail per category

Final evaluation JSON consumed by frontend UI

This is the final scoring brain of your QA system.

This spec has zero fluff, no extra features, and everything your AI coder needs to implement it without guessing.

0 — PURPOSE OF PHASE 5

Transform structured stage scores into:

Category scores (e.g., Communication, Accuracy, Resolution).

Overall weighted score.

Pass/fail based on category passing thresholds.

Final evaluation object ready for storage.

This phase does not generate feedback — feedback is already provided by Phase 4 LLM.

This phase does not re-evaluate rules or steps — it only aggregates.

1 — INPUTS REQUIRED BY PHASE 5

Phase 5 consumes three inputs:

Input A — RubricTemplate (from criteria page)

For minimal implementation, each category contains:

RubricTemplate {
  categories: [
    {
      id: "<category_id>",
      name: "<string>",                 // e.g. "Communication"
      weight: <number>,                 // e.g. 25
      pass_threshold: <number>,         // e.g. 75
      stage_ids: [ "<stage_id>", ... ]  // mapped stages from FlowVersion
    }
  ]
}


Weight sum must equal 100.

Input B — LLM Stage Evaluations (from Phase 4)

Phase 4 output for all stages:

llm_stage_evaluations = {
  "<stage_id>": {
    stage_score: <0-100>,
    stage_confidence: <0-1>,
    critical_violation: true|false
  }
}

Input C — DeterministicResult (Phase 3)

Needed only to enforce the rule:

If deterministic critical violation exists anywhere → auto-fail overall.

DeterministicResult {
  rule_evaluations: [ ... ],
  stage_results: { ... },
  deterministic_score: <0-100>,
  overall_passed: true|false
}

2 — OUTPUT OF PHASE 5
FinalEvaluation {
  overall_score: <0-100>,
  category_scores: [
    {
      category_id: "<id>",
      name: "<string>",
      weight: <number>,
      score: <0-100>,
      passed: true|false
    }
  ],
  stage_scores: {
    <stage_id>: {
      score: <0-100>,
      critical_violation: true|false,
      confidence: <0-1>
    }
  },
  overall_passed: true|false
}


This is the final object stored in DB and returned to frontend.

3 — CATEGORY SCORING — ALGORITHMIC RULES (MANDATORY)
3.1 Category score formula (exact)

A category score is the simple average of all mapped stage scores:

category_score = average( stage_score[stage_id] for each stage_id in category.stage_ids )


If a category has only one stage → category_score = that stage_score.

If a stage defined in category.stage_ids does not exist in LLM output → treat missing stage as score = 0 (explicit fail; missing stage means incomplete evaluation).

3.2 Score rounding

Round category_score to nearest integer.

4 — CATEGORY PASSING RULES
For each category:
passed = (category_score >= pass_threshold)


pass_threshold is defined in the UI (e.g., 75).

5 — OVERALL SCORE (WEIGHTED)

After computing all category scores:

overall_score =
  sum( category_score * (category.weight / 100) )


Round to nearest integer.

6 — OVERALL PASS/FAIL LOGIC
6.1 Fail if deterministic critical violation

If DeterministicResult.rule_evaluations contains:

severity="critical" AND passed=false


→ overall_passed = false
→ overall_score = overall_score (do not change, but result is fail)

6.2 Otherwise evaluate category-level pass

If any category fails:

(category.pass == false)


→ overall_passed = false

Else → overall_passed = true.

7 — HANDLING LOW CONFIDENCE STAGE SCORES

If any stage has:

stage_confidence < 0.50


Mark evaluation with flag:

requires_human_review = true


This is NOT part of the scoring — it doesn’t fail the score.
It only flags the evaluation.

8 — EDGE CASE RULES (MANDATORY)
8.1 Stage missing in LLM output

If a stage is missing entirely:

stage_score = 0

flagged in final output

this will negatively impact mapped category

8.2 Category mapped to empty stage list

Block at template creation. (Handled in Phase 1–2 UI but must validate here too.)

8.3 Negative scores

Clamp after penalties and rounding:

if score < 0: score = 0
if score > 100: score = 100

8.4 Stage with critical violation

If:

llm_stage_evaluations[stage_id].critical_violation == true


Then:

stage_score = stage_score (keep it)

but overall_passed = false

8.5 Missing rubric template

If category list empty or no rubric template exists:

Fallback: overall_score = deterministic_score

overall_passed = deterministic_result.overall_passed

Set requires_human_review = true

Reason: “Missing rubric.”

9 — FULL SCORING EXAMPLE
Inputs:
RubricTemplate
Communication — 30% — threshold 75 → stages [Opening]  
Resolution — 40% — threshold 80 → stages [Resolution]  
Process Adherence — 30% — threshold 70 → stages [Discovery]

LLM stage scores:
Opening: 80  
Discovery: 60  
Resolution: 85

Category Scores:

Communication = 80

Process Adherence = 60

Resolution = 85

Category pass:

Communication: pass

Process: fail (60 < 70)

Resolution: pass

Overall score:
(80 * 0.30) + (60 * 0.30) + (85 * 0.40)
= 24 + 18 + 34
= 76

overall_passed:

Fail (because Process category failed)

10 — ACCEPTANCE TESTS (must pass)
Test 1 — Weight sum 100

Rubric with 95 or 105 total weight must cause validation error.

Test 2 — Category score average

Stages:

s1=70, s2=90 → category score = 80

Test 3 — Missing stage = score 0

If LLM skips a stage:

category_score = average( existing scores + 0 )

Test 4 — Overall weighted scoring

Given:

category A: 80 (50%)

category B: 60 (50%)
→ overall = 70

Test 5 — Threshold enforcement

If category_score < pass_threshold → category fails.

Test 6 — Deterministic auto-fail

If Phase 3 has a critical violation → overall_passed=false, regardless of weighted score.

Test 7 — Confidence flag

If any stage_confidence < 0.5 → requires_human_review=true.

Test 8 — JSON output format

Final evaluation must match exact schema in Section 2.

11 — FINAL PHASE OUTPUT (FULL OBJECT)
{
  "overall_score": <0-100>,
  "overall_passed": true|false,
  "category_scores": [
    { "category_id":"c1","name":"Communication","weight":30,"score":82,"passed":true },
    { "category_id":"c2","name":"Accuracy","weight":40,"score":75,"passed":true },
    { "category_id":"c3","name":"Resolution","weight":30,"score":60,"passed":false }
  ],
  "stage_scores": {
    "stage_opening": { "score": 82, "critical_violation": false, "confidence": 0.98 },
    "stage_discovery": { "score": 60, "critical_violation": false, "confidence": 0.70 },
    "stage_resolution": { "score": 85, "critical_violation": false, "confidence": 0.92 }
  },
  "requires_human_review": false
}

12 — PURPOSE (BLUNT SUMMARY)

Phase 5 is needed because:

It converts per-stage scores → category scores → final score

It applies weights

It applies pass thresholds

It enforces auto-fail for compliance

It produces the final result that you show to customers

It guarantees consistent, repeatable, non-AI scoring

Without Phase 5, the whole evaluation system has no final scoring logic.