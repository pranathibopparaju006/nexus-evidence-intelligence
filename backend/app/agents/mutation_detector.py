from typing import List, Dict, Any
from datetime import datetime



class MutationDetectorAgent:
    def __init__(self):
        pass
    
    async def detect_mutations(self, narratives: List[Dict]) -> List[Dict]:
        if len(narratives) < 2:
            return []
        
        sorted_narratives = sorted(narratives, key=lambda x: x.get("timestamp", ""))
        
        mutations = []
        
        for i in range(len(sorted_narratives) - 1):
            current = sorted_narratives[i]
            next_narrative = sorted_narratives[i + 1]
            
            mutation = await self._analyze_mutation(current, next_narrative)
            
            if mutation and mutation["is_mutation"]:
                mutations.append({
                    "type": "narrative_mutation",
                    "from_content": current["content_id"],
                    "to_content": next_narrative["content_id"],
                    "confidence": mutation["confidence"],
                    "claim_status": "SUPPORTED" if mutation["confidence"] > 0.8 else "PARTIALLY_SUPPORTED",
                    "evidence": mutation["evidence"],
                    "narrative_dna": {
                        "mutation_type": mutation["mutation_type"],
                        "semantic_continuity": mutation["continuity"],
                        "linguistic_change": mutation["linguistic_change"],
                        "entity_mutation": mutation["entity_change"],
                        "emotional_mutation": mutation["emotional_change"]
                    }
                })
        
        return mutations
    
    async def _analyze_mutation(self, narrative_a: Dict, narrative_b: Dict) -> Dict:
        dna_a = narrative_a.get("dna", {})
        dna_b = narrative_b.get("dna", {})
        
        if not dna_a or not dna_b:
            return {"is_mutation": False}
        
        core_claim_similarity = await self._compare_texts(
            dna_a.get("core_claim", ""),
            dna_b.get("core_claim", "")
        )
        
        entity_overlap = self._calculate_entity_overlap(
            dna_a.get("entities", []),
            dna_b.get("entities", [])
        )
        
        emotional_change = self._compare_emotional_framing(
            dna_a.get("emotional_framing", ""),
            dna_b.get("emotional_framing", "")
        )
        
        is_mutation = (
            core_claim_similarity > 0.6 and
            core_claim_similarity < 0.95
        )
        
        if not is_mutation:
            return {"is_mutation": False}
        
        mutation_type = self._classify_mutation(
            core_claim_similarity,
            entity_overlap,
            emotional_change
        )
        
        confidence = (core_claim_similarity + entity_overlap) / 2
        
        return {
            "is_mutation": True,
            "confidence": confidence,
            "mutation_type": mutation_type,
            "continuity": core_claim_similarity,
            "linguistic_change": 1 - core_claim_similarity,
            "entity_change": 1 - entity_overlap,
            "emotional_change": emotional_change,
            "evidence": {
                "core_claim_similarity": core_claim_similarity,
                "entity_overlap": entity_overlap,
                "emotional_shift": emotional_change,
                "time_delta": self._calculate_time_delta(
                    narrative_a.get("timestamp"),
                    narrative_b.get("timestamp")
                )
            }
        }
    
    @staticmethod
    def _as_text(value) -> str:
        """Normalize extracted fields that may be strings or structured objects."""
        if value is None:
            return ""
        if isinstance(value, dict):
            for key in ("text", "name", "value", "content", "label"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
            return " ".join(
                MutationDetectorAgent._as_text(v)
                for v in value.values()
                if isinstance(v, (str, int, float))
            ).strip()
        if isinstance(value, (list, tuple, set)):
            return " ".join(
                MutationDetectorAgent._as_text(item)
                for item in value
            ).strip()
        return str(value).strip()

    async def _compare_texts(self, text_a: str, text_b: str) -> float:
        text_a = self._as_text(text_a)
        text_b = self._as_text(text_b)
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        
        if not words_a or not words_b:
            return 0.0
        
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        
        return len(intersection) / len(union)
    
    def _calculate_entity_overlap(self, entities_a: List[str], entities_b: List[str]) -> float:
        # Narrative DNA may return structured entity dictionaries, not only strings.
        set_a = {
            self._as_text(e).lower()
            for e in (entities_a or [])
            if self._as_text(e)
        }
        set_b = {
            self._as_text(e).lower()
            for e in (entities_b or [])
            if self._as_text(e)
        }
        
        if not set_a or not set_b:
            return 0.0
        
        intersection = set_a.intersection(set_b)
        union = set_a.union(set_b)
        
        return len(intersection) / len(union)
    
    def _compare_emotional_framing(self, emotion_a: str, emotion_b: str) -> float:
        emotion_a = self._as_text(emotion_a)
        emotion_b = self._as_text(emotion_b)
        if emotion_a.lower() == emotion_b.lower():
            return 0.0
        return 0.5
    
    def _classify_mutation(self, core_similarity: float, entity_overlap: float, emotional_change: float) -> str:
        if emotional_change > 0.5:
            return "emotional_mutation"
        elif entity_overlap < 0.5:
            return "entity_mutation"
        elif core_similarity > 0.8:
            return "linguistic_reformulation"
        else:
            return "semantic_drift"
    
    def _calculate_time_delta(self, time_a: str, time_b: str) -> str:
        try:
            t_a = datetime.fromisoformat(time_a.replace('Z', '+00:00'))
            t_b = datetime.fromisoformat(time_b.replace('Z', '+00:00'))
            delta = t_b - t_a
            
            hours = delta.total_seconds() / 3600
            if hours < 1:
                return f"{int(delta.total_seconds() / 60)} minutes"
            elif hours < 24:
                return f"{int(hours)} hours"
            else:
                return f"{int(hours / 24)} days"
        except:
            return "unknown"
