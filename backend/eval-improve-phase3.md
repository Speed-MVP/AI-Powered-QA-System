PHASE 3 — RULE ENGINE V2 (Policy-Based Deterministic Evaluation)
Goal: Replace the LLM’s “rule interpretation” with a fully deterministic, structured-rule execution engine that evaluates calls BEFORE the LLM is even involved.

Phase 3 is where your QA system becomes a hybrid deterministic-AI engine.
This phase makes your evaluations stable and consistent by moving all rule logic into a pure rule engine.

1. Core Purpose of Phase 3

Up to Phase 2, companies have machine-readable rules.

Phase 3 makes the system execute those rules against real call data.

This means:

Detecting violations automatically

Gathering evidence

Linking violations to categories

Applying severities

Preparing results for scoring

Providing consistent outputs for every evaluation

From this point forward:
LLM NO LONGER DECIDES RULE VIOLATIONS. EVER.

2. Inputs to the Rule Engine V2

Rule Engine V2 must accept the following data sources:

A. Structured policy rules from Phase 2

Example rule types the engine must understand:

Time thresholds

Required phrases

Forbidden phrases

Boolean required behaviors

Conditional rules

Multi-step rules

Empathy requirements

Resolution completeness rules

Silence/timing-based constraints

Actions (hold, escalate, verify)

B. Transcript

Full normalized transcript

Utterances

Speaker identification

C. Timing metadata

Timestamps for every utterance

Silence durations

Time between customer statements and agent responses

D. Voice sentiment + baselines

Agent’s voice tone

Caller’s voice tone

Baseline profiles

Segment-level sentiment

E. Rule parameters

Severity

Category links

Evidence requirements

3. What Rule Engine V2 Must Do

This engine must apply every structured rule deterministically with no interpretation or guesswork.

3.1 Evaluate every rule logically

Each rule is executed EXACTLY as defined:

If rule says “Greeting must occur within 15 seconds,” check timestamp difference.

If rule says “Must apologize when customer is angry,” check both:

customer sentiment segments

apology phrases

3.2 Detect violations consistently

The engine must output:

If rule was passed or failed

Why

Evidence (timestamps, quotes, segments)

Severity (minor, moderate, major, critical)

Which category this impacts

**3.3 Never guess

Never interpret
Never infer intention**

The rule engine is pure logic:

string matching

time comparisons

conditional branch logic

sentiment threshold checks

No AI reasoning here.

4. Rule Engine V2 Must Produce the Following Outputs

Phase 3 defines a standard output contract that the scoring engine and LLM will depend on.

The output should always contain:

A. Rule-by-rule evaluation

For every structured rule:

rule_id

rule_name

passed/failed

severity

evidence

category

B. A summary of all violations

Grouped by category:

Professionalism → [violations]

Empathy → [violations]

Resolution → [violations]

C. Rule score penalties

Each rule has a defined penalty or mapping to a lower rubric level.

Rule Engine must calculate:

penalty per rule

total penalty per category

rule impact severity

D. Execution metadata

total rules checked

total passed

total failed

time taken

E. Structured “ready for LLM” output

A clean, simplified dataset so that the LLM never sees raw transcript or policy text.

5. Rule Types Rule Engine V2 Must Support

Phase 3 requires defining which rule families your engine supports, even if implementation comes later.

Here are the mandatory rule types:

Type 1: Timing Rules

Examples:

Greeting must occur within X seconds

Must provide escalation within Y seconds after unresolved issue

Silence cannot exceed Z seconds

What the engine checks:

Timestamp deltas

Silence segments

Response speed

Type 2: Required Phrase Rules

Examples:

Must apologize: “sorry”, “I apologize”

Must greet: “thank you for calling”

Engine checks:

Phrase existence

Multiple variations

Exact match or fuzzy match

Type 3: Forbidden Phrase Rules

Examples:

Cannot say: “I can’t do anything”

Cannot use sarcasm phrases

Engine checks:

Phrase match

Severity escalation

Type 4: Boolean Rules

Examples:

Must verify customer identity

Must ask “is there anything else?”

Engine checks:

Boolean yes/no

With evidence timestamp

Type 5: Conditional Rules

Examples:

If customer is angry → empathy required

If customer asks for supervisor → must offer transfer

Engine checks:

Condition first

Then required behavior

Type 6: Multi-step Rules

Examples:
To place caller on hold:

Explain reason

Give expected duration

Ask permission

Engine checks:

All steps must be found

In correct order

Each step must be timestamped

Type 7: Tone-Based Rules

These are affected by Deepgram sentiment + baselines.

Examples:

If agent says “I understand” but tone contradicts baseline → tone issue

If agent escalates conflict → violation

Engine checks:

Voice sentiment vs text sentiment

Deviation from baseline

Strength of mismatch

LLM will NOT decide tone mismatches anymore.
Rule engine handles this deterministically.

Type 8: Resolution Rules

Examples:

Issue must be resolved

If unresolved → must document next steps

Must give clear resolution summary

Engine checks:

Key words

Intent

Resolution markers

Only nuance will later be handled by LLM, not rule detection.

6. What Rule Engine V2 Must Guarantee

Phase 3 requires defining these guarantees:

1. Deterministic behavior

Same input → same output
No randomness
No temperature
No interpretation

2. Complete rule coverage

Every rule MUST be evaluated.
No skipping.
No silent failures.

3. Evidence attached to every violation

Every failed rule must have:

transcript snippet

timestamp

speaker

sentiment (optional)

4. Category alignment

Every rule is linked to exactly one category.
Professionalism, Empathy, or Resolution.

5. Predictable scoring impact

Scoring system must receive:

pass/fail

severity

total penalty

Consistency becomes mathematically guaranteed.

7. What Will No Longer Happen After Phase 3

This must be explicitly documented:

A. LLM cannot create or detect rule violations

All rule detection is deterministic and handled by the engine.

B. LLM stops scanning raw policy text

The giant prompt disappears in Phase 4.

C. LLM cannot guess tone interpretation

Tone mismatches are defined in structured rules.

D. LLM cannot override structured rules

Deterministic > generative.

E. Company “vague” policies no longer break evaluation

Because rules are explicit.

8. How Rule Engine V2 Fits into the Pipeline

Phase 3 defines this REQUIRED pipeline order:

Deepgram transcription

Speaker identification

Voice baseline extraction

Rule Engine V2 runs

Violations + evidence are generated

Rule engine summary is passed to the LLM

LLM only performs rubric classification

Scoring engine applies penalties

Final score calculated

Notice the order:
Rule engine always runs before LLM.

9. What Phase 3 Does NOT Include

No changes to UI

No redesign of evaluation viewer

No changes to scoring formula

No changes to JSON schema

No changes to LLM yet (that comes in Phase 4)

No structured rule editor yet (Phase 5)

Phase 3 is purely:
determine rule violations → produce evidence → pass to scorer + LLM

10. Expected Result of Phase 3

Once Phase 3 is in place:

Rule violations become 100% consistent

Companies get predictable, stable enforcement

Tone evaluation becomes deterministic

LLM no longer controls compliance decisions

Debugging becomes easier

Evaluations become explainable

Human reviewers trust the system more

LLM workload shrinks massively

This is where your system becomes defensible, “enterprise-ready,” and no longer looks like a toy LLM wrapper.

Final Summary — Phase 3

Phase 3 turns structured rules into real executable enforcement.

By the end of Phase 3, the system:

Reads structured rules

Executes them

Detects violations

Creates evidence

Applies severity

Outputs consistent results

Sends a clean summary to the LLM

This is the phase that removes all ambiguity from compliance evaluation and makes the system predictable.