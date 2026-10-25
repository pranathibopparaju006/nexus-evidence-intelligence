from datetime import datetime
from typing import List, Dict, Any
import re

from neo4j import GraphDatabase
from app.config import settings
from app.core.database import SessionLocal
from app.models.database import DataSource
from app.agents.narrative_dna import NarrativeDNAAgent


class GraphBuilderAgent:

    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    async def build_graph(self, project_id: int) -> Dict[str, Any]:
        try:
            # Rebuild this project's graph from its currently ingested sources.
            # Without cleanup, removed/older sources remain visible as stale nodes.
            with self.driver.session() as session:
                session.run(
                    "MATCH (n {project_id: $project_id}) DETACH DELETE n",
                    {"project_id": project_id}
                )

            content_nodes = await self._get_content_nodes(project_id)

            entity_nodes = []

            for content in content_nodes:
                entities = await self._extract_entities(content)

                for entity in entities:
                    entity_id = await self._create_entity_node(
                        project_id,
                        entity
                    )

                    entity_nodes.append({
                        "id": entity_id,
                        "type": entity["type"],
                        "name": entity["name"]
                    })

                    await self._create_relationship(
                        content["id"],
                        entity_id,
                        "MENTIONS"
                    )

            await self._create_temporal_relationships(
                project_id,
                content_nodes
            )

            await self._create_similarity_relationships(
                project_id,
                content_nodes
            )

            return {
                "success": True,
                "content_nodes": content_nodes,
                "entity_nodes": entity_nodes,
                "total_nodes": len(content_nodes) + len(entity_nodes)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _get_content_nodes(
        self,
        project_id: int
    ) -> List[Dict]:

        db = SessionLocal()

        try:
            sources = (
                db.query(DataSource)
                .filter(
                    DataSource.project_id == project_id,
                    DataSource.ingestion_status == "completed"
                )
                .all()
            )

            content_nodes = []

            for source in sources:

                metadata = source.extracted_metadata or {}
                content = metadata.get("content", {})

                items = (
                    content
                    if isinstance(content, list)
                    else [content]
                )

                for index, item in enumerate(items):

                    if not isinstance(item, dict):
                        item = {
                            "text": str(item)
                        }

                    text = item.get("text", "")
                    # Some parsers/JSON uploads may nest extracted text as an object.
                    if isinstance(text, dict):
                        text = text.get("text") or text.get("content") or text.get("value") or ""
                    if isinstance(text, (list, tuple)):
                        text = "\n".join(str(part) for part in text if part is not None)
                    if not isinstance(text, str):
                        text = str(text) if text is not None else ""
                    text = text.strip()

                    if not text:
                        continue

                    node_id = f"content_{source.id}_{index}"

                    timestamp = (
                        item.get("timestamp")
                        or item.get("created_at")
                        or metadata.get("processed_at")
                    )

                    node = {
                        "id": node_id,
                        "type": "Content",
                        "text": text,
                        "timestamp": timestamp,
                        "source_id": source.id,
                        "filename": source.filename,
                        "source": source.filename,
                    }

                    content_nodes.append(node)

                    with self.driver.session() as session:
                        session.run(
                            """
                            MERGE (c:Content {id: $id})
                            SET c.type = 'Content',
                                c.project_id = $project_id,
                                c.text = $text,
                                c.timestamp = CASE
                                    WHEN $timestamp IS NOT NULL
                                    THEN datetime($timestamp)
                                    ELSE NULL
                                END,
                                c.source_id = $source_id,
                                c.filename = $filename
                            """,
                            {
                                "id": node_id,
                                "project_id": project_id,
                                "text": text,
                                "timestamp": timestamp,
                                "source_id": source.id,
                                "filename": source.filename
                            }
                        )

            return content_nodes

        finally:
            db.close()

    async def _extract_entities(
        self,
        content: Dict
    ) -> List[Dict]:

        # Use the same human-readable extraction rules as Narrative DNA.
        # This keeps the Neo4j graph and the Overview page consistent.
        text = content.get("text", "")
        if not text:
            return []

        agent = NarrativeDNAAgent()
        structured = agent._extract_structured_entities(text)

        return [
            {
                "type": entity["type"],
                "name": entity["name"],
                "context": text[:300]
            }
            for entity in structured
        ]

    async def _create_entity_node(
        self,
        project_id: int,
        entity: Dict
    ) -> str:

        entity_id = (
            f"entity_{project_id}_{hash(entity['name'])}"
        )

        with self.driver.session() as session:

            session.run(
                """
                MERGE (e:Entity {id: $id})
                SET e.name = $name,
                    e.type = $type,
                    e.context = $context,
                    e.project_id = $project_id,
                    e.created_at = datetime()
                """,
                {
                    "id": entity_id,
                    "name": entity["name"],
                    "type": entity["type"],
                    "context": entity["context"],
                    "project_id": project_id
                }
            )

        return entity_id

    async def _create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str
    ):

        with self.driver.session() as session:

            session.run(
                f"""
                MATCH (a {{id: $from_id}})
                MATCH (b {{id: $to_id}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r.created_at = datetime()
                """,
                {
                    "from_id": from_id,
                    "to_id": to_id
                }
            )

    async def _create_temporal_relationships(
        self,
        project_id: int,
        content_nodes: List[Dict]
    ):

        sorted_content = sorted(
            content_nodes,
            key=lambda x: x.get("timestamp", "")
        )

        for i in range(
            len(sorted_content) - 1
        ):

            await self._create_relationship(
                sorted_content[i]["id"],
                sorted_content[i + 1]["id"],
                "POSTED_BEFORE"
            )

    async def _create_similarity_relationships(
        self,
        project_id: int,
        content_nodes: List[Dict]
    ):

        for i, content1 in enumerate(content_nodes):

            for j, content2 in enumerate(
                content_nodes[i + 1:],
                i + 1
            ):

                similarity = await self._calculate_similarity(
                    content1,
                    content2
                )

                if similarity > 0.85:

                    await self._create_relationship(
                        content1["id"],
                        content2["id"],
                        "SIMILAR_TO"
                    )

    async def _calculate_similarity(
        self,
        content1: Dict,
        content2: Dict
    ) -> float:

        text1 = content1.get("text", "")
        text2 = content2.get("text", "")
        if isinstance(text1, dict):
            text1 = text1.get("text") or text1.get("content") or text1.get("value") or ""
        if isinstance(text2, dict):
            text2 = text2.get("text") or text2.get("content") or text2.get("value") or ""
        text1 = str(text1 or "")
        text2 = str(text2 or "")

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)