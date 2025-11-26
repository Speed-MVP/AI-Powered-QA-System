PHASE 5 — Detection Engine (Semantic / Exact / Hybrid)

This is the heart of your system’s accuracy, fairness, and real-world usability for call centers.
It is also the part where most QA tools fail — they either use shallow keyword detection (garbage accuracy) or they rely purely on LLMs (inconsistent, brittle, expensive).

Your detection engine must be:

deterministic where possible

semantic (meaning-based) when needed

robust to phrasing variations

speaker-aware

context-aware

time-aware

reproducible across calls

This phase describes the runtime engine that consumes the compiled blueprint and transcript to produce per-behavior detection results.

1 — Purpose

Take a transcript (from Deepgram) and determine for each behavior in the blueprint:

Did the agent do it?

Did the agent violate something?

Did it happen early/late?

Was it done correctly?

What did they actually say?

How confident is the detection?

This produces the detection JSON that Phase 6 (Stage LLM evaluator) will refine and Phase 7 (Scoring) will consume.

2 — Inputs & Outputs
Inputs

Transcript

diarized utterances with timestamps

speaker labels ("agent", "caller")

sentiment (Deepgram)

per-utterance confidence

Compiled FlowVersion

stages

steps (behaviors)

detection hints

expected phrases

Compliance rules

required / forbidden / critical

timing constraints

match_mode (semantic/exact/hybrid)

Detection Engine Config

semantic LLM model settings

similarity thresholds

max LLM calls allowed

fallback logic

Outputs

For each behavior:

{
  "behavior_id": "uuid",
  "name": "Verify caller identity",
  "detected": true,
  "match_type": "semantic", 
  "matched_text": "Could I have your full name for verification?",
  "confidence": 0.93,
  "start_time": 12.4,
  "end_time": 14.8,
  "violation": false,
  "violation_reason": null,
  "timing_passed": true,
  "additional_evidence": { ... }
}


At the stage level:

{
  "stage_id": "uuid",
  "behaviors": [ ... ],
  "deterministic_score": 85
}

3 — Detection Engine Architecture (Critical)

The engine must be composed of 5 layers:

Layer 1 — Transcript Normalization

Purpose: make transcripts more machine-detectable.

Actions:

remove stutters ("uh", "um")

remove filler words ("you know", "like")

normalize contractions ("I’m" → "I am")

unify punctuation

unify casing

map speaker diarization → “agent” / “caller"

Built-in filters:

irrelevant small talk detection (optional)

profanity masking (optional)

punctuation injection for long monologues

Output is a cleaned transcript that downstream detection uses.

Layer 2 — Exact Match Engine

Used when detection_mode = exact or hybrid.

Actions:

For each behavior expected phrase:

perform literal substring match

fuzzy match (Levenshtein ≤ 15% difference)

phonetic match (optional)

For forbidden behaviors, run negative-match detection.

Results:

high precision, medium recall

fast, deterministic

Outputs:

{
  "detected": true,
  "match_type": "exact",
  "confidence": 1.0,
  "matched_text": "This call may be recorded."
}

Layer 3 — Semantic Match Engine

Used when detection_mode = semantic or hybrid.

This uses a small LLM / embedding model, not the Stage LLM.

Process:

Split transcript into agent utterances

Compute embedding similarity between utterance and behavior semantics

behavior semantic = embed(behavior.description + behavior.phrases.join(","))

utterance semantic = embed(utterance_text)

Compare vectors using cosine similarity

Accept if:

score ≥ semantic_threshold (0.78 recommended)

Extract matched utterance

Calculate confidence using:

similarity score

utterance length

Deepgram confidence

This layer is critical for call center accuracy because agents rephrase scripts.

Example:
Behavior: "Verify caller identity"
Agent said: "Can I confirm your name first?"

Exact match fails.
Semantic match detects it with ~0.92 similarity → correct.

Layer 4 — Hybrid Decision Logic

If detection mode = hybrid, apply:

if exact_match:
    use exact (confidence=1.0)
else if semantic_match:
    use semantic
else:
    detected = false


This prevents:

false positives

semantic overreach

