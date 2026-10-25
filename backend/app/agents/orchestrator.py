import asyncio
from datetime import datetime
from typing import Dict, Any

from app.core.database import SessionLocal
from app.models.database import AnalysisJob, Project, ProjectStatus

from app.agents.graph_builder import GraphBuilderAgent
from app.agents.narrative_dna import NarrativeDNAAgent
from app.agents.mutation_detector import MutationDetectorAgent
from app.agents.coordination_analyzer import CoordinationAnalyzerAgent
from app.agents.claim_verifier import ClaimVerifierAgent
from app.agents.content_auditor import ContentAuditorAgent


async def run_analysis(job_id: int, project_id: int):

    db = SessionLocal()

    try:
        job = (
            db.query(AnalysisJob)
            .filter(AnalysisJob.id == job_id)
            .first()
        )

        if not job:
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()

        # =====================================================
        # STAGE 1 — BUILD GRAPH
        # =====================================================

        await update_job_progress(
            db,
            job,
            "building_graph",
            "Constructing temporal evidence graph..."
        )

        graph_builder = GraphBuilderAgent()

        graph_result = await graph_builder.build_graph(project_id)

        if not graph_result.get("success"):
            raise Exception(
                graph_result.get(
                    "error",
                    "Graph building failed"
                )
            )

        # =====================================================
        # STAGE 2 — NARRATIVE DNA
        # =====================================================

        await update_job_progress(
            db,
            job,
            "extracting_dna",
            "Analyzing narrative structures..."
        )

        dna_agent = NarrativeDNAAgent()

        narratives = await dna_agent.extract_narratives(
            project_id,
            graph_result.get("content_nodes", [])
        )

        if narratives is None:
            narratives = []

        # =====================================================
        # STAGE 3 — MUTATION DETECTION
        # =====================================================

        await update_job_progress(
            db,
            job,
            "detecting_mutations",
            "Tracking narrative evolution..."
        )

        mutation_agent = MutationDetectorAgent()

        mutations = await mutation_agent.detect_mutations(
            narratives
        )

        if mutations is None:
            mutations = []

        # =====================================================
        # STAGE 4 — COORDINATION
        # =====================================================

        await update_job_progress(
            db,
            job,
            "analyzing_coordination",
            "Identifying coordination patterns..."
        )

        coordination_agent = CoordinationAnalyzerAgent()

        coordination_findings = (
            await coordination_agent.analyze_coordination(
                project_id,
                graph_result.get("entity_nodes", []),
                narratives,
                mutations
            )
        )

        if coordination_findings is None:
            coordination_findings = []

        # =====================================================
        # STAGE 5 — CLAIM VERIFICATION
        # =====================================================

        await update_job_progress(
            db,
            job,
            "verifying_claims",
            "Verifying evidence and claims..."
        )

        verifier = ClaimVerifierAgent()

        verified_findings = await verifier.verify_findings(
            project_id,
            coordination_findings + mutations,
            graph_result
        )

        if verified_findings is None:
            verified_findings = []

        # =====================================================
        # ENRICH FINDINGS WITH NARRATIVE DNA
        # =====================================================
        # Coordination findings are generated from narratives, but the
        # original finding objects only carried their signal evidence.
        # Attach the relevant DNA so the Narratives UI can show the
        # actual extracted claim/entities/events instead of "Not available".
        verified_findings = _attach_narrative_dna(
            verified_findings,
            narratives
        )

        # =====================================================
        # STAGE 6 — CONTENT QUALITY REVIEW
        # =====================================================
        # Review the source itself for human-readable issues such as
        # conflicting measurements, dates, explanations and unsupported
        # statements. These are review signals, not proof of wrongdoing.
        content_auditor = ContentAuditorAgent()
        content_review_findings = content_auditor.audit(
            graph_result.get("content_nodes", [])
        )
        verified_findings.extend(content_review_findings)
        verified_findings = _deduplicate_findings(verified_findings)

        # =====================================================
        # FALLBACK 1 — NARRATIVE OBSERVATIONS
        # =====================================================

        if not verified_findings and narratives:

            fallback_findings = []

            for narrative in narratives[:10]:

                dna = narrative.get("dna", {})

                if dna is None:
                    dna = {}

                fallback_findings.append(
                    {
                        "type": "narrative_observation",

                        "confidence": 0.65,

                        "claim_status": "PARTIALLY_SUPPORTED",

                        "abstain_reason": (
                            "Narrative structure was extracted "
                            "from source content, but available "
                            "evidence is insufficient to establish "
                            "coordination or mutation."
                        ),

                        "narrative_dna": dna,

                        "evidence": {
                            "signal_type": "narrative_observation",

                            "content_id": narrative.get(
                                "content_id"
                            ),

                            "source": narrative.get(
                                "source",
                                "uploaded_document"
                            ),

                            "timestamp": str(
                                narrative.get("timestamp")
                            ),

                            "extraction_method": dna.get(
                                "extraction_method",
                                "unknown"
                            ),

                            "evidence_note": (
                                "Observation generated from "
                                "ingested source content. "
                                "No attribution or coordination "
                                "claim is made."
                            )
                        }
                    }
                )

            verified_findings = fallback_findings

        # =====================================================
        # FALLBACK 2 — SOURCE CONTENT
        # =====================================================

        if (
            not verified_findings
            and graph_result.get("content_nodes")
        ):

            first_content = graph_result["content_nodes"][0]

            verified_findings = [
                {
                    "type": "evidence_observation",

                    "confidence": 0.50,

                    "claim_status": "INSUFFICIENT",

                    "abstain_reason": (
                        "The system found source content but "
                        "could not establish a sufficiently "
                        "supported narrative coordination "
                        "or mutation finding."
                    ),

                    "narrative_dna": {},

                    "evidence": {
                        "signal_type": "source_content_present",

                        "content_id": first_content.get(
                            "id"
                        ),

                        "evidence_note": (
                            "Source content successfully "
                            "ingested and available for "
                            "investigation."
                        )
                    }
                }
            ]

        # =====================================================
        # STORE FINDINGS
        # =====================================================

        await store_findings(
            db,
            project_id,
            verified_findings
        )

        # =====================================================
        # COMPLETE JOB
        # =====================================================

        job.status = "completed"
        job.completed_at = datetime.utcnow()

        job.results = {
            "stages_completed": 6,

            "entities_found": len(
                graph_result.get("entity_nodes", [])
            ),

            "narratives_identified": len(
                narratives
            ),

            "mutations_detected": len(
                mutations
            ),

            "findings": len(
                verified_findings
            ),

            "abstentions": len(
                [
                    f
                    for f in verified_findings
                    if f.get("claim_status")
                    == "INSUFFICIENT"
                ]
            )
        }

        # =====================================================
        # PROJECT STATUS
        # =====================================================

        project = (
            db.query(Project)
            .filter(Project.id == project_id)
            .first()
        )

        if project:
            project.status = ProjectStatus.COMPLETED

        db.commit()

        print(
            f"NEXUS analysis completed | "
            f"Project={project_id} | "
            f"Narratives={len(narratives)} | "
            f"Mutations={len(mutations)} | "
            f"Findings={len(verified_findings)}"
        )

    except Exception as e:

        db.rollback()

        try:
            job.status = "error"
            job.error_message = str(e)
            db.commit()
        except Exception:
            db.rollback()

        print(
            f"NEXUS analysis failed: {e}"
        )

    finally:
        db.close()


