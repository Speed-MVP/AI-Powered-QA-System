PHASE 1 — Concept & Goals (High-Level Architecture)
Purpose

Shift from your over-engineered 7-structure configuration (Flows, Steps, Rules, Rubrics, Criteria, Mappings, Templates) → to ONE unified, human-friendly configuration system called the QA Blueprint.

This blueprint is what QA managers see.
Your backend still runs deterministic + LLM + scoring.
But the user config becomes simple, visual, and intuitive.

WHAT THE QA BLUEPRINT REPRESENTS

A single object that defines:

1. Call Flow (Stages)

A vertical list of stages (Opening, Verification, Resolution, Closing).

2. Behaviors (Inside Each Stage)

Each behavior = ONE action expected from agent.

Examples:

Greeting

Asking for name

Confirming identity

Providing a solution

Thanking customer

Behaviors replace:

rules

rubric criteria

steps

evaluations

compliance requirements

scoring mappings

3. Behavior Settings

Each behavior has:

Behavior Type
required / optional / forbidden / critical

Detection Mode
semantic → LLM meaning
exact phrase → literal match
hybrid → both accepted

Phrases (optional)

Weight (how much the behavior contributes to stage score)

Critical Action (fail stage / fail overall)

GOALS ACHIEVED
✔ Simplicity for QA managers
✔ Accurate + reproducible evaluations
✔ No need to configure 50+ rules
✔ Transparent scoring
✔ Flexible natural-language detection
✔ Auditable + version-controlled
✔ Still fully compatible with your existing 7-phase pipeline