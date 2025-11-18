PHASE 2 — AI Policy Rule Builder (Conceptual Only)
Goal: Convert vague, human-written company policies into precise, structured, machine-readable rules — with human confirmation — before evaluations can ever use them.

Phase 2 is the most important phase of the entire redesign.
This is where you eliminate policy ambiguity forever.

You are building a policy interpretation system that only runs once per policy creation or update — NOT during evaluation.

1. Core Purpose of Phase 2

To create a one-time transformation pipeline that converts human-written policy text into structured rules that the Rule Engine V2 can execute.

After Phase 2:

LLM NEVER sees human-written policies during evaluation

LLM NEVER interprets free-text policies

LLM ONLY interacts with structured rules

Rules become locked, explicit, deterministic

Companies cannot accidentally create vague policies that break evaluations

Phase 2 is where the system becomes enterprise-grade.

2. Inputs for Phase 2

The system will ask the company to provide:

A. Human policy text (current approach)

Example:

“Agent must greet the customer warmly.”

“Agent should resolve issues in a timely manner.”

B. Category definitions

Example:

Professionalism

Empathy

Resolution

C. Rubric levels

Example:

Excellent

Good

Average

Poor

Unacceptable

These become the raw material for rule creation.

3. The Policy Rule Builder Pipeline

Phase 2 introduces a 5-stage pipeline:

Stage 1 — LLM Reads Human Policy Text (Offline)

The LLM reads the entire human-written policy text plus company rubric levels.

This ONLY happens during policy creation or editing — NOT during evaluation.

During this stage, the LLM:

Identifies actionable items

Identifies hidden rules

Identifies missing detail

Identifies vague statements

Identifies ambiguous wording

The output is NOT rules yet.
It is an analysis of what’s missing and unclear.

Stage 2 — LLM Generates Clarifying Questions

Because human policy text is always vague, the builder must ask clarifying questions.

Examples:

“What is considered a ‘timely manner’? Please specify in minutes.”

“Does ‘warm greeting’ require a specific phrase?”

“How many seconds after call start must greeting occur?”

“Is customer verification mandatory in all calls?”

The system continues generating questions until:

All rules become explicitly quantifiable

No ambiguity remains

Every vague policy has at least one clarification

This forces companies to define real policy rules instead of vague HR-style guidelines.

Stage 3 — Admin User Answers Clarifications

Company admin answers all clarifying questions.

Some answers will modify or override the initial vague policy text.

This step guarantees:

Policy is explicitly defined

Policy is not open to interpretation

Policy becomes enforceable

Rules reflect the company’s actual expectations

You must design the system so the admin cannot skip this step.

Stage 4 — LLM Generates Structured Machine Rules

Once answers are complete, the LLM converts all info into structured rules.

Rules will include:

A. Boolean rules

must_identify_company: true

must_offer_further_help: false

B. Timing rules

greeting_within_seconds: 15

hold_explanation_required_within: 5

C. Required phrases / keywords

greeting_phrases: ["thank you for calling"]

apology_phrases: ["sorry", "I apologize"]

D. Disallowed phrases

forbidden_phrases: ["nothing I can do", "that’s policy"]

E. Numeric thresholds

resolution_time_max: 180 seconds

silence_threshold: 10 seconds

F. Conditional rules

if_customer_is_angry → empathy_required: true

if_issue_unresolved → escalation_required: true

Every rule:

Includes category (Professionalism, Empathy, Resolution)

Includes severity (minor, moderate, major, critical)

Includes evidence requirements

This output is purely structured and deterministic.

Stage 5 — Admin Approves or Edits the Final Rules

The admin sees a full preview of machine-generated rules.

The admin must confirm:

Yes → rules locked

No → admin edits rules manually

The company must explicitly approve the structured rules.

No structured rules = policy cannot be activated.

4. Rule Quality Guarantees

The rule builder must guarantee these properties:

1. Completeness

Every part of human-written policy must be accounted for.

2. Determinism

Every rule must have:

explicit thresholds

explicit match conditions

explicit severity

3. 1-to-1 traceability

Each structured rule must point to:

the original human policy

the expected behavior

the category it belongs to

the severity of violation

4. No interpretation required later

Once structured, the LLM never interprets again.

5. What the System Blocks in Phase 2

Phase 2 explicitly prevents:

A. Vague policy text from being used directly

Example:

“Greet warmly” → REJECTED until clarified

“Quick resolution” → REJECTED until clarified

B. Policies without thresholds

Example:

“Respond promptly” → FORCE QUESTION: “In how many seconds?”

C. Policies missing categories

Example:

A rule must always belong to a category

D. Contradictory rules

Example:

“Must escalate unresolved calls”

“Avoid escalation”

System forces admin confirmation with warnings.

E. Company skipping policy clarifications

No clarifications → rules cannot be generated.

6. What This Solves

Before Phase 2:

Policies are vague

LLM “interprets”

Evaluation inconsistent

Different runs → different results

After Phase 2:

Policies become explicit, structured, deterministic

Rule Engine V2 uses rules directly

LLM never interprets rules

All companies have consistent scoring

Evaluation becomes repeatable and stable

7. Output of Phase 2

After completing Phase 2, every policy template will contain:

A. Original human-written policy

For reference only.

B. Structured rules generated from that policy

Used by the Rule Engine V2.

C. Clarification answers from the admin

Stored and traceable.

D. A final “approved ruleset”

This becomes the only policy used during evaluation.

8. What Phase 2 Does NOT Include

No evaluation logic

No LLM scoring logic

No rule engine execution

No frontend UI redesign for scoring

No scoring changes

Phase 2 is purely policy → rule transformation.

9. The Importance of Phase 2

This phase is the “policy compiler.”

You are essentially creating:

a policy programming language

a compiler

a validation system

a rulebook that never changes unless the company changes it

a future-proof evaluation foundation

Without Phase 2, deterministic evaluation is impossible.

10. What Happens After Phase 2

Phase 3:

Rule Engine reads the structured rules and executes them deterministically.

Phase 4:

LLM only reads the rule results and rubric definitions (not human policy text).

Phase 5 (optional):

Companies can manually modify structured rules visually without LLM help.

Final Summary — Phase 2

Phase 2 transforms company-written policies into something machines can evaluate consistently.

It introduces:

A clarifying question workflow

A one-time LLM transformation

Strict structured rules

Rule validation

Admin approval

Guaranteed determinism

Zero ambiguity

Zero interpretation

A locked policy_rules dataset

This is the phase that makes the entire QA system:

Stable

Predictable

Enterprise-ready

Defendable

Auditable

Non-random

This is the most important phase of the redesign.