# Gemini API Zero Data Retention Configuration Guide

## Current Status

**Temperature = 0**: ✅ **CONFIGURED** in code (`llm_stage_evaluator.py:201`)

**Zero Data Retention**: ⚠️ **REQUIRES ADDITIONAL CONFIGURATION**

## Important Finding

The **Generative Language API** (used by `google.generativeai` Python SDK) does **NOT** have data retention settings in the API key configuration page in Google Cloud Console.

## Default Behavior

When using the Generative Language API:
- **In-memory caching**: Data is cached in-memory (not at rest) for **24 hours** to reduce latency
- **Data isolation**: Cached data is isolated at the project level
- **No training**: Data is **NOT** used for model training
- **Data residency**: Complies with data residency requirements
- **No persistent storage**: Data is **NOT** stored at rest

## Options for Zero Data Retention

### Option 1: Disable In-Memory Cache (Recommended for True Zero Retention)

Disable the 24-hour in-memory cache at the **project level** using Vertex AI API:

```bash
# Set your project ID
PROJECT_ID=your-google-cloud-project-id

# Get authentication token
TOKEN=$(gcloud auth application-default print-access-token)

# Disable cache
curl -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/cacheConfig \
  -d '{
    "name": "projects/'$PROJECT_ID'/cacheConfig",
    "disableCache": true
  }'
```

**Requirements:**
- IAM permission: `roles/aiplatform.admin` or `roles/aiplatform.user`
- Project must have Vertex AI API enabled

**Note:** This disables caching for the entire project, which may increase API latency.

### Option 2: Use Vertex AI API Instead

Switch from Generative Language API to Vertex AI API for more control:

```python
# Instead of:
from google.generativeai import GenerativeModel
model = GenerativeModel('gemini-2.5-flash-lite')

# Use:
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel

aiplatform.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel('gemini-2.5-flash-lite')
```

Vertex AI API provides:
- More granular cache control
- Better enterprise data retention options
- Project-level configuration

### Option 3: Enterprise Zero Data Retention Agreement

For strict compliance requirements:
1. Contact Google Cloud Support
2. Request enterprise zero data retention agreement
3. May require:
   - Enterprise support contract
   - Custom data processing agreement
   - Switching to Vertex AI API

## Current Implementation

The project currently uses:
- **API**: Generative Language API (`google.generativeai`)
- **Model**: `gemini-2.5-flash-lite`
- **Temperature**: 0 (deterministic)
- **Data Retention**: 24-hour in-memory cache (default)
- **Training**: Data NOT used for training (guaranteed by Google)

## Privacy Protections Already in Place

Even with the 24-hour cache, the following privacy protections are implemented:

1. ✅ **PII Redaction**: All PII is redacted before sending to LLM
2. ✅ **Temperature = 0**: Deterministic outputs (no randomness)
3. ✅ **Minimal Data**: Only stage-specific segments sent, not full transcript
4. ✅ **No Training**: Google guarantees data is NOT used for training
5. ✅ **Project Isolation**: Data is isolated per project
6. ✅ **No Persistent Storage**: Data is NOT stored at rest, only in-memory cache

## Recommendation

For most use cases, the **default 24-hour in-memory cache is acceptable** because:
- Data is NOT used for training
- Data is NOT stored at rest
- Data is isolated per project
- PII is redacted before sending

For strict zero retention requirements:
1. **Short term**: Document the current behavior and privacy protections
2. **Long term**: Implement Option 1 (disable cache) or Option 2 (switch to Vertex AI)

## Verification

To verify current cache settings:

```bash
PROJECT_ID=your-project-id
TOKEN=$(gcloud auth application-default print-access-token)

curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  https://us-central1-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/cacheConfig
```

## References

- [Google Vertex AI Zero Data Retention](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention)
- [Gemini API Privacy](https://ai.google.dev/gemini-api/docs/privacy)
- [Generative Language API vs Vertex AI](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/differences)