def _deduplicate_findings(findings: list) -> list:
    """Collapse repeated signals so the UI shows distinct findings."""
    seen = set()
    unique = []
    for finding in findings or []:
        evidence = finding.get("evidence") or {}
        pair = evidence.get("entity_pair") or []
        if isinstance(pair, (list, tuple)):
            pair = tuple(sorted(str(x).strip().lower() for x in pair))
        else:
            pair = str(pair)
        key = (
            finding.get("type"),
            evidence.get("title") or evidence.get("signal_type"),
            pair,
            evidence.get("content_a"),
            evidence.get("content_b"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique


def _attach_narrative_dna(findings: list, narratives: list) -> list:
    """Attach the most relevant extracted Narrative DNA to each finding.

    Coordination findings reference content IDs for temporal/content signals,
    while network findings reference an entity pair. Mutation findings already
    contain mutation-specific DNA; those are preserved.
    """
    by_id = {n.get("content_id"): n for n in narratives if n.get("content_id") is not None}

    def candidates_for_finding(finding):
        evidence = finding.get("evidence") or {}
        ids = []
        for key in ("content_id", "content_a", "content_b"):
            value = evidence.get(key)
            if value is not None:
                ids.append(value)
        for value in evidence.get("content_ids") or []:
            ids.append(value)
        for value in evidence.get("mutation_ids") or []:
            if value in by_id:
                ids.append(value)
        return [by_id[i] for i in ids if i in by_id]

    enriched = []
    for finding in findings or []:
        item = dict(finding)
        existing = item.get("narrative_dna")
        if not isinstance(existing, dict):
            existing = {}

        if not existing or not existing.get("core_claim"):
            candidates = candidates_for_finding(item)

            # Network coordination has no content IDs, so locate narratives
            # containing both entities in the reported pair.
            if not candidates and item.get("type") == "network_coordination":
                pair = (item.get("evidence") or {}).get("entity_pair") or []
                wanted = {str(x).strip().lower() for x in pair}
                if wanted:
                    candidates = [
                        n for n in narratives
                        if wanted.issubset({
                            str(x.get("name") if isinstance(x, dict) else x).strip().lower()
                            for x in (n.get("dna") or {}).get("entities", [])
                        })
                    ]

            if not candidates:
                candidates = narratives[:1]

            if candidates:
                dna = dict((candidates[0].get("dna") or {}))
                if len(candidates) > 1:
                    # Preserve the first claim while merging unique entities,
                    # events, locations and supporting claims from related content.
                    for field in ("entities", "events", "locations", "time_references", "key_phrases", "supporting_claims"):
                        merged = list(dna.get(field) or [])
                        for candidate in candidates[1:4]:
                            for value in (candidate.get("dna") or {}).get(field, []) or []:
                                if value not in merged:
                                    merged.append(value)
                        dna[field] = merged[:20]
                item["narrative_dna"] = dna

        enriched.append(item)

    return enriched


# =============================================================
# JOB PROGRESS
# =============================================================

async def update_job_progress(
    db,
    job,
    stage: str,
    message: str
):

    job.results = job.results or {}

    job.results["current_stage"] = stage
    job.results["message"] = message

    db.commit()


# =============================================================
# STORE FINDINGS
# =============================================================

async def store_findings(
    db,
    project_id: int,
    findings: list
):

    from app.models.database import NarrativeFinding

    # Keep the project result set clean when analysis is re-run.
    db.query(NarrativeFinding).filter(
        NarrativeFinding.project_id == project_id
    ).delete(synchronize_session=False)

    for finding in findings:

        db_finding = NarrativeFinding(
            project_id=project_id,

            finding_type=finding.get(
                "type",
                "unknown"
            ),

            confidence_score=finding.get(
                "confidence",
                0.0
            ),

            claim_status=finding.get(
                "claim_status",
                "INSUFFICIENT"
            ),

            abstain_reason=finding.get(
                "abstain_reason"
            ),

            narrative_dna=finding.get(
                "narrative_dna",
                {}
            ),

            evidence=finding.get(
                "evidence",
                {}
            ),

            created_at=datetime.utcnow()
        )

        db.add(db_finding)

    db.commit()