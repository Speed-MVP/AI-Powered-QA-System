# When Policy Rules Get Generated - Complete Workflow

## Important: Rules Are NOT Generated Automatically

**Rule generation is a separate, manual step** that happens AFTER you create the template and add criteria/rubrics.

## The Complete Workflow

### Step 1: Create Policy Template
**Endpoint:** `POST /api/templates`

**What happens:**
- User creates template with name and description
- Template is saved to `policy_templates` table
- **At this point:**
  - `policy_rules = NULL` ❌ (no rules yet)
  - `enable_structured_rules = false`
  - Only human-typed data is saved

**Database state:**
```sql
policy_templates:
├── id = "abc-123"
├── template_name = "Customer Service Policy"
├── description = "Agents must greet customers..."  ← Human text
└── policy_rules = NULL                             ← NO RULES YET
```

---

### Step 2: Add Evaluation Criteria & Rubrics
**Endpoints:** 
- `POST /api/templates/{id}/criteria` (add criteria)
- `POST /api/templates/{id}/criteria/{criteria_id}/rubric-levels` (add rubrics)

**What happens:**
- User adds evaluation criteria (category names, weights, evaluation prompts)
- User adds rubric levels (Excellent, Good, Needs Improvement, etc.)
- All saved to `evaluation_criteria` and `evaluation_rubric_levels` tables
- **Still no rules generated!**

**Database state:**
```sql
policy_templates:
├── id = "abc-123"
├── description = "Agents must greet..."  ← Human text
└── policy_rules = NULL                 ← STILL NO RULES

evaluation_criteria:
├── policy_template_id = "abc-123"
├── category_name = "Professionalism"
└── evaluation_prompt = "Check if agent greets..."  ← Human text

evaluation_rubric_levels:
├── criteria_id = "..."
├── level_name = "Excellent"
└── description = "Agent greets within 5 seconds"  ← Human text
```

---

### Step 3: Manual Trigger - Generate Rules (Admin/QA Manager Only)

**This is when rule generation happens!** It's a separate workflow with multiple stages:

#### Stage 1: Analyze Policy Text
**Endpoint:** `POST /api/policy-templates/{template_id}/analyze-policy`

**What happens:**
- System extracts policy text from:
  - `template.description`
  - `evaluation_criteria[].evaluation_prompt`
- LLM analyzes text and identifies vague statements
- Generates clarification questions
- Questions saved to `policy_clarifications` table

**User action:** Admin/QA Manager clicks "Generate Rules" or "Analyze Policy" button in UI

**Database state:**
```sql
policy_templates:
└── policy_rules = NULL  ← STILL NO RULES

policy_clarifications:
├── policy_template_id = "abc-123"
├── question_id = "q1"
└── question = "What is the maximum acceptable greeting time in seconds?"
```

---

#### Stage 2: Answer Clarification Questions
**Endpoint:** `POST /api/policy-templates/{template_id}/clarifications`

**What happens:**
- User answers clarification questions
- Answers saved to `policy_clarifications` table

**User action:** Admin fills in answers to questions like:
- "What is 'promptly'?" → "10 seconds"
- "What empathy phrases are required?" → "I understand, I'm sorry"

**Database state:**
```sql
policy_clarifications:
├── question = "What is the maximum acceptable greeting time?"
└── answer = "10 seconds"  ← User's answer
```

---

#### Stage 3: Generate Structured Rules
**Endpoint:** `POST /api/policy-templates/{template_id}/generate-rules`

**What happens:**
- System extracts:
  - Policy text (description + evaluation prompts)
  - Clarification answers
  - Rubric levels
- LLM converts human text + answers → structured JSON rules
- Rules are validated against `PolicyRulesSchema`
- **Rules are returned but NOT saved yet!**

**User action:** Admin clicks "Generate Rules" button

**Response:**
```json
{
  "rules": {
    "version": 1,
    "rules": {
      "Professionalism": [
        {
          "id": "greet_within_seconds",
          "type": "numeric",
          "value": 10.0,
          "comparator": "le"
        }
      ]
    }
  },
  "conflicts": []
}
```

**Database state:**
```sql
policy_templates:
└── policy_rules = NULL  ← STILL NOT SAVED (just generated, not approved)
```

---

#### Stage 4: Approve & Save Rules
**Endpoint:** `POST /api/policy-templates/{template_id}/approve-rules`

**What happens:**
- Admin reviews generated rules
- Admin approves rules
- **Rules are NOW saved to database!**

