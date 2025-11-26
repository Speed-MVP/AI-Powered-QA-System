# QA Blueprint API Documentation

## Overview

The QA Blueprint API provides endpoints for creating, managing, and evaluating QA Blueprints. Blueprints define call flows with stages, behaviors, and evaluation criteria.

## Base URL

```
/api/blueprints
```

## Authentication

All endpoints require JWT authentication via Bearer token in the Authorization header:

```
Authorization: Bearer <token>
```

## Endpoints

### Blueprint CRUD

#### Create Blueprint
```
POST /api/blueprints
```

**Request Body:**
```json
{
  "name": "Customer Support Blueprint",
  "description": "Standard customer support evaluation",
  "metadata": {
    "language": "en-US"
  },
  "stages": [
    {
      "stage_name": "Opening",
      "ordering_index": 1,
      "stage_weight": 25.0,
      "behaviors": [
        {
          "behavior_name": "Greet customer",
          "behavior_type": "required",
          "detection_mode": "semantic",
          "weight": 50.0
        }
      ]
    }
  ]
}
```

**Response:** 201 Created
```json
{
  "id": "uuid",
  "name": "Customer Support Blueprint",
  "status": "draft",
  "version_number": 1,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### List Blueprints
```
GET /api/blueprints?status=draft&skip=0&limit=100
```

**Query Parameters:**
- `status` (optional): Filter by status (draft, published, archived)
- `skip` (optional): Pagination offset
- `limit` (optional): Max results (default: 100)

#### Get Blueprint
```
GET /api/blueprints/{blueprint_id}
```

**Response Headers:**
- `ETag`: Entity tag for optimistic concurrency control

#### Update Blueprint
```
PUT /api/blueprints/{blueprint_id}
```

**Request Headers:**
- `If-Match`: ETag value for optimistic concurrency control
- `Idempotency-Key` (optional): For idempotent requests

**Request Body:** Same as create, but all fields optional

#### Delete Blueprint
```
DELETE /api/blueprints/{blueprint_id}?force=false
```

### Stage Management

#### Create Stage
```
POST /api/blueprints/{blueprint_id}/stages
```

#### Update Stage
```
PUT /api/blueprints/{blueprint_id}/stages/{stage_id}
```

#### Delete Stage
```
DELETE /api/blueprints/{blueprint_id}/stages/{stage_id}
```

### Behavior Management

#### Create Behavior
```
POST /api/blueprints/{blueprint_id}/stages/{stage_id}/behaviors
```

**Request Body:**
```json
{
  "behavior_name": "Verify identity",
  "description": "Agent must verify customer identity",
  "behavior_type": "required",
  "detection_mode": "hybrid",
  "phrases": ["Can I verify", "May I have your"],
  "weight": 30.0,
  "critical_action": null
}
```

#### Update Behavior
```
PUT /api/blueprints/{blueprint_id}/stages/{stage_id}/behaviors/{behavior_id}
```

#### Delete Behavior
```
DELETE /api/blueprints/{blueprint_id}/stages/{stage_id}/behaviors/{behavior_id}
```

### Publish & Compilation

#### Publish Blueprint
```
POST /api/blueprints/{blueprint_id}/publish
```

**Request Body:**
```json
{
  "force_normalize_weights": false,
  "publish_note": "Initial publication",
  "compiler_options": {}
}
```

**Response:** 202 Accepted
```json
{
  "job_id": "compile-job-uuid",
  "blueprint_id": "uuid",
  "status": "queued",
  "links": {
    "job_status": "/api/blueprints/{id}/publish_status/{job_id}"
  }
}
```

#### Get Publish Status
```
GET /api/blueprints/{blueprint_id}/publish_status/{job_id}
```

**Response:**
```json
{
  "job_id": "compile-job-uuid",
  "status": "succeeded",
  "progress": 100,
  "compiled_flow_version_id": "uuid",
  "errors": [],
  "warnings": []
}
```

### Sandbox Testing

#### Run Sandbox Evaluation
```
POST /api/blueprints/{blueprint_id}/sandbox-evaluate
```

**Request Body:**
```json
{
  "mode": "sync",
  "input": {
    "transcript": "Agent: Hello, how can I help you?"
  }
}
```

**Response:**
```json
{
  "run_id": "sandbox-run-uuid",
  "status": "succeeded"
}
```

#### Get Sandbox Run
```
GET /api/blueprints/{blueprint_id}/sandbox-runs/{run_id}
```

### Version Management

#### List Versions
```
GET /api/blueprints/{blueprint_id}/versions
```

#### Get Version
```
GET /api/blueprints/{blueprint_id}/versions/{version_number}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid token"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Blueprint not found"
}
```

### 409 Conflict
```json
{
  "detail": "Blueprint was modified by another user",
  "headers": {
    "ETag": "current-etag-value"
  }
}
```

## Rate Limiting

- Sandbox evaluations: 100 per company per month (configurable)
- API requests: 1000 per hour per user

## Best Practices

1. **Use ETags**: Always include `If-Match` header when updating blueprints
2. **Idempotency**: Use `Idempotency-Key` header for critical operations
3. **Validation**: Validate blueprints before publishing
4. **Testing**: Use sandbox before publishing to production
5. **Versioning**: Keep track of published versions for rollback

