"""
Layered memory management for the graph runtime.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Tuple

from app.db.vector_store import VectorStore
from app.graph.contracts import TripGraphState
from app.services.preference_reducer import PreferenceReducer

logger = logging.getLogger(__name__)


def merge_precedence_dicts(*layers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge preference layers from lowest to highest precedence.
    Later dictionaries win.
    """
    merged: Dict[str, Any] = {}
    for layer in layers:
        if not layer:
            continue
        merged.update({k: v for k, v in layer.items() if v not in (None, "", [])})
    return merged


class GraphMemoryManager:
    """Resolves session, profile, and trip memory for graph execution."""

    def __init__(self):
        self.vector_store = VectorStore()
        self.reducer = PreferenceReducer()

    async def hydrate(self, state: TripGraphState) -> TripGraphState:
        """Populate layered memory fields and derive the active constraint view."""
        state.session_memory = {
            "latest_user_message": state.message,
            "recent_history": state.conversation_context[-10:],
        }
        state.profile_memory = {
            "profile_preferences": dict(state.profile_preferences),
            "semantic_memories": await self._search_memories(state.user_id, state.message),
        }
        state.trip_memory = {
            **state.trip_memory,
            "trip_id": state.trip_id,
            "existing_preferences": dict(state.preferences),
        }
        state.trip_constraints = self.resolve_constraints(state)
        return state

    def resolve_constraints(self, state: TripGraphState) -> Dict[str, Any]:
        """Apply the global precedence order for preference-like constraints."""
        return merge_precedence_dicts(
            state.inferred_preferences,
            state.profile_preferences,
            state.locked_logistics,
            state.confirmed_trip_constraints,
            state.latest_user_preferences,
        )

    def apply_preference_update(
        self,
        current: Dict[str, Any],
        updates: Dict[str, Any],
        user_message: str,
    ) -> Tuple[Dict[str, Any], str]:
        """Resolve preference updates using the shared conflict reducer."""
        cleaned_updates = {k: v for k, v in (updates or {}).items() if v not in (None, "", [])}
        if not cleaned_updates:
            return dict(current), "No preference changes detected"
        return self.reducer.update_preferences(current, cleaned_updates, user_message)

    async def _search_memories(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        if not query:
            return []
        try:
            return await self.vector_store.search_memories(user_id=user_id, query=query, limit=5)
        except Exception as exc:
            logger.warning("Graph memory search failed: %s", exc)
            return []

