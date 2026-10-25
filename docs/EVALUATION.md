# NEXUS Evaluation Framework

## Metrics

### 1. Narrative Mutation Accuracy
- **Definition**: % of correctly identified narrative mutations
- **Measurement**: Compare against ground truth labels in synthetic data
- **Target**: > 75%

### 2. Evidence Precision
- **Definition**: % of cited evidence that actually supports the claim
- **Measurement**: Manual review of evidence-claim pairs
- **Target**: > 90%

### 3. Abstention Appropriateness
- **Definition**: When system abstains, is it truly uncertain?
- **Measurement**: Compare abstention rate vs. actual uncertainty in ground truth
- **Target**: Abstention rate 10-30% (not too high, not too low)

### 4. False Attribution Rate
- **Definition**: Rate of incorrectly attributing coordination to organic content
- **Measurement**: Test on organic-only datasets
- **Target**: 0% (critical requirement)

### 5. Coordination Detection F1
- **Definition**: F1 score for coordination pattern detection
- **Measurement**: Precision and recall against labeled data
- **Target**: F1 > 0.70

## Test Datasets

### Synthetic Scenarios
1. **Product Misinformation** (5 posts, 3 coordinated, 2 organic)
2. **Security Rumor** (4 posts, 2 coordinated, 2 organic)
3. **Corporate Crisis** (5 posts, 3 coordinated, 2 organic)

### Evaluation Protocol

1. **Inject Ground Truth**: Load synthetic data with known labels
2. **Run Analysis**: Execute full NEXUS pipeline
3. **Compare Outputs**: Match findings against ground truth
4. **Calculate Metrics**: Compute all metrics above
5. **Generate Report**: Export evaluation results

## Baseline Comparison

Compare NEXUS against:
- **Vanilla GPT-4**: Direct prompting without graph grounding
- **Keyword Matching**: Simple text similarity
- **Statistical Only**: Network analysis without LLM

## Success Criteria

| Metric | Threshold | Priority |
|--------|-----------|----------|
| Mutation Accuracy | > 75% | High |
| Evidence Precision | > 90% | Critical |
| Abstention Appropriateness | 10-30% | High |
| False Attribution | 0% | Critical |
| Coordination F1 | > 0.70 | High |

## Responsible AI Evaluation

- **Transparency**: Can users see why system abstained?
- **Explainability**: Are evidence chains clear?
- **Fairness**: Does system perform equally across content types?
- **Safety**: Does system refuse harmful analysis requests?
```

---

## 🚀 Quick Start Commands

```bash
# 1. Clone and enter directory
cd nexus

# 2. Setup environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start all services
docker-compose up -d

# 4. Wait for services to start (30 seconds)
sleep 30

# 5. Generate demo data
cd synthetic_data && python generate_scenario.py

# 6. Access the system
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo "Neo4j:    http://localhost:7474"

# 7. Register and login
# Open browser to http://localhost:3000
# Create account and start investigation
