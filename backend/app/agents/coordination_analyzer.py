from typing import List, Dict, Any
from collections import defaultdict
import numpy as np


class CoordinationAnalyzerAgent:
    def __init__(self):
        pass

    async def analyze_coordination(
        self,
        project_id: int,
        entity_nodes: List[Dict],
        narratives: List[Dict],
        mutations: List[Dict]
    ) -> List[Dict]:
        findings = []

        temporal_findings = await self._analyze_temporal_clustering(
            narratives
        )
        findings.extend(temporal_findings)

        similarity_findings = await self._analyze_content_similarity(
            narratives
        )
        findings.extend(similarity_findings)

        network_findings = await self._analyze_network_patterns(
            entity_nodes,
            narratives
        )
        findings.extend(network_findings)

        amplification_findings = await self._analyze_amplification_patterns(
            narratives,
            mutations
        )
        findings.extend(amplification_findings)

        return findings

    async def _analyze_temporal_clustering(
        self,
        narratives: List[Dict]
    ) -> List[Dict]:

        time_windows = defaultdict(list)

        for narrative in narratives:
            timestamp = narrative.get("timestamp", "")

            if timestamp:
                timestamp = str(timestamp)
                hour_key = timestamp[:13]
                time_windows[hour_key].append(narrative)

        findings = []

        for window, items in time_windows.items():

            if len(items) >= 3:
                similarities = []

                for i in range(len(items)):
                    for j in range(i + 1, len(items)):

                        sim = await self._calculate_narrative_similarity(
                            items[i].get("dna", {}),
                            items[j].get("dna", {})
                        )

                        similarities.append(sim)

                avg_similarity = (
                    float(np.mean(similarities))
                    if similarities
                    else 0.0
                )

                if avg_similarity > 0.85:
                    findings.append({
                        "type": "temporal_coordination",
                        "confidence": min(
                            avg_similarity,
                            0.95
                        ),
                        "evidence": {
                            "time_window": window,
                            "content_count": len(items),
                            "average_similarity": avg_similarity,
                            "content_ids": [
                                item.get("content_id")
                                for item in items
                            ],
                            "signal_type": "synchronized_posting"
                        }
                    })

        return findings

    async def _analyze_content_similarity(
        self,
        narratives: List[Dict]
    ) -> List[Dict]:

        findings = []

        for i in range(len(narratives)):

            for j in range(i + 1, len(narratives)):

                narrative_a = narratives[i]
                narrative_b = narratives[j]

                if (
                    narrative_a.get("source")
                    == narrative_b.get("source")
                ):
                    continue

                similarity = await self._calculate_narrative_similarity(
                    narrative_a.get("dna", {}),
                    narrative_b.get("dna", {})
                )

                if similarity > 0.85:
                    findings.append({
                        "type": "content_coordination",
                        "confidence": similarity,
                        "evidence": {
                            "similarity_score": similarity,
                            "content_a": narrative_a.get(
                                "content_id"
                            ),
                            "content_b": narrative_b.get(
                                "content_id"
                            ),
                            "source_a": narrative_a.get(
                                "source"
                            ),
                            "source_b": narrative_b.get(
                                "source"
                            ),
                            "signal_type": "cross_source_similarity"
                        }
                    })

        return findings

    async def _analyze_network_patterns(
        self,
        entity_nodes: List[Dict],
        narratives: List[Dict]
    ) -> List[Dict]:

        findings = []

        # Count repeated entity co-occurrences.
        entity_interactions = defaultdict(int)

        for narrative in narratives:

            entities = (
                narrative
                .get("dna", {})
                .get("entities", [])
            )

            # Normalize entities and filter metadata-only labels.
            clean_entities = []
            metadata_labels = {
                "date", "device date", "time", "timestamp",
                "source", "url", "title", "author", "unknown",
                "none", "null", "location", "event date",
                "publication date"
            }

            for entity in entities:
                if isinstance(entity, dict):
                    name = (
                        entity.get("name")
                        or entity.get("text")
                        or entity.get("value")
                    )
                else:
                    name = entity

                if not name:
                    continue

                name = " ".join(str(name).strip().split())
                normalized = name.casefold().strip(" .,:;")

                if not normalized or normalized in metadata_labels:
                    continue

                if not any(ch.isalpha() for ch in normalized):
                    continue

                clean_entities.append(name)

            # Case-insensitive deduplication, preserving original order.
            unique_entities = []
            seen_entities = set()

            for name in clean_entities:
                key = name.casefold()
                if key not in seen_entities:
                    seen_entities.add(key)
                    unique_entities.append(name)

            clean_entities = unique_entities

            for i in range(len(clean_entities)):

                for j in range(i + 1, len(clean_entities)):

                    # IMPORTANT:
                    # Sort strings, never dictionaries.
                    pair = tuple(
                        sorted(
                            (
                                clean_entities[i],
                                clean_entities[j]
                            ),
                            key=lambda value: value.lower()
                        )
                    )

                    entity_interactions[pair] += 1

        for pair, count in entity_interactions.items():

            # Co-occurrence is a signal to review, not proof of coordination.
            if count >= 3 and all(
                isinstance(value, str) and len(value.strip()) >= 3
                for value in pair
            ):

                findings.append({
                    "type": "network_coordination",
                    "confidence": min(
                        0.5 + (count * 0.1),
                        0.9
                    ),
                    "evidence": {
                        "entity_pair": pair,
                        "interaction_count": count,
                        "signal_type": "repeated_co_occurrence"
                    }
                })

        return findings

    async def _analyze_amplification_patterns(
        self,
        narratives: List[Dict],
        mutations: List[Dict]
    ) -> List[Dict]:

        findings = []

        mutation_types = defaultdict(list)

        for mutation in mutations:

            mutation_type = (
                mutation
                .get("narrative_dna", {})
                .get("mutation_type", "unknown")
            )

            mutation_types[mutation_type].append(mutation)

        for m_type, m_list in mutation_types.items():

            if len(m_list) >= 3:

                findings.append({
                    "type": "amplification_coordination",
                    "confidence": min(
                        0.6 + (len(m_list) * 0.05),
                        0.9
                    ),
                    "evidence": {
                        "mutation_type": m_type,
                        "mutation_count": len(m_list),
                        "mutation_ids": [
                            mutation.get("to_content")
                            for mutation in m_list
                        ],
                        "signal_type": "coordinated_amplification"
                    }
                })

        return findings

    async def _calculate_narrative_similarity(
        self,
        dna_a: Dict,
        dna_b: Dict
    ) -> float:

        if not dna_a or not dna_b:
            return 0.0

        claim_sim = await self._compare_texts(
            str(dna_a.get("core_claim", "") or ""),
            str(dna_b.get("core_claim", "") or "")
        )

        entities_a = self._normalise_entities(
            dna_a.get("entities", [])
        )

        entities_b = self._normalise_entities(
            dna_b.get("entities", [])
        )

        if entities_a and entities_b:

            entity_sim = (
                len(entities_a.intersection(entities_b))
                / len(entities_a.union(entities_b))
            )

        else:
            entity_sim = 0.0

        return float(
            (claim_sim * 0.6)
            + (entity_sim * 0.4)
        )

    @staticmethod
    def _normalise_entities(
        entities: Any
    ) -> set:

        if not isinstance(entities, (list, tuple, set)):
            return set()

        result = set()

        for entity in entities:

            if isinstance(entity, dict):

                name = (
                    entity.get("name")
                    or entity.get("text")
                    or entity.get("value")
                )

            else:
                name = entity

            if name:

                name = str(name).strip().lower()

                if name:
                    result.add(name)

        return result

    async def _compare_texts(
        self,
        text_a: str,
        text_b: str
    ) -> float:

        words_a = set(
            str(text_a).lower().split()
        )

        words_b = set(
            str(text_b).lower().split()
        )

        if not words_a or not words_b:
            return 0.0

        intersection = words_a.intersection(
            words_b
        )

        union = words_a.union(
            words_b
        )

        return (
            len(intersection) / len(union)
            if union
            else 0.0
        )


