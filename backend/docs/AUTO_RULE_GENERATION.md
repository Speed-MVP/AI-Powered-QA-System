# Automatic Rule Generation on Template Activation

## Overview

Rules are now **automatically generated** when a template is activated, eliminating the need for manual rule generation steps.

## New Workflow

### Scenario 1: Create Template and Activate Immediately

1. **User creates template** with name, description, criteria, and rubrics
2. **User sets `is_active = true`** during creation
3. **System automatically:**
   - Extracts policy text from `description` + `evaluation_criteria[].evaluation_prompt`
   - Extracts rubric levels
   - Generates structured rules using LLM (skips clarification step)
   - Saves rules to `policy_templates.policy_rules`
   - Sets `enable_structured_rules = true`

**Result:** Template is created AND rules are generated automatically ✅

---

### Scenario 2: Create Template, Then Activate Later

1. **User creates template** with `is_active = false`
   - Template saved, no rules generated

2. **User adds criteria and rubrics**
   - Criteria saved, still no rules

3. **User sets template to active** (`is_active = true`)
4. **System automatically:**
   - Checks if `policy_rules = NULL` (no rules exist)
   - If no rules exist, generates them automatically
   - Saves rules to database
   - Sets `enable_structured_rules = true`

**Result:** Rules generated automatically when activated ✅

---

### Scenario 3: Template Already Has Rules

1. **Template has existing rules** (`policy_rules != NULL`)
2. **User activates template** (`is_active = true`)
3. **System checks:**
   - `policy_rules != NULL` → Rules already exist
   - **Skips rule generation** ✅
   - Template is activated with existing rules

**Result:** No duplicate rule generation ✅

---

## Implementation Details

### Code Location

**File:** `backend/app/routes/templates.py`

**Two endpoints modified:**

1. **`POST /api/templates`** (create_template)
   - Checks if `is_active = true` AND `policy_rules = NULL`
   - Auto-generates rules if conditions met

2. **`PUT /api/templates/{id}`** (update_template)
   - Checks if template is being activated (`is_active` changing from `false` → `true`)
   - Checks if `policy_rules = NULL`
   - Auto-generates rules if conditions met

### Logic Flow

```python
# Check if template is being activated
is_being_activated = template_data.is_active and not template.is_active

# Check if rules need to be generated
needs_rule_generation = is_being_activated and template.policy_rules is None

if needs_rule_generation:
    # Extract policy text
    policy_text = template.description + evaluation_criteria prompts
    
    # Extract rubric levels
    rubric_levels = {...}
    
    # Generate rules (skip clarification step)
    builder = PolicyRuleBuilder()
    validated_rules, metadata = builder.generate_structured_rules(
        policy_text=policy_text,
        clarification_answers={},  # Empty - auto-generate
        rubric_levels=rubric_levels
    )
    
    # Save rules
    template.policy_rules = rules_dict
    template.enable_structured_rules = True
    template.rules_generation_method = "ai"
    db.commit()
```

### Error Handling

- **If rule generation fails:**
  - Template is still created/activated ✅
  - Rules are not generated (template works with old LLM evaluation)
  - Error is logged but doesn't fail the request
  - User can manually generate rules later if needed

### Clarification Step

**Skipped for automatic generation:**
- When rules are auto-generated, `clarification_answers = {}` (empty)
- LLM generates rules directly from policy text
- If clarification is needed, user can manually regenerate rules later

## Benefits

1. **Simplified workflow** - No manual "Generate Rules" button needed
2. **Automatic** - Rules generated when template is ready
3. **Idempotent** - Won't regenerate if rules already exist
4. **Non-blocking** - Template activation succeeds even if rule generation fails
5. **Backward compatible** - Old templates without rules still work

## User Experience

### Before (Manual):
```
1. Create template
2. Add criteria/rubrics
3. Click "Generate Rules" button
4. Answer clarification questions
5. Review generated rules
6. Approve rules
7. Activate template
```

### After (Automatic):
```
1. Create template
2. Add criteria/rubrics
3. Set template to active ✅
   → Rules generated automatically!
```

## Database State Examples

### Template Created as Active (No Rules Yet)
```sql
policy_templates:
├── id = "abc-123"
├── is_active = true
├── description = "Agents must greet..."
└── policy_rules = NULL  ← Will be generated automatically
```

### After Auto-Generation
```sql
policy_templates:
├── id = "abc-123"
├── is_active = true
├── description = "Agents must greet..."
├── policy_rules = {
│     "version": 1,
│     "rules": {...}
│   }                    ← Generated automatically!
├── enable_structured_rules = true
└── rules_generation_method = "ai"
```

### Template Already Has Rules
```sql
policy_templates:
├── id = "abc-123"
├── is_active = true
├── policy_rules = {...}  ← Already exists
└── enable_structured_rules = true
```
**Result:** No regeneration, uses existing rules ✅

## API Behavior

### Create Template (Active)
```http
POST /api/templates
{
  "template_name": "Customer Service",
  "description": "Agents must greet...",
  "is_active": true,
  "criteria": [...]
}
```

**Response:** Template created with rules auto-generated ✅

### Update Template (Activate)
```http
PUT /api/templates/{id}
{
  "template_name": "Customer Service",
  "is_active": true,  ← Changed from false
  "criteria": [...]
}
```

**Response:** Template activated, rules auto-generated if needed ✅

### Update Template (Already Has Rules)
```http
PUT /api/templates/{id}
{
  "is_active": true,  ← Template already has policy_rules
  ...
}
```

**Response:** Template activated, existing rules used (no regeneration) ✅

