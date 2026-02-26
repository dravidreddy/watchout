"""
Watchout — Trip State Machine

Provides deterministic phase control for multi-city travel planning.
The LLM never decides when to change phases — the code does.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Phase enum
# ---------------------------------------------------------------------------

class TripState(str, Enum):
    GREETING       = "greeting"     # Very first message, no context yet
    GATHERING      = "gathering"    # Collecting preferences (clarification loop)
    CONFIRMING     = "confirming"   # All prefs collected, showing confirmation card
    PLANNING       = "planning"     # Generating itinerary + parallel agents
    COMPLETE       = "complete"     # Itinerary generated and saved


# ---------------------------------------------------------------------------
# Data model for a single city leg
# ---------------------------------------------------------------------------

@dataclass
class CitySegment:
    city: str
    days: int
    vibe: List[str] = field(default_factory=list)
    arrives_from: Optional[str] = None       # Previous city or origin
    transport_preference: str = "flexible"   # flight | train | road | flexible
    budget_per_day: Optional[float] = None   # Filled by allocate_budget()
    _cache_key: Optional[str] = field(default=None, repr=False)

    def cache_key(self) -> str:
        """Stable hash of the segment inputs — used for incremental regen."""
        payload = {
            "city": self.city,
            "days": self.days,
            "vibe": sorted(self.vibe),
            "arrives_from": self.arrives_from,
            "transport_preference": self.transport_preference,
            "budget_per_day": self.budget_per_day,
        }
        return hashlib.md5(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("_cache_key", None)
        return d


# ---------------------------------------------------------------------------
# Core state machine
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = [
    "destinations",
    "duration_days",
    "num_travelers",
    "budget_range",
    "travel_vibe",
    "origin_city",
    "pace",
]

# Fields we can infer — never ask for these if inference is possible
INFERABLE_FIELDS = {"travel_vibe", "pace"}

# Mood pill → travel vibe mapping
MOOD_TO_VIBE: Dict[str, List[str]] = {
    "adventurous": ["adventure", "outdoors", "trekking"],
    "chill":       ["leisure", "relaxed", "beach"],
    "romantic":    ["romantic", "couples", "scenic"],
    "family":      ["family", "safe", "kid-friendly"],
    "workation":   ["workation", "quiet", "co-working"],
    "spiritual":   ["spiritual", "temples", "wellness"],
    "foodie":      ["foodie", "street food", "culinary"],
    "party":       ["nightlife", "party", "entertainment"],
}

STYLE_TO_PACE: Dict[str, str] = {
    "relaxing":   "relaxed",
    "adventure":  "fast-paced",
    "balanced":   "moderate",
    "cultural":   "moderate",
    "workation":  "moderate",
}


class TripStateMachine:
    """
    Owns and validates the trip state. Determines which phase the
    orchestrator should operate in and what information is still missing.

    All inference rules live here — not in prompts, not in agents.
    """

    def __init__(
        self,
        preferences: Dict[str, Any],
        state: TripState = TripState.GATHERING,
        cached_segment_keys: Optional[Dict[str, str]] = None,
    ):
        self.preferences = self._normalize_prefs(dict(preferences or {}))
        self.state = state
        self.cached_segment_keys: Dict[str, str] = cached_segment_keys or {}

    # ------------------------------------------------------------------
    # Preference normalization (inference rules)
    # ------------------------------------------------------------------

    def _normalize_prefs(self, prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Apply inference rules before computing missing fields."""

        # 1. Mood pill → travel_vibe
        mood = prefs.get("current_mood")
        if mood and not prefs.get("travel_vibe"):
            prefs["travel_vibe"] = MOOD_TO_VIBE.get(mood, [mood])

        # 2. Onboarding travel_vibe[] (list) → travel_vibe if still empty
        onboard_vibe = prefs.get("travel_vibe")
        if isinstance(onboard_vibe, list) and onboard_vibe:
            pass  # already set
        elif isinstance(onboard_vibe, str) and onboard_vibe:
            prefs["travel_vibe"] = [onboard_vibe]

        # 3. travel_style → pace if pace missing
        style = prefs.get("travel_style")
        if style and not prefs.get("pace"):
            prefs["pace"] = STYLE_TO_PACE.get(style, "moderate")

        # 4. Normalize destinations to list
        destinations = prefs.get("destinations")
        if isinstance(destinations, str):
            prefs["destinations"] = [destinations]

        return prefs

    # ------------------------------------------------------------------
    # Missing fields (computed, never stored)
    # ------------------------------------------------------------------

    @property
    def missing_fields(self) -> List[str]:
        """Fields genuinely unknown and cannot be inferred."""
        prefs = self.preferences
        missing = []
        for f in REQUIRED_FIELDS:
            val = prefs.get(f)
            if val is None or val == "" or val == []:
                missing.append(f)
        return missing

    @property
    def is_complete(self) -> bool:
        return len(self.missing_fields) == 0

    # ------------------------------------------------------------------
    # City segments
    # ------------------------------------------------------------------

    def build_segments(self) -> List[CitySegment]:
        """
        Convert flat preferences into per-city CitySegment objects.
        Called after GATHERING is complete.
        """
        destinations = self.preferences.get("destinations", [])
        total_days = self.preferences.get("duration_days", len(destinations) * 2)
        total_budget = self._parse_budget_total()
        vibe = self.preferences.get("travel_vibe", [])
        origin = self.preferences.get("origin_city", "")

        # If city_segments already specified (from clarification), use them directly
        raw_segments = self.preferences.get("city_segments")
        if raw_segments:
            segments = [CitySegment(**s) for s in raw_segments]
        else:
            # Distribute days evenly, last city gets remainder
            days_each = total_days // len(destinations) if destinations else total_days
            segments = []
            for i, city in enumerate(destinations):
                days = days_each if i < len(destinations) - 1 else total_days - days_each * i
                arrives_from = destinations[i - 1] if i > 0 else origin
                segments.append(CitySegment(
                    city=city,
                    days=max(1, days),
                    vibe=vibe,
                    arrives_from=arrives_from,
                    transport_preference=self.preferences.get("transport_preference", "flexible"),
                ))

        return self.allocate_budget(segments, total_budget)

    def allocate_budget(
        self,
        segments: List[CitySegment],
        total_budget_inr: Optional[float],
    ) -> List[CitySegment]:
        """Distribute total budget across city segments proportionally by days."""
        if not total_budget_inr:
            return segments
        total_days = sum(s.days for s in segments) or 1
        for seg in segments:
            seg.budget_per_day = round((seg.days / total_days) * total_budget_inr / seg.days, 0)
        return segments

    def segments_needing_regen(self, new_preferences: Dict[str, Any]) -> List[str]:
        """
        Given updated preferences, return city names whose CitySegment
        inputs have changed — these need to be re-planned.
        Unchanged cities reuse their cached result from MongoDB.
        """
        old_sm = TripStateMachine(self.preferences, self.state, self.cached_segment_keys)
        new_sm = TripStateMachine(new_preferences, self.state, self.cached_segment_keys)

        old_segs = {s.city: s.cache_key() for s in old_sm.build_segments()}
        new_segs = {s.city: s.cache_key() for s in new_sm.build_segments()}

        changed = []
        for city, key in new_segs.items():
            if old_segs.get(city) != key:
                changed.append(city)
        return changed

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def next_state(self) -> TripState:
        """Advance the state deterministically based on current data."""
        if self.state == TripState.GREETING:
            return TripState.GATHERING

        if self.state == TripState.GATHERING and self.is_complete:
            return TripState.CONFIRMING

        if self.state == TripState.CONFIRMING:
            return TripState.PLANNING

        if self.state == TripState.PLANNING:
            return TripState.COMPLETE

        return self.state

    def merge_preferences(self, new_prefs: Dict[str, Any]) -> "TripStateMachine":
        """Return a new state machine with merged preferences."""
        merged = {**self.preferences, **{k: v for k, v in new_prefs.items() if v}}
        return TripStateMachine(merged, self.state, self.cached_segment_keys)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _parse_budget_total(self) -> Optional[float]:
        """Convert budget_range string to an approximate total INR amount."""
        mapping = {
            "budget":   5000,
            "mid-range": 12000,
            "mid_range": 12000,
            "luxury":   30000,
        }
        budget_range = (self.preferences.get("budget_range") or "").lower()
        daily = mapping.get(budget_range)
        if daily is None:
            return None
        days = self.preferences.get("duration_days", 1) or 1
        travelers = self.preferences.get("num_travelers", 1) or 1
        return daily * days * travelers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "preferences": self.preferences,
            "missing_fields": self.missing_fields,
            "is_complete": self.is_complete,
            "cached_segment_keys": self.cached_segment_keys,
        }
