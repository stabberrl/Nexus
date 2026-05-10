"""Game API routes for world creation, exploration, and interaction."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from game_engine.conversation_manager import ConversationManager
from game_engine.game_state import GameStateManager
from game_engine.location_generator import LocationGenerator
from game_engine.models import GamePhase, GameState, World
from game_engine.narrative_engine import NarrativeEngine
from game_engine.npc_generator import NpcGenerator
from game_engine.ollama_bridge import OllamaBridge
from game_engine.quest_system import QuestSystem
from game_engine.world_generator import WorldGenerator

logger = logging.getLogger("tavern.api")

DATA_DIR = Path(os.getenv("TAVERN_DATA_DIR", str(Path.home() / ".oldstavern")))

ollama = OllamaBridge()
world_gen = WorldGenerator(ollama)
narrative = NarrativeEngine(ollama)
conversation = ConversationManager(ollama)
quests = QuestSystem(ollama)
locations = LocationGenerator(ollama)
npcs = NpcGenerator(ollama)
state_mgr = GameStateManager(DATA_DIR / "tavern.db")

router = APIRouter(prefix="/api/game", tags=["game"])

# In-memory active game state
active_game: GameState | None = None


class CreateWorldRequest(BaseModel):
    player_idea: str


class ActionRequest(BaseModel):
    action: str
    context: dict = {}


class ChatRequest(BaseModel):
    npc_id: str
    message: str


class SaveRequest(BaseModel):
    name: str


@router.post("/new")
async def new_game(request: CreateWorldRequest) -> dict:
    """Create a new world from the player's initial idea."""
    global active_game

    try:
        world = await world_gen.create_world_from_conversation(request.player_idea)
        active_game = GameState(world=world)
        active_game.phase = GamePhase.WORLD_CREATION

        return {
            "world": {
                "name": world.name,
                "description": world.description,
                "setting": world.setting,
                "tone": world.tone,
            },
            "phase": "world_creation",
        }
    except Exception as error:
        logger.exception("Failed to create world")
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/state")
async def get_state() -> dict:
    """Get current game state."""
    if active_game is None:
        return {"phase": "no_game", "world": None}
    return _serialize_game_state(active_game)


@router.post("/action")
async def perform_action(request: ActionRequest) -> dict:
    """Process a player action and return narrative result."""
    global active_game

    if active_game is None or active_game.world is None:
        raise HTTPException(status_code=400, detail="No active game")

    try:
        world_dict = {
            "name": active_game.world.name,
            "description": active_game.world.description,
            "setting": active_game.world.setting,
            "tone": active_game.world.tone,
        }

        result = await narrative.resolve_action(
            action=request.action,
            context={
                "world": world_dict,
                "player_context": request.context,
                "narrative_log": active_game.narrative_log[-5:],
            },
        )

        active_game.turn_count += 1
        active_game.narrative_log.append(
            f"[{active_game.turn_count}] {request.action}: {result.get('narrative', '')}"
        )

        return {
            "narrative": result.get("narrative", ""),
            "success": result.get("success", True),
            "consequences": result.get("consequences", []),
            "suggested_actions": result.get("suggested_actions", []),
            "turn": active_game.turn_count,
        }
    except Exception as error:
        logger.exception("Action failed")
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/chat")
async def talk_to_npc(request: ChatRequest) -> dict:
    """Talk to an NPC."""
    if active_game is None or active_game.world is None:
        raise HTTPException(status_code=400, detail="No active game")

    npc = active_game.world.npcs.get(request.npc_id)
    if npc is None:
        raise HTTPException(status_code=404, detail="NPC not found")

    try:
        response = await conversation.generate_response(
            npc_name=npc.name,
            npc_personality=npc.personality,
            npc_role=npc.role,
            player_message=request.message,
            conversation_history=active_game.conversation_history,
            npc_memory=npc.memory,
            world_context={
                "world_name": active_game.world.name,
                "current_location": active_game.current_location_id,
            },
        )

        active_game.conversation_history.append(
            {"speaker": "player", "text": request.message}
        )
        active_game.conversation_history.append(
            {"speaker": npc.name, "text": response}
        )

        return {"response": response, "npc_name": npc.name}
    except Exception as error:
        logger.exception("Chat failed")
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/save")
async def save_game(request: SaveRequest) -> dict:
    """Save current game state."""
    if active_game is None:
        raise HTTPException(status_code=400, detail="No active game")
    if active_game.world is None:
        raise HTTPException(status_code=400, detail="No world created yet")
    try:
        logger.info("Saving game: %s, world=%s, turn=%d",
                     request.name, active_game.world.name, active_game.turn_count)
        state_mgr.save(request.name, active_game)
        return {"status": "saved", "name": request.name}
    except Exception as error:
        logger.exception("Save failed: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/load/{name}")
async def load_game(name: str) -> dict:
    """Load a saved game."""
    global active_game
    state = state_mgr.load(name)
    if state is None:
        raise HTTPException(status_code=404, detail="Save not found")
    active_game = state
    return _serialize_game_state(state)


@router.get("/saves")
async def list_saves() -> list[dict]:
    """List all saved games."""
    return state_mgr.list_saves()


def _serialize_game_state(state: GameState) -> dict:
    """Serialize game state for API response."""
    world_data = None
    if state.world:
        world_data = {
            "name": state.world.name,
            "description": state.world.description,
            "setting": state.world.setting,
            "tone": state.world.tone,
        }

    return {
        "phase": state.phase.value,
        "world": world_data,
        "current_location_id": state.current_location_id,
        "turn_count": state.turn_count,
        "narrative_log": state.narrative_log[-10:] if state.narrative_log else [],
        "conversation_history": state.conversation_history[-10:] if state.conversation_history else [],
    }