misinterpretation

Hybrid is the safest default.

Layer 5 — Rule Compliance Evaluation

After detection is done per behavior:

For required behaviors:
if detected == false:
    violation = true
    violation_reason = "required_action_missing"

For forbidden behaviors:
if detected == true:
    violation = true
    violation_reason = "forbidden_phrase_used"

For critical behaviors:

If violated → stage auto-fail OR pipeline auto-fail depending on blueprint config.

For timing-based behaviors:
if stage_start_time + expected_seconds < detection_time:
    timing_passed = false
    violation = true
    violation_reason = "late_behavior"


Supports early, late, or missing.

4 — Confidence Scoring Model (Must Be Explicit)

Confidence score = weighted ensemble:

confidence =
    0.50 * similarity_score    (semantic layer)
  + 0.20 * deepgram_confidence (utterance confidence)
  + 0.20 * match_precision     (exact/hybrid)
  + 0.10 * evidence_strength   (# of supporting utterances)


Range = 0–1
If < 0.50 → pass to human review.

5 — Speaker-Aware Behavior Detection

Behaviors must be evaluated only in the agent’s speech.

Ignore caller responses unless blueprint explicitly defines caller-required behavior.

For multi-party calls, agent diarization should be robust:

Use Deepgram’s diarization

If confidence low, use fallback speaker classifier

If still uncertain → mark detection as “low confidence” to human review

6 — Multi-Utterance Behavior Detection

Some behaviors require multiple sentences to confirm.

Example: “Provide resolution + confirm satisfaction”

Engine must allow:

Utterance 1: “I’ve fixed the issue…”
Utterance 2: “Is everything working now?”


This is one behavior.
Semantic engine should merge them automatically.

7 — Negative Semantic Detection

Important for forbidden behaviors like:

“Don’t say sorry”

“Avoid promising refunds”

Semantic detection must support:

intent matching

polarity detection

paraphrase rejection

Thus:

"we won't replace it" ≠ "we will replace it"


Use the embedding model with negation handling.

8 — Special Cases & Edge Handling
Case 1 — Extremely short utterances

Semantic similarity become noisy.
Fallback to hybrid mode prioritizing exact phrases.

Case 2 — Long storytelling segments

Behavior must not trigger inside irrelevant monologue → require context window.

Case 3 — Questions vs statements

Semantic model must consider intent:

“Do you want me to verify your info?” ≠ verifying.

Case 4 — Sarcasm / tone

Detect likely sarcasm → mark low confidence → route to human review.

9 — Evidence Output Format

The detection engine produces detailed evidence fields:

{
  "utterances_checked": 143,
  "matches_found": 3,
  "best_match_similarity": 0.91,
  "context_window": [
     {"utterance":"...", "time":...}
  ],
  "speaker_validation": "agent",
  "timing_data": {...}
}


This is what your results page will show in the UI.

10 — Fail-Safe Mode

If semantic engine malfunctions (LLM error, embeddings unavailable):

fall back to exact match

set confidence to 0.4

force human review

11 — Performance Requirements

Max 3000 utterances per call

Must run in <2 seconds for 10-minute call

Semantic embeddings should be cached per utterance

Parallel scoring for behaviors

12 — Deliverables for Devs
Required modules:

TranscriptNormalizer

ExactMatchDetector

EmbeddingService

SemanticDetector

HybridDetector

ComplianceRuleEvaluator

ConfidenceEngine

DetectionAggregator

Required tests:

exact match tests

fuzzy match tests

semantic paraphrase tests

forbidden phrase tests

timing rule tests

multi-utterance tests

negative detection tests

diarization tests

low-confidence routing tests

Required monitoring:

similarity score histograms

semantic false-positive/false-negative rate

utterance-embedding throughput

average detection latency

13 — Why This Design Is Superior

Because it:

avoids brittle keyword-only systems

avoids unpredictable LLM hallucinations

detects paraphrases

respects agent natural language

uses hybrid logic to prevent errors

handles timing and speaker attribution

produces reliable evidence

scales to enterprise call centers

works internationally

This is the best detection engine architecture you can realistically ship.