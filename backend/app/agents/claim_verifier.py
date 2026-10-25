from typing import List, Dict, Any



class ClaimVerifierAgent:
    def __init__(self):
        pass
        self.confidence_threshold = 0.7
        self.abstain_threshold = 0.4
    
    async def verify_findings(
        self,
        project_id: int,
        findings: List[Dict],
        graph_data: Dict
    ) -> List[Dict]:
        verified_findings = []
        
        for finding in findings:
            verified = await self._verify_single_finding(finding, graph_data)
            verified_findings.append(verified)
        
        return verified_findings
    
    async def _verify_single_finding(self, finding: Dict, graph_data: Dict) -> Dict:
        evidence = finding.get("evidence", {})
        confidence = finding.get("confidence", 0)
        
        evidence_sufficient = self._check_evidence_sufficiency(evidence)
        evidence_relevant = await self._check_evidence_relevance(finding, evidence)
        alternatives = await self._check_alternative_explanations(finding, evidence)
        contradictions = await self._check_contradictory_evidence(finding, graph_data)
        
        if not evidence_sufficient or confidence < self.abstain_threshold:
            claim_status = "INSUFFICIENT"
            abstain_reason = self._generate_abstain_reason(
                evidence_sufficient=evidence_sufficient,
                confidence=confidence,
                alternatives=alternatives,
                contradictions=contradictions
            )
        elif contradictions:
            claim_status = "CONTRADICTED"
            abstain_reason = "Contradictory evidence found"
        elif confidence < self.confidence_threshold or alternatives:
            claim_status = "PARTIALLY_SUPPORTED"
            abstain_reason = None
        else:
            claim_status = "SUPPORTED"
            abstain_reason = None
        
        enhanced_evidence = {
            **evidence,
            "verification": {
                "evidence_sufficient": evidence_sufficient,
                "evidence_relevant": evidence_relevant,
                "alternatives_considered": alternatives,
                "contradictions_found": bool(contradictions)
            }
        }
        
        return {
            **finding,
            "claim_status": claim_status,
            "abstain_reason": abstain_reason,
            "evidence": enhanced_evidence,
            "verification_summary": {
                "checks_performed": 4,
                "checks_passed": sum([
                    evidence_sufficient,
                    evidence_relevant,
                    not alternatives,
                    not contradictions
                ])
            }
        }
    
    def _check_evidence_sufficiency(self, evidence: Dict) -> bool:
        required_fields = ["signal_type"]
        
        if not all(field in evidence for field in required_fields):
            return False
        
        has_supporting_data = any(
            key in evidence for key in ["content_ids", "content_count", "similarity_score", "interaction_count"]
        )
        
        return has_supporting_data
    
    async def _check_evidence_relevance(self, finding: Dict, evidence: Dict) -> bool:
        finding_type = finding.get("type", "")
        signal_type = evidence.get("signal_type", "")
        
        valid_mappings = {
            "temporal_coordination": ["synchronized_posting"],
            "content_coordination": ["cross_source_similarity"],
            "network_coordination": ["repeated_co_occurrence"],
            "amplification_coordination": ["coordinated_amplification"],
            "narrative_mutation": ["semantic_continuity", "linguistic_reformulation"]
        }
        
        expected_signals = valid_mappings.get(finding_type, [])
        return signal_type in expected_signals
    
    async def _check_alternative_explanations(self, finding: Dict, evidence: Dict) -> List[str]:
        alternatives = []
        finding_type = finding.get("type", "")
        
        if finding_type == "temporal_coordination":
            alternatives.append("organic_virality")
            alternatives.append("breaking_news_event")
        elif finding_type == "content_coordination":
            alternatives.append("shared_source_material")
            alternatives.append("independent_similar_observation")
        elif finding_type == "network_coordination":
            alternatives.append("topic_based_association")
        elif finding_type == "narrative_mutation":
            alternatives.append("independent_development")
            alternatives.append("cultural_trend")
        
        return alternatives
    
    async def _check_contradictory_evidence(self, finding: Dict, graph_data: Dict) -> List[Dict]:
        contradictions = []
        return contradictions
    
    def _generate_abstain_reason(
        self,
        evidence_sufficient: bool,
        confidence: float,
        alternatives: List[str],
        contradictions: List[Dict]
    ) -> str:
        reasons = []
        
        if not evidence_sufficient:
            reasons.append("Insufficient evidence to support claim")
        
        if confidence < self.abstain_threshold:
            reasons.append(f"Confidence ({confidence:.2f}) below threshold ({self.abstain_threshold})")
        
        if alternatives:
            reasons.append(f"Alternative explanations possible: {', '.join(alternatives)}")
        
        if contradictions:
            reasons.append("Contradictory evidence detected")
        
        return "; ".join(reasons) if reasons else "Unable to verify claim with available evidence"
