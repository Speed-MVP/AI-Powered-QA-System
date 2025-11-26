# QA Blueprint Creation Guide

## Introduction

QA Blueprints are human-friendly configurations that define how call center interactions should be evaluated. They replace the complex 7-structure configuration with a simple, intuitive system.

## Core Concepts

### Blueprint
A Blueprint is a complete evaluation configuration containing:
- **Name & Description**: Human-readable identification
- **Stages**: Ordered phases of a call (e.g., Opening, Verification, Resolution, Closing)
- **Behaviors**: Specific actions or phrases to detect within each stage
- **Metadata**: Additional configuration (language, retention, etc.)

### Stage
A Stage represents a phase of the call flow:
- **Stage Name**: e.g., "Opening", "Verification", "Resolution"
- **Ordering Index**: Position in the call flow (1, 2, 3...)
- **Stage Weight**: Percentage contribution to overall score (should sum to 100%)
- **Behaviors**: List of behaviors to evaluate in this stage

### Behavior
A Behavior is an atomic action or phrase to detect:
- **Behavior Name**: e.g., "Greet customer", "Verify identity"
- **Behavior Type**: 
  - `required`: Must be present
  - `optional`: Nice to have
  - `forbidden`: Should not be present
  - `critical`: Must be present, failure has severe consequences
- **Detection Mode**:
  - `semantic`: Uses AI to understand meaning
  - `exact_phrase`: Matches exact phrases
  - `hybrid`: Combines both approaches
- **Phrases**: List of phrases to match (required for exact_phrase/hybrid)
- **Weight**: Contribution to stage score (0-100)
- **Critical Action**: For critical behaviors, what happens on failure:
  - `fail_stage`: Fail the entire stage
  - `fail_overall`: Fail the entire evaluation
  - `flag_only`: Flag but don't fail

## Creating Your First Blueprint

### Step 1: Create the Blueprint

1. Navigate to Blueprints page
2. Click "New Blueprint"
3. Enter name and description
4. Click "Create"

### Step 2: Add Stages

1. Click "Add Stage" in the left panel
2. Enter stage name (e.g., "Opening")
3. Set ordering index (1 for first stage)
4. Optionally set stage weight (will be auto-normalized if not provided)
5. Click "Add Stage"

Repeat for all stages in your call flow.

### Step 3: Add Behaviors to Each Stage

1. Select a stage in the canvas
2. Click "Add Behavior" in the stage card
3. Configure behavior:
   - **Name**: Descriptive name
   - **Type**: Required/Optional/Forbidden/Critical
   - **Detection Mode**: Semantic/Exact/Hybrid
   - **Phrases**: If using exact_phrase or hybrid, enter phrases (one per line)
   - **Weight**: Contribution to stage score
   - **Critical Action**: If critical, select action on failure
4. Click "Add Behavior"

### Step 4: Configure Weights

- **Stage Weights**: Should sum to 100% across all stages
- **Behavior Weights**: Should sum to stage weight within each stage
- System can auto-normalize weights on publish if enabled

### Step 5: Validate and Publish

1. Review the scoring summary at the bottom
2. Check for validation warnings
3. Click "Publish"
4. Review validation results
5. Wait for compilation to complete
6. Blueprint is now ready for evaluations

## Best Practices

### Stage Design
- **Keep stages focused**: Each stage should represent a distinct phase
- **Logical ordering**: Stages should follow the natural call flow
- **Balanced weights**: Distribute stage weights based on importance

### Behavior Design
- **Be specific**: Clear, actionable behavior names
- **Use semantic mode**: For flexible detection of concepts
- **Use exact mode**: For compliance phrases that must be said verbatim
- **Critical behaviors**: Reserve for compliance-critical items

### Detection Modes

**Semantic Mode:**
- Best for: Concepts, intent, general behaviors
- Example: "Show empathy", "Acknowledge concern"
- No phrases needed

**Exact Phrase Mode:**
- Best for: Compliance phrases, required disclosures
- Example: "This call may be recorded", "Can I verify your identity"
- Requires phrases list

**Hybrid Mode:**
- Best for: Important behaviors where you want both exact and semantic matching
- Tries exact first, falls back to semantic
- Requires phrases list

### Weight Distribution

**Example for 4-stage call:**
- Opening: 20%
- Verification: 25%
- Resolution: 40%
- Closing: 15%
- **Total: 100%**

**Within a stage (e.g., Opening with 20% weight):**
- Greet customer: 50% of stage (10% overall)
- Identify purpose: 30% of stage (6% overall)
- Set expectations: 20% of stage (4% overall)
- **Total: 100% of stage**

## Common Patterns

### Customer Support Call
1. **Opening** (20%)
   - Greet customer (required, semantic)
   - Identify purpose (required, semantic)
2. **Verification** (25%)
   - Verify identity (critical, exact_phrase)
   - Confirm account (required, semantic)
3. **Resolution** (40%)
   - Listen actively (required, semantic)
   - Provide solution (required, semantic)
   - Confirm understanding (required, semantic)
4. **Closing** (15%)
   - Summarize resolution (required, semantic)
   - Thank customer (required, exact_phrase)

### Sales Call
1. **Opening** (15%)
   - Professional greeting (required, exact_phrase)
   - State purpose (required, semantic)
2. **Discovery** (30%)
   - Ask qualifying questions (required, semantic)
   - Listen to needs (required, semantic)
3. **Presentation** (35%)
   - Present solution (required, semantic)
   - Address objections (required, semantic)
4. **Closing** (20%)
   - Ask for commitment (critical, semantic)
   - Confirm next steps (required, semantic)

## Testing with Sandbox

Before publishing, test your blueprint:

1. Click "Sandbox" button in blueprint editor
2. Enter a sample transcript or select a recording
3. Run evaluation
4. Review results:
   - Check behavior detections
   - Verify scores are reasonable
   - Look for false positives/negatives
5. Adjust behaviors and retest

## Troubleshooting

### Weights Don't Sum to 100%
- Enable "force_normalize_weights" on publish
- Or manually adjust weights

### Behaviors Not Detected
- Check detection mode (semantic vs exact)
- For exact mode, verify phrases match transcript
- For semantic mode, improve behavior description
- Check confidence thresholds

### Scores Too Low/High
- Review stage weights distribution
- Check behavior weights within stages
- Verify detection is working (use sandbox)
- Adjust thresholds if needed

### Compilation Fails
- Check validation errors
- Ensure all required fields are filled
- Verify no duplicate stage/behavior names
- Check for contradictory rules (required + forbidden same phrase)

## Migration from Legacy System

If migrating from FlowVersion/FlowStage/FlowStep:

1. Export existing configuration
2. Map stages to Blueprint stages
3. Map steps to behaviors
4. Convert compliance rules to behaviors
5. Test in sandbox
6. Publish and activate

## Support

For questions or issues:
- Check API documentation: `/docs/BLUEPRINT_API.md`
- Review validation errors in publish modal
- Use sandbox for testing
- Contact support for assistance

