PHASE 1 — Structured Rules Foundation (No Code Version)
Goal: remove LLM interpretation from policies by creating a rule-based foundation BEFORE any LLM evaluation happens.

Phase 1 is the architectural cleanup phase.
You’re not changing the user-facing product yet.
You’re laying the foundation that will make all later phases consistent and deterministic.

This is what Phase 1 must achieve:

1. Introduce the concept of “Structured Rules”

You need the system to have two versions of every company’s policy:

Human-Written Policy

What the company types (plain text, vague, ambiguous)

Machine-Readable Policy Rules

A structured representation that is:

deterministic

explicit

executable

free of interpretation

consistent across evaluations

Phase 1 only introduces the concept and storage for the structured rules.
These rules are not used yet. They are just added to the system.

2. Add a storage space for “policy_rules” inside policy templates

Policies today are only stored as unstructured text + categories + rubric levels.

You need to introduce a new field (conceptually):

policy_rules
A container that will later hold structured rule objects, such as:

must_greet_within: 15 seconds  
must_confirm_account: true  
must_state_resolution: mandatory  
allowed_close_phrases: [...list...]  


For Phase 1:

You just prepare a place to store these rules.

You don’t populate them.

You don’t use them.

You’re simply preparing the container.

3. Create a “Rule Schema” (conceptual definition)

Before you can create structured rules later, you need to define how rules must look.

Phase 1 requires defining the schema, not generating rules.

Your schema must support at least:

A. Boolean rules

Examples:

agent must apologize

must confirm customer name

must offer help closure

B. Numeric threshold rules

Examples:

greeting must occur within X seconds

hold explanation must appear within Y seconds

silence cannot exceed Z seconds

C. Required phrase / keyword rules

Examples:

must say “thank you for calling”

must provide case number

must restate issue

D. Disallowed phrase rules

Examples:

cannot say “I can’t do anything”

cannot say “that’s policy”

E. Evidence-based rules

Rules that require specific transcript evidence.

Phase 1 goal:
Define these rule types clearly so you know what Phase 2 will generate.

4. Add a “Rule Validator” design (conceptual only)

Before you accept structured rules, you must know whether a rule is valid.

So Phase 1 requires you to define what constitutes a valid rule.

You need to define:

which fields are required

which fields belong to which rule types

how to detect incomplete rules

how to catch conflicting rules

how severity is defined

how to detect vague instructions

The actual validator code is later.
Phase 1 is just the rules of the rules (meta-layer).

5. Define how rules will be used (conceptual pipeline)

This phase defines the future pipeline without implementing any logic.

The rule engine in Phase 3 will use:

Transcript

Segmented utterances

Speaker roles

Rule definitions from Phase 1

Structured policy_rules (created in Phase 2)

And produce:

Violations

Evidence

Severity

Category link

Rule score impacts

Phase 1 defines the “blueprint” for this future behavior.

6. Define what cannot happen anymore

You must decide the behaviors that will be blocked once the redesign is active.

These include:

A. The LLM should NEVER again:

read raw policy text

interpret user-written policies directly

guess what company rules mean

fabricate rule logic

invent missing constraints

drift category names

decide criteria from prose

B. The system will require:

all policies MUST be converted into structured rules

scoring must rely on structured rules

LLM can only score nuance (rubric-level classification), NOT rules

Phase 1 documents these requirements.

7. Add a setting to toggle “structured policy mode”

You need to define (conceptually) a system feature flag:

enable_structured_rules = false (default)

Later phases turn it on after the rules are fully ready.

Phase 1 just defines the config.

8. Define the transition plan for existing customers

You need to plan how existing policy templates are handled.

Phase 1 defines:

Existing policies stay untouched

No impact on current evaluation

Structured rules remain empty

LLM still uses the long prompt until Phase 4

This avoids breaking older customers.

9. Define the required metadata for future updates

You must decide what metadata will be required in later phases:

policy_rules_version

date rules were last generated

who approved the rules (user id)

rule generation method (AI vs manual)

rule validation status

rubric_version_connected

company_policy_version

Phase 1 documents this metadata but does not store anything yet.

10. Define the expectations for Phase 2

Phase 1 ends with defining what Phase 2 must do:

Phase 2 will:

Read human-written policy

Ask clarifying questions

Generate structured rules

Present generated rules to the user

Allow user to approve or revise

Lock rules into policy_rules

Phase 1 only documents this.
Phase 2 actually builds it.

11. Define rule engine V2 architecture (conceptual only)

You’re not implementing the engine in Phase 1, but you must define:

what inputs the rule engine accepts

what outputs it must generate

how it links a violation to a category

how severity affects scoring

how rules are weighted

how evidence is attached to violations

how timestamps are handled

how silence detection works

how numeric checks work

This gives your team clarity before writing code.

12. Define how LLM will later be restricted

Phase 1 documents how the LLM will work AFTER redesign:

It will NOT read raw policy text

It will receive structured rule results only

It will receive rubric names only

It will classify “which rubric level fits the data”

It will NOT perform direct scoring

It will NOT interpret rules

This ensures all future phases follow the design.

Final Summary — What Phase 1 Produces

By the end of Phase 1, you must have:

1. A clear definition of structured rules
2. A conceptual rule schema
3. A rule validator definition
4. A conceptual rule engine V2 design
5. A configuration toggle
6. A policy_rules container prepared
7. Transition plan for current clients
8. Future pipeline documented
9. Metadata definitions
10. LLM restrictions clearly documented
