PHASE 1 — SOP BUILDER (BARE-MINIMUM, FULL SPEC)

Purpose:
Define the call flow (Stages → Steps) that describes how an agent should handle the call.
This gives your deterministic rule engine the procedural skeleton of the call so it can check:

did the agent follow the correct order?

did the agent follow required steps?

did the agent skip anything?

did expected cues appear?

when did each step happen (timestamps)?

Without this, the evaluation has no structure.

1. What PHASE 1 Must Build

A single page/editor that allows users to define:

A) Stages (example: Opening, Discovery, Resolution, Closing)
B) Steps inside each stage (example: Greet customer, Verify identity, Ask probing questions)

This becomes the FlowVersion.

This is the foundation for deterministic rule checking and mapping rubrics later.

Nothing more.

2. UI Requirements (Bare Minimum)
2.1 Layout

A simple 2-column builder:

LEFT SIDE: Stages List

Add stage

Rename stage

Delete stage

Drag to reorder stages

RIGHT SIDE: Stage Detail → Steps List

Add step

Rename step

Delete step

Drag to reorder steps

Step detail panel

2.2 Step Detail Panel

Each step has the following minimal fields:

Step Name

Description

Explain what the step means operationally.

Required Step (true/false)

If true: missing this step = deterministic violation.

Expected Phrases (optional list)

Words or short phrases you expect agents to say during this step.

Used for detection.

Timing Requirement (optional)

Numeric field: must occur within X seconds from:

call start OR

previous step (default: call start)

That’s all.

3. Data Model Requirements (No code, just structure)
3.1 FlowVersion JSON (entire output of Phase 1)
FlowVersion {
  id: <string>,
  name: <string>,
  stages: [
    {
      id: <string>,
      name: <string>,
      order: <int>,
      steps: [
        {
          id: <string>,
          name: <string>,
          description: <string>,
          required: <boolean>,
          expected_phrases: [ "<phrase1>", "<phrase2>" ],
          timing_requirement: {
            enabled: <boolean>,
            seconds: <number>
          },
          order: <int>
        }
      ]
    }
  ]
}


This JSON is used by the deterministic engine (Phase 3) AND the rubric/scoring map (Phase 5).

4. Behavior & Functional Logic
4.1 Stage behavior

Stages define the sequence of the call.

The order matters → evaluation checks that conversation flows in the stage order.

4.2 Step behavior

Each step represents an expected action by the agent.

At evaluation time, the rule engine will:

Search for expected phrases in the transcript.

If matched → pass with evidence

If not matched → step likely failed

Check if step occurred in correct order.

Check if step was required.

Evaluate timing requirement if enabled.

This means your step definitions must be clear and concise.

5. Validations (Mandatory)

Your UI must block saving if:

Stage validations

Stage name empty

Two stages have same name

Step validations

Step name empty

Step description empty

Ordering must be unique and sequential

If timing is enabled but seconds is empty → block

Flow-level validations

At least one stage must exist

Each stage must have at least one step

6. Purpose in the Pipeline (Why Phase 1 Exists)
6.1 PHASE 1 gives structure to your entire evaluation system.

Without SOP definition, your product is blind.

Used by Phase 2 (Compliance Rules)

Compliance rules attach to stages or steps.
FlowVersion gives them the valid IDs.

Used by Phase 3 (Deterministic Rule Engine)

Rule engine uses the FlowVersion to:

detect stage boundaries

detect step completion

enforce step order

detect missing required steps

enforce timing rules

provide evidence snippets

Used by Phase 4 (LLM Stage Evaluation)

LLM uses:

stage list

step list

step requirements
to give structured stage scoring.

Used by Phase 5 (Rubric Scoring)

Rubric mappings connect categories → stages.
This mapping uses stage IDs defined in Phase 1.

Used by Phase 6 (Final Scoring Pipeline)

Final score references stage IDs and step IDs from FlowVersion.

PHASE 1 is the skeleton of everything.

7. Acceptance Criteria (Must Pass)
A. User can:

Create unlimited stages

Reorder stages

Add unlimited steps under each stage

Reorder steps

Delete stages/steps

Edit all fields

B. Validations prevent broken FlowVersion
C. Saving produces a valid FlowVersion JSON
D. Rule Engine can consume FlowVersion without errors

Stage IDs exist

Step IDs exist

Required flags present

Timing fields valid

E. LLM receives stable structure

Stages and steps are predictable and consistent.

8. Example of a minimal SOP built in Phase 1
FlowVersion {
  id: "fv_001",
  name: "Default Call Flow",
  stages: [
    {
      id: "stage_open",
      name: "Opening",
      order: 1,
      steps: [
        {
          id: "step_greet",
          name: "Greeting",
          description: "Agent greets the customer politely.",
          required: true,
          expected_phrases: ["How may I help you", "Good morning"],
          timing_requirement: {
            enabled: true,
            seconds: 10
          },
          order: 1
        }
      ]
    },
    {
      id: "stage_discovery",
      name: "Discovery",
      order: 2,
      steps: [
        {
          id: "step_probe",
          name: "Ask probing questions",
          description: "Agent asks clarifying questions.",
          required: true,
          expected_phrases: ["Can you tell me more", "What seems to be the issue"],
          timing_requirement: {
            enabled: false,
            seconds: null
          },
          order: 1
        }
      ]
    }
  ]
}


This is the output of Phase 1.
This is exactly what phases 2–6 consume.

9. Summary (Blunt and Clear)

Phase 1 only builds the SOP structure.
No rules engine.
No scoring.
No rubrics.
No evaluation.
No extra UI.
No auditing.

Just:

stages

steps

required flags

expected phrases

optional timing

ordering

And emits a clean FlowVersion JSON used by the rest of the system.

If you want, I’ll now send PHASE 2 (Compliance Rules Builder — minimal, full implementation details) in the same format.