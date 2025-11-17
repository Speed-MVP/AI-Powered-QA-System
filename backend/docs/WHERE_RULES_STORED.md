# Where Deterministic Rules Are Stored

## The Complete Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER CREATES POLICY TEMPLATE (Human-Typed Text)              │
│                                                                 │
│    Table: policy_templates                                      │
│    Columns populated:                                           │
│    ├── id = "abc-123"                                           │
│    ├── template_name = "Customer Service Policy"               │
│    ├── description = "Agents must greet customers promptly..." │
│    ├── company_id = "xyz-789"                                   │
│    └── evaluation_criteria = [                                  │
│          {                                                       │
│            "category_name": "Professionalism",                   │
│            "evaluation_prompt": "Check if agent greets..."     │
│          }                                                       │
│        ]                                                        │
│                                                                 │
│    At this point:                                               │
│    - policy_rules = NULL (not yet generated)                    │
│    - enable_structured_rules = false                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. SYSTEM CONVERTS HUMAN TEXT → DETERMINISTIC RULES            │
│                                                                 │
│    Process:                                                     │
│    a) Extract policy text from template.description +           │
│       evaluation_criteria[].evaluation_prompt                   │
│    b) Call PolicyRuleBuilder.generate_structured_rules()       │
│    c) LLM converts vague text → structured JSON                 │
│    d) Validate against PolicyRulesSchema                       │
│                                                                 │
│    Output: Structured JSON rules                                │
│    {                                                            │
│      "version": 1,                                             │
│      "rules": {                                                 │
│        "Professionalism": [                                    │
│          {                                                     │
│            "id": "greet_within_seconds",                      │
│            "type": "numeric",                                 │
│            "value": 10.0,                                      │
│            "comparator": "le",                                │
│            ...                                                 │
│          }                                                     │
│        ]                                                       │
│      }                                                         │
│    }                                                           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. ADMIN APPROVES RULES                                         │
│    POST /api/policy-templates/{id}/approve-rules                │
│                                                                 │
│    Code (from policy_rules.py:365):                            │
│    template.policy_rules = request.rules  ← SAVED HERE!         │
│    template.policy_rules_version = 1                          │
│    template.enable_structured_rules = True                       │
│    template.rules_approved_by_user_id = current_user.id         │
│    db.commit()                                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. FINAL STATE: SAME TABLE, SAME ROW, DIFFERENT COLUMNS         │
│                                                                 │
│    Table: policy_templates                                      │
│    Row ID: "abc-123"                                            │
│                                                                 │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ HUMAN-TYPED DATA (Original)                             │ │
│    ├─────────────────────────────────────────────────────────┤ │
│    │ template_name = "Customer Service Policy"              │ │
│    │ description = "Agents must greet customers promptly..." │ │
│    │ evaluation_criteria = [...] (human-written prompts)     │ │
│    └─────────────────────────────────────────────────────────┘ │
│                                                                 │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ DETERMINISTIC RULES (Generated)                        │ │
│    ├─────────────────────────────────────────────────────────┤ │
│    │ policy_rules = {                                        │ │
│    │   "version": 1,                                         │ │
│    │   "rules": {                                           │ │
│    │     "Professionalism": [                               │ │
│    │       {                                                │ │
│    │         "id": "greet_within_seconds",                  │ │
│    │         "type": "numeric",                             │ │
│    │         "value": 10.0,                                  │ │
│    │         "comparator": "le"                              │ │
│    │       }                                                │ │
│    │     ]                                                  │ │
│    │   }                                                    │ │
│    │ }                                                       │ │
│    │                                                         │ │
│    │ policy_rules_version = 1                               │ │
│    │ enable_structured_rules = true                         │ │
│    │ rules_generated_at = 2025-01-27 12:00:00              │ │
│    │ rules_approved_by_user_id = "user-456"                 │ │
│    │ rules_generation_method = "ai"                         │ │
│    └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

### Table: `policy_templates`

**Same table stores both:**
- **Original human-typed policy** (columns: `description`, `template_name`, `evaluation_criteria`)
- **Deterministic rules** (column: `policy_rules` JSONB)

```sql
CREATE TABLE policy_templates (
    -- Original human-typed data
    id VARCHAR(36) PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    description TEXT,                    -- Human-typed policy text
    company_id VARCHAR(36) NOT NULL,
    
    -- Deterministic rules (generated from human text above)
    policy_rules JSONB,                  -- ← DETERMINISTIC RULES STORED HERE
    policy_rules_version INTEGER,
    enable_structured_rules BOOLEAN DEFAULT false,
    rules_generated_at TIMESTAMP,
    rules_approved_by_user_id VARCHAR(36),
    rules_generation_method VARCHAR(20),  -- 'ai' or 'manual'
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Related table for evaluation criteria (human-typed prompts)
CREATE TABLE evaluation_criteria (
    id VARCHAR(36) PRIMARY KEY,
    policy_template_id VARCHAR(36) REFERENCES policy_templates(id),
    category_name VARCHAR(255),
    evaluation_prompt TEXT,              -- Human-typed evaluation prompt
    ...
);
```

## Key Points

### 1. **Same Table, Same Row**
- The deterministic rules are stored in the **SAME table** (`policy_templates`)
- In the **SAME row** as the original policy template
- Just in a **different column** (`policy_rules` JSONB)

### 2. **Why This Design?**
- **One-to-one relationship**: Each policy template has exactly one set of deterministic rules
- **Easy lookup**: When evaluating a call, just query `policy_templates.policy_rules` for that template
- **Backward compatible**: Old templates without rules still work (`policy_rules = NULL`)

### 3. **How It's Used**

When evaluating a call:

```python
# Get policy template
template = db.query(PolicyTemplate).filter(
    PolicyTemplate.id == recording.policy_template_id
).first()

# Check if structured rules exist
if template.enable_structured_rules and template.policy_rules:
    # Use deterministic rules
    rules = template.policy_rules  # JSONB data
    engine = RuleEngineV2(policy_rules=rules)
    results = engine.evaluate_rules(transcript_segments)
else:
    # Fall back to old LLM-based evaluation
    # Uses template.description + evaluation_criteria
    ...
```

## Additional Storage (Version History)

While the **active rules** are in `policy_templates.policy_rules`, the system also maintains:

### `rule_versions` Table
- **Purpose**: Immutable snapshots of published rules (version history)
- **When**: Created every time rules are published/updated
- **Contains**: Full copy of rules at that point in time

```sql
CREATE TABLE rule_versions (
    id VARCHAR(36) PRIMARY KEY,
    policy_template_id VARCHAR(36) REFERENCES policy_templates(id),
    rules_json JSONB,              -- Immutable snapshot
    rules_version INTEGER,         -- Version number (1, 2, 3...)
    rules_hash VARCHAR(64),        -- SHA256 hash
    created_at TIMESTAMP
);
```

**Example:**
- Version 1: Rules with greeting time = 10 seconds
- Version 2: Rules with greeting time = 15 seconds (updated)
- Version 3: Rules with new empathy requirement added

All versions are kept in `rule_versions` table, but only the latest is active in `policy_templates.policy_rules`.

## Summary

**Answer: Deterministic rules are stored in the `policy_templates` table, in the `policy_rules` JSONB column.**

- **Table**: `policy_templates`
- **Column**: `policy_rules` (JSONB type)
- **Same row** as the original human-typed policy template
- **Version history** also stored in `rule_versions` table

This design allows:
- ✅ Easy access: One query gets both human text and deterministic rules
- ✅ Backward compatibility: Templates without rules still work
- ✅ Version control: History kept in separate table
- ✅ Performance: JSONB allows fast queries on rule data

