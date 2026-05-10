"""Game state manager with SQLite persistence."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from game_engine.models import GamePhase, GameState, World

logger = logging.getLogger("tavern.state")


class GameStateManager:
    """Manages game state with SQLite persistence."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def _ensure_db(self) -> None:
        """Create connection and apply schema migrations if needed."""
        if self._conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        self._run_migrations()

    def _run_migrations(self) -> None:
        """Apply all pending schema migrations (idempotent)."""
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_saves_name ON saves(name)
        """)
        conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def save(self, name: str, state: GameState) -> int:
        """Persist game state to database."""
        self._ensure_db()
        conn = self._get_connection()
        serialized = self._serialize(state)
        cursor = conn.execute(
            """INSERT INTO saves (name, state)
               VALUES (?, ?)
               ON CONFLICT(name) DO UPDATE SET
                   state = excluded.state,
                   updated_at = CURRENT_TIMESTAMP""",
            (name, json.dumps(serialized)),
        )
        conn.commit()
        logger.info("Game saved: %s", name)
        return cursor.lastrowid or 0

    def load(self, name: str) -> GameState | None:
        """Load game state from database."""
        self._ensure_db()
        conn = self._get_connection()
        row = conn.execute(
            "SELECT state FROM saves WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            return None
        data = json.loads(row["state"])
        return self._deserialize(data)

    def list_saves(self) -> list[dict[str, Any]]:
        """List all saved games."""
        self._ensure_db()
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT id, name, created_at, updated_at FROM saves ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]

    def delete_save(self, name: str) -> bool:
        """Delete a saved game."""
        self._ensure_db()
        conn = self._get_connection()
        cursor = conn.execute("DELETE FROM saves WHERE name = ?", (name,))
        conn.commit()
        return cursor.rowcount > 0

    def _serialize(self, state: GameState) -> dict[str, Any]:
        """Serialize game state to a JSON-compatible dict."""
        world_dict = None
        if state.world:
            world_dict = {
                "name": state.world.name,
                "description": state.world.description,
                "setting": state.world.setting,
                "tone": state.world.tone,
            }

        return {
            "world": world_dict,
            "phase": state.phase.value,
            "current_location_id": state.current_location_id,
            "turn_count": state.turn_count,
            "narrative_log": state.narrative_log,
        }

    def _deserialize(self, data: dict[str, Any]) -> GameState:
        """Deserialize dict back to GameState."""
        state = GameState()
        state.phase = GamePhase(data.get("phase", "world_creation"))
        state.current_location_id = data.get("current_location_id", "")
        state.turn_count = data.get("turn_count", 0)
        state.narrative_log = data.get("narrative_log", [])

        world_data = data.get("world")
        if world_data:
            state.world = World(
                name=world_data["name"],
                description=world_data.get("description", ""),
                setting=world_data.get("setting", ""),
                tone=world_data.get("tone", ""),
            )

        return state