**Code (from `policy_rules.py:365`):**
```python
template.policy_rules = request.rules  # ← SAVED HERE!
template.policy_rules_version = 1
template.enable_structured_rules = True
template.rules_approved_by_user_id = current_user.id
db.commit()
```

**User action:** Admin reviews rules in UI and clicks "Approve Rules"

**Final database state:**
```sql
policy_templates:
├── id = "abc-123"
├── description = "Agents must greet..."  ← Original human text
├── policy_rules = {                     ← DETERMINISTIC RULES NOW SAVED!
│     "version": 1,
│     "rules": {
│       "Professionalism": [
│         {
│           "id": "greet_within_seconds",
│           "type": "numeric",
│           "value": 10.0,
│           "comparator": "le"
│         }
│       ]
│     }
│   }
├── policy_rules_version = 1
├── enable_structured_rules = true       ← NOW ENABLED!
└── rules_approved_by_user_id = "user-456"
```

---

## Summary: When Rules Are Generated

| Step | Action | Rules Generated? | Database State |
|------|--------|------------------|----------------|
| 1 | Create template | ❌ NO | `policy_rules = NULL` |
| 2 | Add criteria/rubrics | ❌ NO | `policy_rules = NULL` |
| 3a | Analyze policy | ❌ NO | `policy_rules = NULL` (questions created) |
| 3b | Answer questions | ❌ NO | `policy_rules = NULL` (answers saved) |
| 3c | Generate rules | ⚠️ Generated but NOT saved | `policy_rules = NULL` (rules in response only) |
| 3d | Approve rules | ✅ YES - SAVED! | `policy_rules = {...}` (rules saved to DB) |

## UI Workflow

Based on the policy template page, the workflow should be:

1. **Create Template Page:**
   - User fills in template name, description
   - User adds criteria and rubrics
   - User clicks "Save Template"
   - **Result:** Template saved, but NO rules generated

2. **Template Detail Page:**
   - Shows template with criteria/rubrics
   - Shows button: **"Generate Deterministic Rules"** or **"Convert to Structured Rules"**
   - **This button triggers Stage 1 (analyze-policy)**

3. **Rule Generation Wizard/Modal:**
   - **Step 1:** Shows analysis results and clarification questions
   - **Step 2:** User answers questions
   - **Step 3:** Shows generated rules preview
   - **Step 4:** User reviews and approves
   - **Result:** Rules saved to `policy_templates.policy_rules`

## Key Points

1. **Rules are NOT automatic** - They require manual admin action
2. **Template creation ≠ Rule generation** - These are separate steps
3. **Rules are generated AFTER** template + criteria + rubrics are complete
4. **Rules are saved ONLY after approval** - Generation creates them, approval saves them
5. **Old templates work without rules** - If `policy_rules = NULL`, system falls back to old LLM evaluation

## API Endpoints Summary

```python
# Step 1: Create template (NO rules)
POST /api/templates

# Step 2: Add criteria/rubrics (NO rules)
POST /api/templates/{id}/criteria
POST /api/templates/{id}/criteria/{criteria_id}/rubric-levels

# Step 3: Generate rules (MANUAL TRIGGER)
POST /api/policy-templates/{id}/analyze-policy        # Stage 1: Analyze
POST /api/policy-templates/{id}/clarifications       # Stage 2: Answer questions
POST /api/policy-templates/{id}/generate-rules       # Stage 3: Generate
POST /api/policy-templates/{id}/approve-rules        # Stage 4: Save to DB
```

## Example: Complete Flow

```
User creates template:
  POST /api/templates
  → Template saved, policy_rules = NULL

User adds criteria:
  POST /api/templates/abc-123/criteria
  → Criteria saved, policy_rules = NULL

User adds rubrics:
  POST /api/templates/abc-123/criteria/xyz/rubric-levels
  → Rubrics saved, policy_rules = NULL

Admin clicks "Generate Rules" button:
  POST /api/policy-templates/abc-123/analyze-policy
  → Questions generated, policy_rules = NULL

Admin answers questions:
  POST /api/policy-templates/abc-123/clarifications
  → Answers saved, policy_rules = NULL

Admin generates rules:
  POST /api/policy-templates/abc-123/generate-rules
  → Rules generated (returned in response), policy_rules = NULL

Admin approves rules:
  POST /api/policy-templates/abc-123/approve-rules
  → Rules SAVED! policy_rules = {...} ✅
```

