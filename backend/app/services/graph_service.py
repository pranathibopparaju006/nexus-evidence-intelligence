from typing import List, Dict, Any, Optional
from datetime import datetime, date

from neo4j import GraphDatabase
from app.config import settings
from app.models.schemas import GraphNode, GraphEdge, TimelineEvent


def _native_datetime(value):
    if value is None:
        return None
    try:
        value = value.to_native()
    except (AttributeError, TypeError):
        pass
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None


def _timeline_source_date(text, fallback):
    # Prefer an explicitly labelled source date; otherwise use a clear ISO date.
    patterns = [
        r"(?im)^\s*(?:source\s+)?date\s*:\s*(\d{4}-\d{2}-\d{2})\b",
        r"\b(\d{4}-\d{2}-\d{2})\b",
    ]
    import re
    for pattern in patterns:
        match = re.search(pattern, text or "")
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d")
            except ValueError:
                continue
    return fallback


def _is_timeline_noise(text):
    import re
    cleaned = (text or "").strip()
    lower = cleaned.lower()
    markers = (
        "localhost", "powershell", "windows\\system32", "docker compose",
        "webpack compiled", "ask gemini", "npm start", "select-string",
        "invoke-webrequest", "ps c:\\", "http://", "https://",
        "warn[0000]", "container nexus-", "compiled successfully",
    )
    if len(cleaned) < 30:
        return True
    if any(marker in lower for marker in markers):
        return True
    if re.search(r"(?im)^\s*(?:PS [A-Z]:\\|>>|INFO:\s|WARN\[)", cleaned):
        return True
    return False


class GraphService:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    async def get_project_graph(
        self,
        project_id: int,
        node_type: Optional[str] = None,
        time_start: Optional[str] = None,
        time_end: Optional[str] = None
    ) -> Dict[str, List[Any]]:
        where_clauses = ["n.project_id = $project_id"]
        params = {"project_id": project_id}

        if node_type:
            where_clauses.append("n.type = $node_type")
            params["node_type"] = node_type

        if time_start and time_end:
            where_clauses.append(
                "n.timestamp >= datetime($time_start) "
                "AND n.timestamp <= datetime($time_end)"
            )
            params["time_start"] = time_start
            params["time_end"] = time_end

        where_str = " AND ".join(where_clauses)
        query = f"""
            MATCH (n)
            WHERE {where_str}
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 1000
        """

        nodes = {}
        edges = []
        with self.driver.session() as session:
            result = session.run(query, params)
            for record in result:
                n = record["n"]
                node_id = n["id"]
                if node_id not in nodes:
                    nodes[node_id] = GraphNode(
                        id=node_id,
                        type=n.get("type", "Unknown"),
                        label=str(n.get("name", n.get("text", "Unknown")))[:50],
                        properties={k: str(v) if v is not None else None for k, v in dict(n).items()}
                    )

                m = record["m"]
                if m is not None:
                    other_id = m["id"]
                    if other_id not in nodes:
                        nodes[other_id] = GraphNode(
                            id=other_id,
                            type=m.get("type", "Unknown"),
                            label=str(m.get("name", m.get("text", "Unknown")))[:50],
                            properties={k: str(v) if v is not None else None for k, v in dict(m).items()}
                        )
                    r = record["r"]
                    if r is not None:
                        edges.append(GraphEdge(
                            id=f"{n['id']}-{r.type}-{m['id']}",
                            source=n["id"],
                            target=m["id"],
                            type=r.type,
                            properties={k: str(v) if v is not None else None for k, v in dict(r).items()}
                        ))
        return {"nodes": list(nodes.values()), "edges": edges}

    async def get_timeline_events(self, project_id: int) -> List[TimelineEvent]:
        query = """
            MATCH (n:Content)
            WHERE n.project_id = $project_id
              AND n.timestamp IS NOT NULL
            RETURN n
            ORDER BY n.timestamp
        """
        events = []
        with self.driver.session() as session:
            result = session.run(query, {"project_id": project_id})
            for record in result:
                node = record["n"]
                description = str(node.get("text", "")).strip()
                if _is_timeline_noise(description):
                    continue

                ingestion_timestamp = _native_datetime(node.get("timestamp"))
                timestamp = _timeline_source_date(description, ingestion_timestamp)
                if timestamp is None:
                    continue

                events.append(TimelineEvent(
                    timestamp=timestamp,
                    event_type="content_posted",
                    description=description[:300],
                    node_ids=[str(node.get("id", "unknown"))],
                    significance=float(node.get("significance", 0.5) or 0.5)
                ))
        unique_events = []
        seen = set()

        for event in events:
            key = (
                str(event.timestamp),
                " ".join(event.description.lower().split())
            )
            if key in seen:
                continue
            seen.add(key)
            unique_events.append(event)

        return sorted(unique_events, key=lambda event: event.timestamp)


_graph_service = None


async def get_project_graph(*args, **kwargs):
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return await _graph_service.get_project_graph(*args, **kwargs)


async def get_timeline_events(*args, **kwargs):
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return await _graph_service.get_timeline_events(*args, **kwargs)

