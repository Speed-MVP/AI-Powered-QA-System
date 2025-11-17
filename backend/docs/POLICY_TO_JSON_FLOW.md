# How User Policy Templates Get Converted to AI-Friendly JSON

## Overview

The system uses a **4-stage LLM-powered workflow** to convert human-written policy text into structured, machine-readable JSON rules that the AI can deterministically evaluate.

## The Complete Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER CREATES POLICY TEMPLATE                                  │
│    - Writes policy description                                   │
│    - Defines evaluation criteria                                 │
│    - Sets rubric levels                                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. API: POST /api/policy-templates/{id}/analyze-policy          │
│    - Extracts policy text from template                         │
│    - Calls PolicyRuleBuilder.analyze_policy_text()             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. STAGE 1: POLICY ANALYSIS (LLM Call #1)                      │
│                                                                 │
│    Input:                                                       │
│    {                                                            │
│      "policy_text": "Agent must greet within 15 seconds...",   │
│      "rubric_levels": {...}                                    │
│    }                                                            │
│                                                                 │
│    LLM Prompt: "Analyze policy and identify vague statements"  │
│    Model: gemini-2.0-flash-exp                                 │
│    Temperature: 0.0 (deterministic)                            │
│                                                                 │
│    Output:                                                      │
│    {                                                            │
│      "vague_statements": ["respond quickly", ...],             │
│      "missing_details": ["time threshold", ...],               │
│      "ambiguous_terms": ["quickly", "short time", ...]          │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. STAGE 2: GENERATE CLARIFYING QUESTIONS (LLM Call #2)        │
│                                                                 │
│    Input:                                                       │
│    {                                                            │
│      "policy_text": "...",                                     │
│      "vague_statements": [...],                                 │
│      "ambiguous_terms": [...]                                   │
│    }                                                            │
│                                                                 │
│    LLM Prompt: "Generate specific clarifying questions"         │
│                                                                 │
│    Output:                                                      │
│    {                                                            │
│      "clarifications": [                                        │
│        {                                                        │
│          "id": "q1",                                            │
│          "question": "What is the maximum acceptable greeting  │
│                       time in seconds?"                         │
│        }                                                        │
│      ]                                                          │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. USER ANSWERS CLARIFICATIONS                                  │
│    POST /api/policy-templates/{id}/clarifications               │
│    {                                                            │
│      "answers": [                                               │
│        {"question_id": "q1", "answer": "10 seconds"}            │
│      ]                                                          │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. STAGE 3: GENERATE STRUCTURED RULES (LLM Call #3)           │
│    POST /api/policy-templates/{id}/generate-rules              │
│                                                                 │
│    Input:                                                       │
│    {                                                            │
│      "policy_text": "Agent must greet within 15 seconds...",   │
│      "clarification_answers": {                                │
│        "q1": "10 seconds"                                       │
│      },                                                         │
│      "rubric_levels": {...}                                     │
│    }                                                            │
│                                                                 │
│    LLM Prompt Template:                                         │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ You are a Policy Rule Extractor. Convert human-written   │ │
│    │ policy descriptions into structured, machine-executable │ │
│    │ rules.                                                   │ │
│    │                                                           │ │
│    │ OUTPUT FORMAT (JSON only):                               │ │
│    │ {                                                        │ │
│    │   "policy_rules": {                                      │ │
│    │     "CategoryName": [                                    │ │
│    │       {                                                  │ │
│    │         "id": "snake_case_rule_id",                     │ │
│    │         "type": "boolean|numeric|phrase|list|...",      │ │
│    │         "category": "Professionalism",                   │ │
│    │         "severity": "minor|moderate|major|critical",    │ │
│    │         "enabled": true,                                 │ │
│    │         "description": "...",                          │ │
│    │         "required": true,                                │ │
│    │         "evidence_patterns": ["hello", "hi"],          │ │
│    │         "value": 15,  // for numeric                    │ │
│    │         "comparator": "le",  // for numeric             │ │
│    │         "phrases": [...],  // for phrase                 │ │
│    │         ...                                               │ │
│    │       }                                                  │ │
│    │     ]                                                    │ │
│    │   },                                                      │ │
│    │   "clarifications": []                                    │ │
│    │ }                                                        │ │
│    │                                                           │ │
│    │ RULE TYPES:                                              │ │
│    │ - boolean: true/false rules                              │ │
│    │ - numeric: rules with thresholds (e.g., "≤ 15 seconds") │ │
│    │ - phrase: rules checking for specific phrases           │ │
│    │ - list: rules checking against allowed values           │ │
│    │ - conditional: if-then rules                             │ │
│    │ - multi_step: sequential requirement rules               │ │
│    │ - tone_based: sentiment/emotion-based rules             │ │
│    │ - resolution: call resolution requirements              │ │
│    └─────────────────────────────────────────────────────────┘ │
│                                                                 │
│    Model: gemini-2.0-flash-exp                                 │
│    Temperature: 0.0 (deterministic)                            │
│    Max Tokens: 3000                                            │
│                                                                 │
│    Output (Raw LLM Response):                                 │
│    {                                                            │
│      "policy_rules": {                                         │
│        "Professionalism": [                                    │
│          {                                                     │
│            "id": "greet_within_seconds",                       │
│            "type": "numeric",                                 │
│            "category": "Professionalism",                       │
│            "severity": "moderate",                             │
│            "enabled": true,                                    │
│            "description": "Agent must greet within 10 seconds", │
│            "required": true,                                   │
│            "comparator": "le",                                │
│            "value": 10.0,                                     │
│            "unit": "seconds",                                 │
│            "measurement_field": "greeting_time"                │
│          },                                                    │
│          {                                                     │
│            "id": "identify_self",                             │
│            "type": "boolean",                                 │
│            "category": "Professionalism",                     │
│            "severity": "minor",                               │
│            "enabled": true,                                   │
│            "description": "Agent must identify themselves",  │
│            "required": true,                                  │
│            "evidence_patterns": [                              │
│              "my name is",                                     │
│              "this is",                                        │
│              "I'm"                                             │
│            ]                                                   │
│          }                                                     │
│        ]                                                       │
│      },                                                        │
│      "clarifications": []                                      │
│    }                                                           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. VALIDATION & NORMALIZATION                                   │
│                                                                 │
│    a) Parse JSON response                                       │
│    b) Validate against PolicyRulesSchema (Pydantic)            │
│    c) Convert to typed rule objects:                            │
│       - BooleanRule                                             │
│       - NumericRule                                             │
│       - PhraseRule                                              │
│       - ListRule                                                │
│       - ConditionalRule                                         │
│       - MultiStepRule                                           │
│       - ToneBasedRule                                          │
│       - ResolutionRule                                         │
│    d) Detect conflicts (contradictory rules)                  │
│    e) Return validated PolicyRulesSchema                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. STAGE 4: ADMIN APPROVES RULES                               │
│    POST /api/policy-templates/{id}/approve-rules                │
│                                                                 │
│    Rules are saved to database:                                 │
│    - policy_templates.policy_rules (JSONB column)              │
│    - policy_templates.policy_rules_version = 1                 │
│    - policy_templates.enable_structured_rules = true            │
│    - policy_templates.rules_approved_by_user_id = ...           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. FINAL JSON STRUCTURE (Stored in Database)                   │
│                                                                 │
│    {                                                            │
│      "version": 1,                                             │
│      "rules": {                                                 │
│        "Professionalism": [                                    │
│          {                                                     │
│            "id": "greet_within_seconds",                       │
│            "type": "numeric",                                  │
│            "category": "Professionalism",                      │
│            "severity": "moderate",                             │
│            "enabled": true,                                    │
│            "description": "Agent must greet within 10 seconds",│
│            "required": true,                                    │
│            "comparator": "le",                                 │
│            "value": 10.0,                                      │
│            "unit": "seconds",                                  │
│            "measurement_field": "greeting_time"                │
│          }                                                     │
│        ],                                                       │
│        "Empathy": [...],                                        │
│        "Compliance": [...]                                      │
│      },                                                         │
│      "metadata": {                                              │
│        "llm_model": "gemini-2.0-flash-exp",                    │
│        "llm_tokens_used": 1250,                                │
│        "llm_latency_ms": 450,                                  │
│        "conflicts_detected": []                                 │
│      }                                                          │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. RULE ENGINE V2 USES THIS JSON                              │
│     - Loads rules from policy_rules JSONB                       │
│     - Executes rules deterministically                          │
│     - No LLM interpretation needed                             │
│     - Returns structured violation results                      │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. PolicyRuleBuilder Service
**Location:** `backend/app/services/policy_rule_builder.py`

**Main Methods:**
- `analyze_policy_text()` - Stage 1: Identifies vague statements
- `generate_clarifying_questions()` - Stage 2: Creates clarification questions
- `generate_structured_rules()` - Stage 3: Converts policy + answers → JSON rules

### 2. LLM Prompt Engineering

The system uses carefully crafted prompts that:

1. **Specify exact JSON schema** - The LLM must output valid JSON matching `PolicyRulesSchema`
2. **Provide examples** - Shows the LLM exactly what format to use
3. **Use deterministic settings** - `temperature=0.0` ensures reproducible results
4. **Include rubric context** - Helps LLM understand severity levels

### 3. Rule Types Supported

The JSON supports 8 rule types:

1. **Boolean** - True/false checks (e.g., "agent identified themselves")
2. **Numeric** - Threshold comparisons (e.g., "greeting time ≤ 10 seconds")
3. **Phrase** - Pattern matching (e.g., "must say 'thank you'")
4. **List** - Allowed value checks (e.g., "use one of: option1, option2")
5. **Conditional** - If-then logic (e.g., "if customer is angry, then apologize")
6. **Multi-step** - Sequential requirements (e.g., "first greet, then identify, then ask")
7. **Tone-based** - Sentiment/emotion rules (e.g., "match customer's tone")
8. **Resolution** - Call resolution requirements (e.g., "must confirm resolution")

### 4. Why This Approach Works

**Before (Old System):**
- LLM directly interprets vague policy text
- Non-deterministic results
- Hard to audit
- Inconsistent evaluations

**After (New System):**
- Human clarifies ambiguous parts
- LLM converts clarified policy → structured rules (one-time)
- Rule Engine executes rules deterministically (every evaluation)
- Fully auditable and consistent

## Example: Complete Conversion

### Input (Human Policy Text):
```
"Agents must greet customers promptly and identify themselves. 
They should show empathy when customers are frustrated. 
All calls must be resolved within 5 minutes."
```

### After Clarification:
- "promptly" → clarified to "within 10 seconds"
- "show empathy" → clarified to "say 'I understand' or 'I'm sorry'"
- "resolved" → clarified to "customer confirms resolution"

### Output (Structured JSON):
```json
{
  "version": 1,
  "rules": {
    "Professionalism": [
      {
        "id": "greet_within_seconds",
        "type": "numeric",
        "category": "Professionalism",
        "severity": "moderate",
        "enabled": true,
        "description": "Agent must greet within 10 seconds",
        "required": true,
        "comparator": "le",
        "value": 10.0,
        "unit": "seconds",
        "measurement_field": "greeting_time"
      },
      {
        "id": "identify_self",
        "type": "boolean",
        "category": "Professionalism",
        "severity": "minor",
        "enabled": true,
        "description": "Agent must identify themselves",
        "required": true,
        "evidence_patterns": ["my name is", "this is", "I'm"]
      }
    ],
    "Empathy": [
      {
        "id": "show_empathy_when_frustrated",
        "type": "phrase",
        "category": "Empathy",
        "severity": "major",
        "enabled": true,
        "description": "Agent must show empathy when customer sentiment is negative",
        "required": true,
        "phrases": ["I understand", "I'm sorry", "I apologize"],
        "condition": {
          "field": "customer_sentiment",
          "operator": "eq",
          "value": "negative"
        }
      }
    ],
    "Resolution": [
      {
        "id": "resolve_within_minutes",
        "type": "numeric",
        "category": "Resolution",
        "severity": "critical",
        "enabled": true,
        "description": "Call must be resolved within 5 minutes",
        "required": true,
        "comparator": "le",
        "value": 5.0,
        "unit": "minutes",
        "measurement_field": "call_duration"
      },
      {
        "id": "confirm_resolution",
        "type": "boolean",
        "category": "Resolution",
        "severity": "critical",
        "enabled": true,
        "description": "Customer must confirm resolution",
        "required": true,
        "evidence_patterns": ["yes", "resolved", "that works", "thank you"]
      }
    ]
  },
  "metadata": {}
}
```

## Benefits

1. **Deterministic** - Same rules always produce same results
2. **Auditable** - Every rule is explicit and traceable
3. **Maintainable** - Rules can be edited without re-training
4. **Fast** - Rule engine executes instantly (no LLM calls per evaluation)
5. **Cost-effective** - LLM only used once during rule generation, not per call

