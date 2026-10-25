# NEXUS Architecture

## System Overview

NEXUS is a multi-agent AI system for narrative evolution analysis and evidence-based intelligence.

## Core Components

### 1. Data Ingestion Layer
- Supports PDF, TXT, JSON, CSV, images
- OCR for image extraction
- Async processing with Celery

### 2. Storage Layer
- **PostgreSQL**: Relational data (users, projects, jobs)
- **Neo4j**: Temporal evidence graphs
- **Qdrant**: Vector embeddings for semantic search
- **MinIO**: Object storage for raw files
- **Redis**: Caching and task queue

### 3. AI Agent Layer (6 Agents)

| Agent | Purpose |
|-------|---------|
| Orchestrator | Workflow coordination |
| GraphBuilder | Construct evidence graphs |
| NarrativeDNA | Extract narrative structures |
| MutationDetector | Track narrative evolution |
| CoordinationAnalyzer | Identify coordination patterns |
| ClaimVerifier | Verify claims + ABSTAIN |

### 4. API Layer
- FastAPI with async endpoints
- JWT authentication
- Rate limiting

### 5. Frontend Layer
- React with React Flow (graph viz)
- Real-time updates
- Interactive investigation dashboard

## Data Flow

```
Upload → Parse → Extract Entities → Build Graph
                                          ↓
                              Narrative DNA Extraction
                                          ↓
                              Mutation Detection
                                          ↓
                              Coordination Analysis
                                          ↓
                              Claim Verification
                                          ↓
                              Interactive Dashboard
```

## Key Design Decisions

1. **Graph-First**: All analysis grounded in Neo4j evidence graph
2. **Abstention**: System can refuse to make claims
3. **No Attribution**: Only patterns, not identities
4. **Temporal**: Time-centric analysis, not just content
5. **Multimodal**: Text + images in unified graph
