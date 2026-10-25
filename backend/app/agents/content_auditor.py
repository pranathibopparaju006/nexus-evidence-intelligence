import re
from collections import defaultdict
from typing import Any, Dict, List, Tuple


class ContentAuditorAgent:
    """Human-readable document quality review.

    This is intentionally evidence-first: it flags inconsistencies and review
    signals found in the source text, rather than pretending to determine truth
    or whether a passage was written by AI.
    """

    def audit(self, content_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        texts = [n for n in content_nodes if n.get("text")]
        if not texts:
            return []
        full = "\n".join(n.get("text", "") for n in texts)
        findings: List[Dict[str, Any]] = []
        findings.extend(self._numeric_conflicts(full))
        findings.extend(self._cause_conflicts(full))
        findings.extend(self._date_conflicts(full))
        findings.extend(self._unsupported_claims(full))
        findings.extend(self._writing_signals(full))
        return self._dedupe(findings)[:12]

    def _sentences(self, text: str) -> List[str]:
        text = re.sub(r"\s+", " ", text).strip()
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 30]

    def _numeric_conflicts(self, text: str) -> List[Dict[str, Any]]:
        groups: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        unit_patterns = [
            (r"(\d[\d,]*(?:\.\d+)?)\s*(?:seconds?|secs?)", "response time"),
            (r"(\d[\d,]*(?:\.\d+)?)\s*(?:records?)", "record count"),
            (r"(\d+(?:\.\d+)?)\s*%", "percentage"),
            (r"(\d[\d,]*(?:\.\d+)?)\s*(?:million|billion)", "reported amount"),
        ]
        sentences = self._sentences(text)
        for sentence in sentences:
            low = sentence.lower()
            for pattern, label in unit_patterns:
                m = re.search(pattern, low)
                if m:
                    groups[label].append((m.group(1), sentence))
        out = []
        for label, vals in groups.items():
            unique = []
            for value, sentence in vals:
                if value not in [v for v, _ in unique]:
                    unique.append((value, sentence))
            if len(unique) > 1:
                examples = [s for _, s in unique[:3]]
                values = [v for v, _ in unique[:3]]
                out.append(self._finding(
                    title=f"Conflicting {label} values",
                    category="Numerical inconsistency",
                    confidence=0.86,
                    status="PARTIALLY_SUPPORTED",
                    explanation=f"The source reports different {label} values: {', '.join(values)}.",
                    recommendation="Confirm the reporting period, population and authoritative source, then retain one reconciled value.",
                    evidence_summary=" | ".join(examples),
                ))
        return out

    def _cause_conflicts(self, text: str) -> List[Dict[str, Any]]:
        sentences = self._sentences(text)
        cause = [s for s in sentences if re.search(r"\b(root cause|caused by|cause of|attributed to|immediate cause)\b", s, re.I)]
        if len(cause) >= 2:
            return [self._finding(
                title="Conflicting incident explanations",
                category="Contradiction",
                confidence=0.84,
                status="PARTIALLY_SUPPORTED",
                explanation="Multiple source passages provide different explanations for an incident or outcome.",
                recommendation="Identify the authoritative incident review and mark superseded explanations explicitly.",
                evidence_summary=" | ".join(cause[:3]),
            )]
        return []

    def _date_conflicts(self, text: str) -> List[Dict[str, Any]]:
        sentences = self._sentences(text)
        date_words = r"\b(?:on|by|from|until|through)\s+(?:\d{1,2}\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{1,2})?(?:,?\s+\d{4})?"
        dated = [s for s in sentences if re.search(date_words, s, re.I)]
        topic_groups = defaultdict(list)
        for s in dated:
            low = s.lower()
            for topic in ("pilot", "deployment", "migration", "rollout", "implementation", "production"):
                if topic in low:
                    topic_groups[topic].append(s)
        out=[]
        for topic, items in topic_groups.items():
            dates=[]
            for s in items:
                dates += re.findall(r"(?:January|February|March|April|May|June|July|August|September|October|November|December)[^,.!?;]*\d{4}", s, re.I)
            if len(set(dates)) > 1:
                out.append(self._finding(
                    title=f"Different dates reported for {topic}",
                    category="Timeline inconsistency",
                    confidence=0.80,
                    status="PARTIALLY_SUPPORTED",
                    explanation=f"The source uses more than one date for the same {topic} context.",
                    recommendation="Reconcile the dates and distinguish planned, completed and validated milestones.",
                    evidence_summary=" | ".join(items[:3]),
                ))
        return out

    def _unsupported_claims(self, text: str) -> List[Dict[str, Any]]:
        sentences = self._sentences(text)
        markers = ("significantly", "successful", "substantial", "major improvement", "dramatically", "greatly improved")
        candidates=[]
        for s in sentences:
            low=s.lower()
            if any(m in low for m in markers) and not re.search(r"\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?\s*(?:seconds?|records?|users?)", low):
                candidates.append(s)
        if candidates:
            return [self._finding(
                title="Claim needs supporting measurement",
                category="Unsupported claim",
                confidence=0.72,
                status="INSUFFICIENT",
                explanation="The document uses a strong outcome statement without an immediately visible measurement or baseline.",
                recommendation="Add the metric, baseline, measurement period and source that support the statement.",
                evidence_summary=" | ".join(candidates[:2]),
            )]
        return []

    def _writing_signals(self, text: str) -> List[Dict[str, Any]]:
        sentences=self._sentences(text)
        if len(sentences) < 10: return []
        normalized=[re.sub(r"[^a-z0-9 ]","",s.lower()) for s in sentences]
        counts=defaultdict(int)
        for s in normalized:
            key=" ".join(s.split()[:8])
            if key: counts[key]+=1
        repeated_phrase = max(counts, key=counts.get, default="")
        repeated = counts.get(repeated_phrase, 1)
        if repeated >= 3 and len(repeated_phrase.split()) >= 6:
            return [self._finding(
                title="Repeated wording detected",
                category="Writing-quality signal",
                confidence=0.70,
                status="PARTIALLY_SUPPORTED",
                explanation="The same normalized opening phrase appears in multiple passages. This is a writing-quality signal, not proof of copied content.",
                recommendation="Review the cited phrase in context and consolidate passages only if they repeat the same information.",
                evidence_summary=f"Repeated opening phrase: '{repeated_phrase}' (detected {repeated} times).",
            )]
        return []

    def _finding(self, title, category, confidence, status, explanation, recommendation, evidence_summary):
        return {
            "type": "content_review",
            "confidence": confidence,
            "claim_status": status,
            "abstain_reason": None if status != "INSUFFICIENT" else "The source contains a claim that needs additional supporting information.",
            "narrative_dna": {},
            "evidence": {
                "signal_type": "content_review",
                "title": title,
                "category": category,
                "explanation": explanation,
                "recommendation": recommendation,
                "evidence_summary": evidence_summary,
            },
        }

    def _dedupe(self, findings):
        seen=set(); out=[]
        for f in findings:
            e=f.get("evidence",{})
            key=(e.get("category"), e.get("title"))
            if key not in seen:
                seen.add(key); out.append(f)
        return out

