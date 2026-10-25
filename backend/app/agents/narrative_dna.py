from typing import Dict, Any, List, Optional
import re
import json

try:
    from openai import AsyncOpenAI
except Exception:
    AsyncOpenAI = None

from app.config import settings


class NarrativeDNAAgent:
    """
    NEXUS Narrative DNA extraction.

    Primary:
        OpenAI structured extraction.

    Fallback:
        Deterministic local extraction.

    IMPORTANT:
        The local fallback guarantees that narratives can still
        be generated when the OpenAI API/model is unavailable.
    """

    def __init__(self):
        self.client = None

        if settings.OPENAI_API_KEY and AsyncOpenAI is not None:
            try:
                self.client = AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY
                )
            except Exception as e:
                print(
                    f"OpenAI client initialization failed: {e}"
                )

    # =========================================================
    # MAIN ENTRY POINT
    # =========================================================

    async def extract_narratives(
        self,
        project_id: int,
        content_nodes: List[Dict]
    ) -> List[Dict]:

        narratives = []

        print(
            f"Narrative extraction started | "
            f"Project={project_id} | "
            f"Content nodes={len(content_nodes)}"
        )

        for index, content in enumerate(content_nodes):

            try:

                dna = await self._extract_narrative_dna(
                    content
                )

                # -------------------------------------------------
                # GUARANTEED LOCAL FALLBACK
                # -------------------------------------------------

                if not dna:

                    print(
                        f"Using local narrative fallback "
                        f"for content {content.get('id')}"
                    )

                    dna = self._local_extract_dna(
                        content
                    )

                if dna:

                    narratives.append(
                        {
                            "content_id": content.get(
                                "id",
                                index
                            ),

                            "dna": dna,

                            "timestamp": content.get(
                                "timestamp"
                            ),

                            "source": content.get(
                                "source",
                                "uploaded_document"
                            )
                        }
                    )

            except Exception as e:

                print(
                    f"Narrative extraction failed for "
                    f"content {content.get('id')}: {e}"
                )

                # -------------------------------------------------
                # ABSOLUTE FALLBACK
                # -------------------------------------------------

                try:

                    dna = self._local_extract_dna(
                        content
                    )

                    if dna:

                        narratives.append(
                            {
                                "content_id": content.get(
                                    "id",
                                    index
                                ),

                                "dna": dna,

                                "timestamp": content.get(
                                    "timestamp"
                                ),

                                "source": content.get(
                                    "source",
                                    "uploaded_document"
                                )
                            }
                        )

                except Exception as fallback_error:

                    print(
                        f"Local fallback failed: "
                        f"{fallback_error}"
                    )

        print(
            f"Narrative DNA extraction completed | "
            f"Narratives={len(narratives)}"
        )

        return narratives

    # =========================================================
    # AI EXTRACTION
    # =========================================================

    async def _extract_narrative_dna(
        self,
        content: Dict
    ) -> Dict[str, Any]:

        text = self._get_content_text(content)

        if not text:

            return None

        if len(text.strip()) < 30:

            return self._local_extract_dna(
                content
            )

        # ---------------------------------------------------------
        # If OpenAI is unavailable, immediately use local method.
        # ---------------------------------------------------------

        if not self.client:

            return self._local_extract_dna(
                content
            )

        prompt = f"""
Analyze the following source text and extract its Narrative DNA.

Return ONLY valid JSON.

Required structure:

{{
    "core_claim": "central assertion or main point",

    "entities": [],

    "events": [],

    "locations": [],

    "time_references": [],

    "emotional_framing": "neutral",

    "key_phrases": [],

    "supporting_claims": [],

    "contradicting_claims": []
}}

Do not invent facts.

Text:

{text[:5000]}
"""

        try:

            response = await self.client.chat.completions.create(

                model=settings.OPENAI_MODEL,

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert in "
                            "forensic narrative analysis. "
                            "Extract structured evidence "
                            "from the supplied text without "
                            "inventing facts."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                response_format={
                    "type": "json_object"
                }
            )

            message = response.choices[0].message

            dna_text = message.content

            if not dna_text:

                raise ValueError(
                    "Empty OpenAI response"
                )

            dna = json.loads(
                dna_text
            )

            dna = self._normalize_dna(
                dna,
                text
            )

            dna["extraction_method"] = "llm"

            # -----------------------------------------------------
            # Do NOT depend on OpenAI embeddings.
            # -----------------------------------------------------

            dna["semantic_embedding"] = []

            dna["propagation_pattern"] = "unknown"

            return dna

        except Exception as e:

            print(
                f"OpenAI narrative extraction failed: "
                f"{e}"
            )

            # -----------------------------------------------------
            # CRITICAL:
            # Never return None just because OpenAI failed.
            # -----------------------------------------------------

            return self._local_extract_dna(
                content
            )

    # =========================================================
    # CONTENT TEXT EXTRACTION
    # =========================================================

    def _get_content_text(
        self,
        content: Dict
    ) -> str:

        possible_fields = [

            "text",

            "content",

            "extracted_text",

            "raw_text",

            "body",

            "description"

        ]

        for field in possible_fields:

            value = content.get(field)

            if value and isinstance(value, str):

                if value.strip():

                    return value.strip()

        # -----------------------------------------------------
        # Some NEXUS records may store extracted data inside
        # metadata.
        # -----------------------------------------------------

        metadata = content.get(
            "metadata"
        )

        if isinstance(metadata, dict):

            for field in possible_fields:

                value = metadata.get(field)

                if value and isinstance(
                    value,
                    str
                ):

                    if value.strip():

                        return value.strip()

        return ""

    # =========================================================
    # LOCAL FALLBACK
    # =========================================================

    def _local_extract_dna(
        self,
        content: Dict
    ) -> Dict[str, Any]:

        text = self._get_content_text(content)

        if not text:
            return None

        clean_text = re.sub(r"\s+", " ", text).strip()

        if not clean_text:
            return None

        sentences = re.split(r"(?<=[.!?])\s+", clean_text)
        sentences = [
            sentence.strip()
            for sentence in sentences
            if len(sentence.strip()) > 20
        ]

        # Keep the overview human-readable: prefer a substantive sentence
        # instead of a document heading or metadata line.
        preferred = [
            sentence for sentence in sentences
            if any(token in sentence.lower() for token in (
                "program", "programme", "platform", "project",
                "designed", "developed", "consolidat", "initiative",
                "purpose", "aim", "objective", "migration",
                "implementation", "transformation"
            ))
        ]
        core_claim = (preferred[0] if preferred else (sentences[0] if sentences else clean_text))[:500]

        entities = self._extract_structured_entities(clean_text)
        events = self._extract_events(sentences)
        locations = [
            item["name"] for item in entities
            if item["type"] == "Location"
        ]

        # The UI can display richer entity groups, while retaining the
        # original simple string format for events/locations.
        entity_names = entities

        time_patterns = [
            r"\b\d{4}\b",
            r"\b\d{1,2}:\d{2}\b",
            r"\b(?:today|yesterday|tomorrow)\b",
            r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b"
        ]

        time_references = []
        for pattern in time_patterns:
            for match in re.findall(pattern, clean_text, flags=re.IGNORECASE):
                value = str(match)
                if value not in time_references:
                    time_references.append(value)

        lower_text = clean_text.lower()

        urgent_words = {
            "danger", "dangerous", "warning", "threat", "risk",
            "fear", "attack", "crisis", "urgent", "alarming", "disaster"
        }
        positive_words = {
            "success", "successful", "safe", "benefit", "improved",
            "positive", "progress", "growth"
        }
        negative_words = {
            "failure", "failed", "problem", "damage", "negative",
            "wrong", "loss", "decline", "conflict", "inconsistent"
        }

        if any(word in lower_text for word in urgent_words):
            emotional_framing = "urgent"
        elif any(word in lower_text for word in positive_words):
            emotional_framing = "optimistic"
        elif any(word in lower_text for word in negative_words):
            emotional_framing = "concerned"
        else:
            emotional_framing = "neutral"

        words = re.findall(r"\b[a-zA-Z]{5,}\b", lower_text)
        stop_words = {
            "about", "after", "again", "because", "before", "being",
            "could", "first", "from", "have", "their", "there",
            "these", "those", "which", "would", "where", "while",
            "other", "should", "through", "between", "program",
            "project", "operations", "service", "transformation"
        }
        frequency = {}
        for word in words:
            if word in stop_words:
                continue
            frequency[word] = frequency.get(word, 0) + 1

        key_phrases = [
            word for word, count in sorted(
                frequency.items(),
                key=lambda item: item[1],
                reverse=True
            )
            if count >= 2
        ][:10]

        supporting_claims = [
            sentence[:500] for sentence in sentences[1:4]
        ]

        dna = {
            "core_claim": core_claim,
            "entities": entity_names,
            "events": events,
            "locations": locations[:12],
            "time_references": time_references[:20],
            "emotional_framing": emotional_framing,
            "key_phrases": key_phrases,
            "supporting_claims": supporting_claims,
            "contradicting_claims": [],
            "semantic_embedding": [],
            "propagation_pattern": "unknown",
            "extraction_method": "local_fallback"
        }

        return self._normalize_dna(dna, clean_text)

    # =========================================================
    # HUMAN-READABLE ENTITY EXTRACTION
    # =========================================================

    _GENERIC_ENTITY_WORDS = {
        "the", "this", "that", "these", "those", "when", "where",
        "what", "which", "however", "therefore", "according",
        "source", "program", "programme", "records", "record",
        "technical", "notes", "note", "operational", "observations",
        "observation", "performance", "materials", "material",
        "purpose", "synthetic", "integrated", "analysis", "demo",
        "all", "summary", "appendix", "section", "overview",
        "implementation", "team", "report", "reports", "reported",
        "document", "content", "project", "digital", "operations",
        "service", "transformation", "phase", "status", "details",
        "information", "findings", "evidence", "review"
    }

    _LOCATION_SUFFIXES = (
        "hub", "campus", "facility", "center", "centre", "room",
        "annex", "site", "office", "depot", "station", "headquarters"
    )

    _SYSTEM_SUFFIXES = (
        "core", "flow", "registry", "monitor", "link", "mesh",
        "portal", "platform", "engine", "system", "gateway", "service"
    )

    _ORG_SUFFIXES = (
        "systems", "infrastructure", "metrics", "networks", "analytics",
        "directorate", "technology", "technologies", "solutions",
        "services", "group", "labs", "laboratories", "corporation",
        "company", "inc", "ltd"
    )

    def _normalise_entity_name(self, value: Any) -> str:
        value = str(value or "")
        value = re.sub(r"\s+", " ", value).strip(" \t\r\n,.;:()[]{}")
        return value

    def _is_generic_entity(self, name: str) -> bool:
        words = re.findall(r"[A-Za-z]+", name.lower())
        if not words:
            return True
        if len(name) < 3 or len(name) > 90:
            return True
        # Reject phrases made entirely from document vocabulary.
        if all(word in self._GENERIC_ENTITY_WORDS for word in words):
            return True
        # Reject very long heading-like phrases.
        if len(words) >= 5 and sum(w in self._GENERIC_ENTITY_WORDS for w in words) >= len(words) - 1:
            return True
        return False

    def _classify_entity(self, name: str, context: str = "") -> Optional[str]:
        lower = name.lower().strip()
        last = lower.split()[-1] if lower.split() else ""

        if last in self._LOCATION_SUFFIXES:
            return "Location"

        if last in self._SYSTEM_SUFFIXES:
            return "System"

        # CamelCase product or system names are a useful low-risk signal.
        if re.fullmatch(r"[A-Z][a-z]+[A-Z][A-Za-z0-9.-]*", name):
            return "System"

        if last in self._ORG_SUFFIXES:
            return "Organization"

        # Common place wording that does not end with a suffix.
        if re.search(r"\b(?:at|in|from|located at|based at)\s+" + re.escape(name.lower()), context.lower()):
            if len(name.split()) >= 2:
                return "Location"

        # Person names: two or three conventional name tokens.
        if re.fullmatch(
            r"[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){1,2}",
            name
        ):
            if not self._is_generic_entity(name):
                return "Person"

        return None

    def _extract_structured_entities(self, text: str) -> List[Dict[str, str]]:
        candidates = []

        # Explicit multi-word proper nouns.
        patterns = [
            r"\b[A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*){1,4}\b",
            r"\b[A-Z][A-Za-z0-9&.-]*(?:\s+(?:Core|Flow|Registry|Monitor|Link|Mesh|Hub|Campus|Facility|Center|Centre|Room|Annex|Site))\b"
        ]

        for pattern in patterns:
            candidates.extend(re.findall(pattern, text))

        # Acronym + name forms are useful for technical systems.
        candidates.extend(re.findall(
            r"\b[A-Z]{2,}[A-Za-z0-9.-]*(?:\s+[A-Z][A-Za-z0-9.-]*){1,3}\b",
            text
        ))

        # Product/system names written as CamelCase (e.g. AsterGlow) are
        # common in incident reports and were previously missed when they
        # appeared as a single token. Keep this conservative to avoid treating
        # ordinary sentence-initial words as entities.
        candidates.extend(re.findall(r"\b[A-Z][a-z]+[A-Z][A-Za-z0-9.-]*\b", text))

        seen = set()
        entities = []

        for raw in candidates:
            name = self._normalise_entity_name(raw)
            if not name or name.lower() in seen:
                continue
            if self._is_generic_entity(name):
                continue

            entity_type = self._classify_entity(name, text)
            if not entity_type:
                continue

            # Avoid accidental sentence fragments and title-like phrases.
            words = name.split()
            if len(words) > 4 and entity_type not in {"Location", "Organization"}:
                continue

            key = name.lower()
            seen.add(key)
            entities.append({
                "type": entity_type,
                "name": name
            })

        # A small, reliable pattern for names introduced in prose.
        person_candidates = re.findall(
            r"\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?)\b",
            text
        )
        for raw in person_candidates:
            name = self._normalise_entity_name(raw)
            if self._is_generic_entity(name):
                continue
            if re.search(r"\b(?:Systems|Infrastructure|Metrics|Networks|Analytics|Directorate|Core|Flow|Registry|Monitor|Link|Mesh|Hub|Campus|Facility|Center|Centre|Room|Annex|Site)\b$", name):
                continue
            key = name.lower()
            if key in seen:
                continue
            entities.append({"type": "Person", "name": name})
            seen.add(key)

        # Keep the graph useful rather than flooding it with every capitalized phrase.
        order = {"Person": 0, "Organization": 1, "Location": 2, "System": 3}
        entities.sort(key=lambda e: (order.get(e["type"], 9), e["name"].lower()))
        return entities[:40]

    def _extract_events(self, sentences: List[str]) -> List[str]:
        event_words = {
            "announced", "reported", "launched", "started", "stopped",
            "occurred", "happened", "confirmed", "denied", "released",
            "published", "shared", "posted", "claimed", "revealed",
            "warned", "detected", "discovered", "introduced", "approved",
            "rejected", "signed", "issued", "created", "deployed",
            "migrated", "implemented", "changed", "reduced", "increased",
            "peaked", "recorded", "failed", "resolved"
        }

        events = []
        seen = set()
        for sentence in sentences:
            lower = sentence.lower()
            if any(word in lower for word in event_words):
                value = sentence[:500]
                key = value.lower()
                if key not in seen:
                    events.append(value)
                    seen.add(key)

        return events[:10]

    # =========================================================
    # NORMALIZATION
    # =========================================================

    def _normalize_dna(
        self,
        dna: Dict[str, Any],
        text: str
    ) -> Dict[str, Any]:

        if not isinstance(
            dna,
            dict
        ):

            dna = {}

        dna.setdefault(
            "core_claim",
            text[:600]
        )

        dna.setdefault(
            "entities",
            []
        )

        dna.setdefault(
            "events",
            []
        )

        dna.setdefault(
            "locations",
            []
        )

        dna.setdefault(
            "time_references",
            []
        )

        dna.setdefault(
            "emotional_framing",
            "neutral"
        )

        dna.setdefault(
            "key_phrases",
            []
        )

        dna.setdefault(
            "supporting_claims",
            []
        )

        dna.setdefault(
            "contradicting_claims",
            []
        )

        dna.setdefault(
            "semantic_embedding",
            []
        )

        dna.setdefault(
            "propagation_pattern",
            "unknown"
        )

        raw_entities = dna.get("entities") or []
        normalized_entities = []
        seen_entity_names = set()

        for item in raw_entities:
            if isinstance(item, dict):
                raw_name = item.get("name") or item.get("label") or ""
                raw_type = item.get("type") or ""
            else:
                raw_name = item
                raw_type = ""

            name = self._normalise_entity_name(raw_name)
            if not name or self._is_generic_entity(name):
                continue

            entity_type = raw_type.title() if raw_type else self._classify_entity(name, text)
            if entity_type not in {"Person", "Organization", "Location", "System"}:
                entity_type = self._classify_entity(name, text)

            if not entity_type:
                continue

            key = (entity_type, name.lower())
            if key in seen_entity_names:
                continue

            seen_entity_names.add(key)
            normalized_entities.append({
                "type": entity_type,
                "name": name
            })

        dna["entities"] = normalized_entities[:40]

        location_names = [
            e["name"] for e in normalized_entities
            if e["type"] == "Location"
        ]

        for value in dna.get("locations") or []:
            value = self._normalise_entity_name(
                value.get("name") if isinstance(value, dict) else value
            )
            if (
                value
                and not self._is_generic_entity(value)
                and value not in location_names
                and self._classify_entity(value, text) == "Location"
            ):
                location_names.append(value)

        dna["locations"] = location_names[:20]

        normalized_events = []
        seen_events = set()
        for event in dna.get("events") or []:
            value = self._normalise_entity_name(
                event.get("description") if isinstance(event, dict) else event
            )
            if len(value) < 20:
                continue
            key = value.lower()
            if key not in seen_events:
                normalized_events.append(value[:500])
                seen_events.add(key)

        dna["events"] = normalized_events[:12]

        return dna