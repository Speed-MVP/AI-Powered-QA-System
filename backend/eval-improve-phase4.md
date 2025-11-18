PHASE 4 — Deterministic LLM Evaluator (Rubric-Level Classifier Only)
Goal: Reduce the LLM’s job to ONE role — choose the correct RUBRIC LEVEL per category based on deterministic rule outputs + transcript evidence.

Phase 4 is the stage where the massive 3,000-token policy prompt becomes obsolete.

The LLM now behaves like:

A classification model

Not a reasoning agent

Not a policy interpreter

Not a rule detector

Not a tone guesser

Not a moral judge

Rubric classification is the only task left.

1. Core Purpose of Phase 4

Phase 4 transforms the LLM from:

“interpret policy, analyze tone, detect violations, infer rules, apply rubric, guess scoring”

into:

“Given the rule engine results, choose the correct rubric level.”

The LLM no longer makes ANY compliance OR rule decisions.

LLM output ceases to be “creative.”
It becomes strict and deterministic.

2. Inputs to the Phase 4 LLM

After Phase 3, the LLM receives only four inputs:

A. Rule Engine Summary

This includes:

Passed/failed rules

Severity

Evidence snippets

Category links

This tells the LLM “what happened” in the call.

NOT “what the policy is.”
NOT “what the rule means.”
NOT “what the company expects.”

Just the results.

B. Category Rubric Levels

Each category has:

Level name (Excellent, Good, Average, Poor, Unacceptable)

Level description

Score range

LLM must map actual performance → rubric description.

C. Transcript Summary (Highly Compressed)

LLM does NOT read full transcript anymore.

Only receives:

Key utterances

Key events

Key customer emotion transitions

Key agent behaviors

This is purely for nuance (tone, communication quality).

Transcript is pre-processed to remove irrelevant lines.

D. Tone Mismatch Indicators (Pre-Computed)

Rule engine V2 computes tone anomalies:

Examples:

monotone baseline: normal (ignore)

empathy phrase + neutral tone: mismatch

apology with annoyed tone: mismatch

LLM cannot detect tone independently.
LLM only reads tone flags, not voice data.

3. What the LLM Must Do Now

Phase 4 reduces the LLM’s responsibilities to THREE operations:

Operation 1 — Choose Rubric Level Per Category

For each category (Professionalism, Empathy, Resolution):

LLM must choose ONE level:

Excellent

Good

Average

Poor

Unacceptable

Based on:

Severity of violations

Frequency of violations

Tonal issues

Customer emotional trajectory

Resolution quality

LLM does not think about “rules” at all.
It only reviews how many and how severe they were.

Operation 2 — Provide Rubric-Level Feedback

Feedback must:

reference only rule results + transcript summary

be blunt, direct, factual

match the selected rubric level

avoid excuses, interpretations, or imagination

Feedback is no longer narrative-heavy.

Example:

“Greeting was late (18s). Rule requires ≤15s. Professionalism lowered to Average.”

“Empathy insufficient during high-intensity customer frustration (segment 3).”

No fluff.
No soft analysis.

Operation 3 — Produce a Stable JSON Output (No Creativity)

The JSON is consistent because:

LLM outputs only allowed categories

Output is tightly schema-constrained

No extra fields allowed

No category drift

LLM simply fills in:

rubric level

numeric score (mapped by backend later)

feedback

4. What the LLM is Explicitly FORBIDDEN From Doing in Phase 4

This is critical.

LLM must NOT:

❌ Interpret Policies

Policies are no longer provided.
LLM should never see them again.

❌ Guess Rules

LLM uses only structured rule results.
It cannot guess missing rule logic.

❌ Detect Rule Violations

Rule engine V2 handles all violations.

❌ Perform Tone Detection

LLM receives tone mismatch flags.
It cannot analyze audio.

❌ Infer Intent

LLM cannot say: “Agent seems annoyed.”
It may only reference mismatch flags.

❌ Invent Categories

No more category drift.
Allowed categories are explicitly provided.

❌ Output narrative paragraphs

Only short rubric-based feedback.

5. Required NLP Transformations Before LLM Input

To guarantee determinism, you must pre-process everything.

Phase 4 requires defining these transformations:

A. Transcript Compression

Collapse transcript to:

key statements

agent-customer conflict points

escalation requests

apology moments

resolution summary

B. Emotion Summary

Customer tone changes must be summarized into:

start → middle → end

Not raw sentiment data.

C. Tone Mismatch Summary

Only flags like:

“major mismatch at 35s (insincerity)”

“minor mismatch at 12s (flat tone)”

D. Rule Violation Summary

Summarized by category so LLM sees a clean input.

This ensures the LLM gets ONLY what it needs.

6. Evaluation Logic After Phase 4

The new evaluation pipeline becomes:

1. Transcription (Deepgram)

↓

2. Voice baseline analysis

↓

3. Rule Engine V2

↓

4. Extract summary datasets

↓

5. LLM selects rubric levels ONLY

↓

6. Backend maps rubric → numeric score

↓

7. Apply rule penalties

↓

8. Final evaluation produced

This pipeline is deterministic from start to end.

7. Expected Behavior After Phase 4

When Phase 4 is complete, you get:

1. No more 350-line prompts

Your new prompt will be:

short

highly structured

no redundant guidelines

no extended instructions

no company policy text

2. 90%+ reduction in LLM randomness

The LLM only picks a rubric level from a fixed list.
Very little generative variability left.

3. Perfect consistency across repeated evaluations

Because:

rule violations are fixed

tone flags are fixed

transcript summary is deterministic

rubric descriptions are fixed

4. Clarity in debugging

If agent scores are off:

You look at rule results → deterministic

You look at rubric selection → fixed options

You can immediately find where mismatch occurred

5. Scores become auditor-friendly

Human QA auditors will see:

rules

evidence

rubric level

score

No arbitrary LLM interpretation.

8. What Phase 4 Does NOT Include

No UI changes

No structured rule editor

No human review redesign

No new scoring visualization

No customer-facing feature changes

Phase 4 is purely about:

a new LLM role

new prompts

new input data format

new evaluator architecture

UI and editor improvements are in Phase 5.

9. Result After Phase 4 — Your LLM is Now a “Rubric Selector”

When Phase 4 is done, the LLM becomes extremely simple:

**It does ONE job:

Pick the correct rubric level for each category.**

Everything else is handled:

deterministically

predictably

consistently

This eliminates LLM overthinking, interpretation, and randomness.

Final Summary — Phase 4

Phase 4 transforms the LLM into a deterministic rubric classifier.

It gets:

rule results

compressed transcript evidence

tone mismatch flags

rubric levels

It produces:

final rubric level per category

short feedback

structured JSON

It NEVER:

interprets policy

interprets rules

analyzes audio

guesses tone

guesses intent

creates penalties

invents categories

This is the phase that makes your QA system stable, predictable, and scalable.