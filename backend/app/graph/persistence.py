"""
Persistence helpers for graph runs and evidence snapshots.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from app.db.mongo import MongoDB
from app.graph.contracts import AgentResult, EvidenceRef, TripGraphState

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def agent_runs_collection():
    return MongoDB.get_collection("agent_runs")


def trip_evidence_collection():
    return MongoDB.get_collection("trip_evidence")


class GraphPersistence:
    """Best-effort persistence for graph traces."""

    async def persist_agent_result(
        self,
        state: TripGraphState,
        result: AgentResult,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        if MongoDB.db is None:
            return
        payload = {
            "trip_id": state.trip_id,
            "user_id": state.user_id,
            "request_id": state.request_id,
            "phase": state.phase,
            "agent_id": result.agent_id,
            "group": result.group,
            "status": result.status,
            "confidence": result.confidence,
            "assumptions": result.assumptions,
            "hard_constraints_checked": result.hard_constraints_checked,
            "state_delta": result.state_delta,
            "errors": result.errors,
            "metadata": {**result.metadata, **(extra or {})},
            "created_at": _utcnow(),
        }
        try:
            await agent_runs_collection().insert_one(payload)
        except Exception as exc:
            logger.warning("Failed to persist agent run for %s: %s", result.agent_id, exc)

    async def persist_evidence(
        self,
        state: TripGraphState,
        evidence_refs: Iterable[EvidenceRef],
    ) -> None:
        if MongoDB.db is None:
            return

        docs: List[Dict[str, Any]] = []
        for evidence in evidence_refs:
            docs.append({
                "trip_id": state.trip_id,
                "user_id": state.user_id,
                "request_id": state.request_id,
                "evidence_id": evidence.evidence_id,
                "source_type": evidence.source_type,
                "source_name": evidence.source_name,
                "summary": evidence.summary,
                "payload": evidence.payload,
                "confidence": evidence.confidence,
                "city": evidence.city,
                "created_at": evidence.created_at,
            })
        if not docs:
            return
        try:
            await trip_evidence_collection().insert_many(docs, ordered=False)
        except Exception as exc:
            logger.warning("Failed to persist graph evidence: %s", exc)

    async def persist_shadow_comparison(
        self,
        *,
        trip_id: str,
        user_id: str,
        request_id: str,
        comparison: Dict[str, Any],
    ) -> None:
        if MongoDB.db is None:
            return
        try:
            await agent_runs_collection().insert_one({
                "trip_id": trip_id,
                "user_id": user_id,
                "request_id": request_id,
                "phase": "shadow_compare",
                "agent_id": "legacy_comparison",
                "group": "executive",
                "status": "success",
                "confidence": comparison.get("confidence", 0.5),
                "metadata": comparison,
                "created_at": _utcnow(),
            })
        except Exception as exc:
            logger.warning("Failed to persist shadow comparison: %s", exc)
