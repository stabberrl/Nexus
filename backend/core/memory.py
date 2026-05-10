"""
Nexus AI - Memory System
Memoria persistente: SQLite (hechos) + ChromaDB (semántica).
Carga diferida para minimizar consumo al inicio.
"""

import os
import json
import sqlite3
import asyncio
from datetime import datetime
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "nexus_memory.db")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")


class MemoryStore:
    """Memoria persistente de Nexus con SQLite + ChromaDB."""

    def __init__(self):
        self._db_conn: Optional[sqlite3.Connection] = None
        self._chroma_client = None
        self._chroma_collection = None

    # ─── SQLite Setup ───

    def _get_db(self) -> sqlite3.Connection:
        """Inicializa SQLite bajo demanda."""
        if self._db_conn is None:
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            self._db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self._db_conn.row_factory = sqlite3.Row
            self._db_conn.execute("PRAGMA journal_mode=WAL")
            self._init_schema()
        return self._db_conn

    def _init_schema(self):
        """Crea tablas si no existen."""
        db = self._db_conn
        db.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_session ON conversations(session_id);

            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                source TEXT,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER REFERENCES tasks(id),
                description TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                result TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS agent_state (
                agent_name TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        db.commit()

    # ─── Conversaciones ───

    async def save_message(self, session_id: str, role: str, content: str):
        """Guarda un mensaje en el historial."""
        db = self._get_db()
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: db.execute(
                "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )
        )
        db.commit()

    async def get_history(self, session_id: str, limit: int = 50) -> list[dict]:
        """Obtiene el historial de una sesión."""
        db = self._get_db()
        rows = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: db.execute(
                "SELECT role, content, timestamp FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        )
        return [{"role": r["role"], "content": r["content"], "time": r["timestamp"]} for r in reversed(rows)]

    async def clear_history(self, session_id: str):
        """Limpia el historial de una sesión."""
        db = self._get_db()
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: db.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        )
        db.commit()

    # ─── Hechos (memoria factual) ───

    async def remember(self, key: str, value: str, source: str = "user"):
        """Guarda un hecho en memoria a largo plazo."""
        db = self._get_db()
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: db.execute(
                "INSERT INTO facts (key, value, source, updated_at) VALUES (?, ?, ?, datetime('now')) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, source=excluded.source, updated_at=datetime('now')",
                (key, value, source),
            )
        )
        db.commit()

    async def recall(self, key: str) -> Optional[str]:
        """Recupera un hecho de la memoria."""
        db = self._get_db()
        row = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: db.execute("SELECT value FROM facts WHERE key = ?", (key,)).fetchone()
        )
        return row["value"] if row else None

    async def recall_all(self) -> dict[str, str]:
        """Recupera todos los hechos."""
        db = self._get_db()
        rows = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: db.execute("SELECT key, value FROM facts").fetchall()
        )
        return {r["key"]: r["value"] for r in rows}

    # ─── Memoria semántica (ChromaDB) ───

    def _get_chroma(self):
        """Inicializa ChromaDB bajo demanda."""
        if self._chroma_client is None:
            try:
                import chromadb
                self._chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
                self._chroma_collection = self._chroma_client.get_or_create_collection(
                    name="nexus_memory",
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as e:
                print(f"[Memory] ChromaDB no disponible: {e}")
        return self._chroma_collection

    async def _get_embedding_async(self, text: str) -> list[float]:
        """Genera embedding usando nomic-embed-text via Ollama."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "http://localhost:11434/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text},
                )
                if resp.status_code == 200:
                    return resp.json()["embedding"]
                return [0.0] * 768
        except Exception as e:
            print(f"[Memory] Error en embedding: {e}")
            return [0.0] * 768

    async def store_semantic(self, text: str, metadata: dict = None):
        """Almacena texto en memoria semántica."""
        collection = self._get_chroma()
        if collection is None:
            return

        embedding = await self._get_embedding_async(text)
        doc_id = f"mem_{datetime.now().timestamp()}"
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}],
        )

    async def search_semantic(self, query: str, n: int = 5) -> list[dict]:
        """Busca en memoria semántica por similitud."""
        collection = self._get_chroma()
        if collection is None:
            return []

        embedding = await self._get_embedding_async(query)
        results = collection.query(
            query_embeddings=[embedding],
            n_results=n,
        )

        docs = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                docs.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        return docs

    # ─── Tareas ───

    async def save_task(self, description: str, agent_type: str, parent_id: int = None) -> int:
        """Guarda una tarea y devuelve su ID."""
        db = self._get_db()
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: db.execute(
                "INSERT INTO tasks (parent_id, description, agent_type) VALUES (?, ?, ?)",
                (parent_id, description, agent_type),
            )
        )
        db.commit()
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]

    async def update_task(self, task_id: int, status: str, result: str = None):
        """Actualiza el estado de una tarea."""
        db = self._get_db()
        if result:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: db.execute(
                    "UPDATE tasks SET status = ?, result = ?, completed_at = datetime('now') WHERE id = ?",
                    (status, result, task_id),
                )
            )
        else:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: db.execute(
                    "UPDATE tasks SET status = ? WHERE id = ?",
                    (status, task_id),
                )
            )
        db.commit()

    async def get_pending_tasks(self) -> list[dict]:
        """Obtiene tareas pendientes."""
        db = self._get_db()
        rows = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: db.execute(
                "SELECT id, parent_id, description, agent_type, status FROM tasks WHERE status = 'pending' ORDER BY id"
            ).fetchall()
        )
        return [dict(r) for r in rows]

    # ─── Estado de agentes ───

    async def save_agent_state(self, agent_name: str, state: dict):
        """Guarda el estado de un agente."""
        db = self._get_db()
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: db.execute(
                "INSERT INTO agent_state (agent_name, state, updated_at) VALUES (?, ?, datetime('now')) "
                "ON CONFLICT(agent_name) DO UPDATE SET state=excluded.state, updated_at=datetime('now')",
                (agent_name, json.dumps(state)),
            )
        )
        db.commit()

    async def get_agent_state(self, agent_name: str) -> Optional[dict]:
        """Recupera el estado de un agente."""
        db = self._get_db()
        row = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: db.execute("SELECT state FROM agent_state WHERE agent_name = ?", (agent_name,)).fetchone()
        )
        return json.loads(row["state"]) if row else None

    # ─── Cierre ───

    def close(self):
        if self._db_conn:
            self._db_conn.close()
