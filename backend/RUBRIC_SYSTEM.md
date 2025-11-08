# Rubric-Based Evaluation System

## Overview

The AI-Powered QA System now uses a **rubric-based evaluation system** that provides more structured, consistent, and customizable criteria for evaluating customer service calls. This system allows you to define multiple performance levels (e.g., Excellent, Good, Average, Poor, Unacceptable) for each evaluation category, with clear descriptions and score ranges.

## Key Features

### 1. **Customizable Performance Levels**
- Define 1-10 performance levels per evaluation category
- Each level has:
  - **Level Name**: e.g., "Excellent", "Good", "Average", "Poor", "Unacceptable"
  - **Level Order**: Numeric order (1 = highest/best, higher numbers = lower performance)
  - **Score Range**: Min and max scores (0-100) for this level
  - **Description**: Clear description of what constitutes this level of performance
  - **Examples** (Optional): Specific examples of behaviors or actions that match this level

### 2. **Rubric-Based LLM Evaluation**
- The LLM (Gemini) uses the rubric levels to determine scores
- Instead of arbitrary scoring, the LLM matches agent performance to the appropriate rubric level
- More consistent and objective evaluations
- Clear feedback that references which rubric level the performance matches

### 3. **Best Practices Implementation**
Based on industry standards for call center QA evaluation:

- **5-Level System** (Recommended):
  - Excellent (90-100): Exceeds all expectations
  - Good (75-89): Meets all requirements
  - Average (60-74): Meets basic requirements with issues
  - Poor (40-59): Significant problems
  - Unacceptable (0-39): Complete failure

- **Customizable**: You can create any number of levels with custom names and score ranges

## Database Schema

### `evaluation_rubric_levels` Table

```sql
CREATE TABLE evaluation_rubric_levels (
    id VARCHAR(36) PRIMARY KEY,
    criteria_id VARCHAR(36) REFERENCES evaluation_criteria(id) ON DELETE CASCADE,
    level_name VARCHAR(50) NOT NULL,
    level_order INTEGER NOT NULL,  -- 1 = highest, 5 = lowest
    min_score INTEGER NOT NULL,   -- 0-100
    max_score INTEGER NOT NULL,   -- 0-100
    description TEXT NOT NULL,
    examples TEXT NULL
);
```

## API Endpoints

### Add Rubric Level
```
POST /api/templates/{template_id}/criteria/{criteria_id}/rubric-levels
```

**Request Body:**
```json
{
  "level_name": "Excellent",
  "level_order": 1,
  "min_score": 90,
  "max_score": 100,
  "description": "All compliance protocols followed perfectly...",
  "examples": "Agent verified customer identity, provided all required disclosures..."
}
```

### Update Rubric Level
```
PUT /api/templates/{template_id}/criteria/{criteria_id}/rubric-levels/{level_id}
```

### Delete Rubric Level
```
DELETE /api/templates/{template_id}/criteria/{criteria_id}/rubric-levels/{level_id}
```

## Frontend Usage

1. **View Rubric Levels**: Click "Show Levels" on any evaluation criteria
2. **Add Level**: Click "Add Rubric Level" button
3. **Edit Level**: Click the edit icon on any rubric level
4. **Delete Level**: Click the delete icon on any rubric level

## LLM Prompt Integration

The LLM prompt now includes rubric levels for each category:

```
- Compliance (Weight: 40%, Passing: 90/100)
  Evaluation Prompt: Evaluate if the agent followed compliance guidelines...
  RUBRIC LEVELS (Use these to determine the score):
    - Excellent (Score: 90-100): All compliance protocols followed perfectly...
    - Good (Score: 75-89): Most compliance requirements met...
    - Average (Score: 60-74): Some compliance requirements missed...
    - Poor (Score: 40-59): Major compliance violations...
    - Unacceptable (Score: 0-39): Severe compliance failures...
```

The LLM is instructed to:
1. Match agent performance to the appropriate rubric level
2. Assign a score within that level's range
3. Reference the rubric level in feedback

## Default Rubric Levels

When you run `quick_test_setup.py`, default rubric levels are created for:
- **Compliance**: 5 levels with compliance-specific descriptions
- **Empathy**: 5 levels with empathy-specific descriptions
- **Resolution**: 5 levels with resolution-specific descriptions
- **Other Categories**: 5 generic levels

## Benefits

1. **Consistency**: Same performance always gets the same score range
2. **Transparency**: Clear criteria for what constitutes each level
3. **Customization**: Tailor levels to your organization's standards
4. **Training**: Use rubric levels to train agents on expectations
5. **Objectivity**: Reduces subjective scoring variations

## Migration

The rubric system is backward compatible. If no rubric levels are defined for a category, the system uses default levels:
- Excellent (90-100)
- Good (75-89)
- Average (60-74)
- Poor (40-59)
- Unacceptable (0-39)

## Best Practices

1. **Define Clear Descriptions**: Be specific about what constitutes each level
2. **Use Examples**: Provide concrete examples to guide the LLM
3. **Non-Overlapping Ranges**: Ensure score ranges don't overlap between levels
4. **Order Matters**: Use level_order to indicate hierarchy (1 = best)
5. **Cover Full Range**: Ensure all scores 0-100 are covered by your levels

