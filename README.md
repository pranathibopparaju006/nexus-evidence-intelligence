
## One-click Windows run

Start Docker Desktop, then double-click `RUN_NEXUS.bat`. It builds/starts the stack, waits for the backend, and opens the frontend.

Direct links: `http://localhost:3000` · `http://localhost:8000/docs` · `http://localhost:8000/health`

# NEXUS
## Narrative Evolution & Evidence Intelligence System

**NEXUS** is a sophisticated AI-powered forensic system that analyzes fragmented digital information to detect narrative evolution, identify coordination patterns, and provide evidence-backed intelligence—with a rigorous abstention mechanism for claims that cannot be sufficiently verified.

### 🎯 Core Question

> How do fragmented pieces of information evolve, connect, mutate, and form measurable patterns across time—and can an AI system explain every finding using the underlying evidence?

### ✨ Four Signature Capabilities

1. **Narrative DNA** — Structured representation of narrative core elements
2. **Narrative Evolution** — Track how narratives mutate over time  
3. **Evidence Graph** — Every finding linked to source evidence
4. **Evidence-Aware Abstention** — System explicitly abstains when evidence is insufficient

### 🏗️ Architecture

```
Multimodal Input → Entity Extraction → Temporal Evidence Graph
                                          ↓
                    ┌─────────────────────┼─────────────────────┐
                    ↓                     ↓                     ↓
              Narrative DNA       Network Signals         Cross-Modal
                    ↓                     ↓                     ↓
              Mutation Engine      Coordination Analysis      Links
                    └─────────────────────┬─────────────────────┘
                                          ↓
                                   AI Hypothesis Generation
                                          ↓
                              Claim Verification Engine
                                   ↓              ↓
                              SUPPORTED      INSUFFICIENT
                                   ↓              ↓
                                Report         ABSTAIN
                                   ↓
                         Interactive Dashboard
```

### 🚀 Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Start all services
docker-compose up -d

# 3. Access the system
Frontend:    http://localhost:3000
API Docs:    http://localhost:8000/docs
Neo4j:       http://localhost:7474 (neo4j/nexus-nexus)

# 4. Generate demo data
cd synthetic_data
python generate_scenario.py
```

### 🧪 Demo Scenarios

Three synthetic scenarios included (non-political):

1. **Product Misinformation** — Safety rumors about fictional product
2. **Security Rumor** — Cybersecurity incident evolution  
3. **Corporate Crisis** — Coordinated narrative attack on company

### 🛠️ Tech Stack

- **Backend:** FastAPI, Python 3.11, LangGraph
- **Graph DB:** Neo4j (temporal evidence graphs)
- **Vector Store:** Qdrant (semantic search)
- **AI:** OpenAI API (configured with `OPENAI_MODEL`, default `gpt-5.6-luna`) with deterministic local narrative fallback
- **Frontend:** React, React Flow, Recharts
- **Infrastructure:** Docker, Redis, PostgreSQL

### 📊 Evaluation Metrics

- Narrative mutation accuracy
- Evidence precision (citations support claims)
- Abstention appropriateness  
- False attribution rate (target: 0%)

### 📄 Documentation

- `docs/ARCHITECTURE.md` — System design
- `docs/API.md` — API endpoints
- `docs/EVALUATION.md` — Benchmark methodology

### 🎓 Academic Context

This project demonstrates:
- Multi-agent AI with verification loops
- Knowledge graphs from unstructured data
- Temporal narrative analysis
- Responsible AI through abstention

### ⚠️ Ethical Design

NEXUS explicitly **does NOT**:
- Attribute actions to specific actors (only patterns)
- Claim causal relationships (only temporal correlations)
- Force conclusions when evidence is insufficient

### License

MIT License


## Human-first analysis output

The current interface opens on an **Overview** designed for non-technical reviewers. It presents the main narrative, key information, meaningful timeline events, review signals, source evidence and recommended changes before exposing technical details.

The analysis pipeline also includes a source-content review stage that flags conflicting measurements, inconsistent dates, conflicting explanations, unsupported strong claims and repeated wording. These are review signals rather than proof, and NEXUS does not claim to determine whether text was AI-generated.
