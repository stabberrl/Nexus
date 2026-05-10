"""Core models and data structures for the game engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GamePhase(Enum):
    WORLD_CREATION = "world_creation"
    CHARACTER_CREATION = "character_creation"
    PLAYING = "playing"
    PAUSED = "paused"


class LocationType(Enum):
    TOWN = "town"
    DUNGEON = "dungeon"
    FOREST = "forest"
    DESERT = "desert"
    MOUNTAIN = "mountain"
    COAST = "coast"
    RUINS = "ruins"
    TEMPLE = "temple"
    CAVE = "cave"
    VILLAGE = "village"
    CASTLE = "castle"
    WILDERNESS = "wilderness"
    CUSTOM = "custom"


@dataclass
class Character:
    name: str
    description: str
    personality: str
    backstory: str = ""
    goals: list[str] = field(default_factory=list)
    inventory: list[str] = field(default_factory=list)
    relationships: dict[str, int] = field(default_factory=dict)


@dataclass
class Npc:
    id: str
    name: str
    description: str
    personality: str
    role: str
    location_id: str
    backstory: str = ""
    secret: str = ""
    memory: list[dict] = field(default_factory=list)
    relationship: int = 0


@dataclass
class Location:
    id: str
    name: str
    description: str
    type: LocationType = LocationType.CUSTOM
    npcs: list[str] = field(default_factory=list)
    exits: dict[str, str] = field(default_factory=dict)
    secrets: list[str] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class Quest:
    id: str
    title: str
    description: str
    giver: str
    objectives: list[str] = field(default_factory=list)
    rewards: list[str] = field(default_factory=list)
    is_completed: bool = False


@dataclass
class Event:
    id: str
    title: str
    description: str
    choices: list[dict] = field(default_factory=list)
    consequences: dict[str, Any] = field(default_factory=dict)
    is_resolved: bool = False


@dataclass
class World:
    name: str
    description: str
    setting: str
    tone: str
    locations: dict[str, Location] = field(default_factory=dict)
    npcs: dict[str, Npc] = field(default_factory=dict)
    factions: list[dict] = field(default_factory=list)
    history: list[str] = field(default_factory=list)


@dataclass
class GameState:
    world: World | None = None
    player: Character | None = None
    current_location_id: str = ""
    phase: GamePhase = GamePhase.WORLD_CREATION
    quests: list[Quest] = field(default_factory=list)
    event_queue: list[Event] = field(default_factory=list)
    conversation_history: list[dict] = field(default_factory=list)
    narrative_log: list[str] = field(default_factory=list)
    turn_count: int = 0
