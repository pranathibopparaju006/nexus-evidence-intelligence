# NEXUS API Documentation

## Authentication

### POST /api/v1/auth/login
Login with username/password.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### POST /api/v1/auth/register
Register new user.

## Projects

### GET /api/v1/projects
List all projects for authenticated user.

### POST /api/v1/projects
Create new project.

**Request:**
```json
{
  "name": "string",
  "description": "string (optional)"
}
```

### GET /api/v1/projects/{id}
Get project details.

### DELETE /api/v1/projects/{id}
Delete project.

## Ingestion

### POST /api/v1/projects/{id}/ingest
Upload file for processing.

**Form Data:**
- `file`: File to upload

### GET /api/v1/projects/{id}/ingest
List data sources for project.

## Analysis

### POST /api/v1/projects/{id}/analyze
Start analysis job.

**Request:**
```json
{
  "analysis_type": "full",
  "options": {}
}
```

### GET /api/v1/projects/{id}/analyze/{job_id}/status
Get analysis status.

### GET /api/v1/projects/{id}/findings
Get all findings for project.

## Graph

### GET /api/v1/projects/{id}/graph
Get graph data.

**Query Parameters:**
- `node_type` (optional): Filter by node type
- `time_start` (optional): Start timestamp
- `time_end` (optional): End timestamp

### GET /api/v1/projects/{id}/timeline
Get timeline events.

## Narratives

### GET /api/v1/projects/{id}/narratives
Get narrative findings.

**Query Parameters:**
- `finding_type` (optional): Filter by type
- `claim_status` (optional): Filter by status (SUPPORTED, PARTIALLY_SUPPORTED, INSUFFICIENT, CONTRADICTED)

### GET /api/v1/projects/{id}/narratives/{finding_id}
Get specific narrative detail.
