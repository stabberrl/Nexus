"""
Nexus AI - FastAPI Server v2 (Multi-Agent)
API REST + WebSockets con soporte multi-agente, memoria y código.
"""

import json
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.core.agent import NexusAgent
from backend.core.codex import CodeExecutor
from backend.core.system import SystemController
from backend.core.llm import LLMEngine


agent: NexusAgent = None
_telegram_proc: subprocess.Popen = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent, _telegram_proc
    agent = NexusAgent()

    # Iniciar Telegram bot como subproceso si hay token en entorno
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        try:
            _telegram_proc = subprocess.Popen(
                [sys.executable, "-m", "backend.core.telegram_bot", "--token", token],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            print(f"[Main] Telegram bot iniciado (PID: {_telegram_proc.pid})")
        except Exception as e:
            print(f"[Main] Error al iniciar Telegram bot: {e}")

    yield
    if _telegram_proc:
        _telegram_proc.terminate()
        try:
            _telegram_proc.wait(timeout=5)
        except Exception:
            _telegram_proc.kill()
    await agent.cleanup()


app = FastAPI(
    title="Nexus AI - Multi-Agent",
    description="API multi-agente con memoria persistente y ejecución de código",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost", "https://tauri.localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Modelos ───

class ChatRequest(BaseModel):
    message: str

class MemoryRequest(BaseModel):
    key: str
    value: str

class CodeRequest(BaseModel):
    code: str

class SessionRequest(BaseModel):
    session_id: str


# ─── Health ───

@app.get("/")
async def root():
    return {
        "name": "Nexus AI",
        "version": "2.0.0",
        "status": "running",
        "features": ["multi-agent", "memory", "code-execution", "task-planner"],
    }


# ─── Chat ───

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Mensaje vacío")
    response = await agent.chat(req.message)
    return {"response": response}


@app.post("/api/clear")
async def clear_history():
    agent.clear_history()
    return {"status": "ok"}


# ─── Sesiones ───

@app.post("/api/session")
async def set_session(req: SessionRequest):
    agent.set_session(req.session_id)
    return {"status": "ok", "session_id": req.session_id}


# ─── Memoria ───

@app.get("/api/memory")
async def get_memory():
    facts = await agent.memory.recall_all()
    return {"facts": facts}

@app.post("/api/memory")
async def set_memory(req: MemoryRequest):
    await agent.memory.remember(req.key, req.value)
    return {"status": "ok", "key": req.key}

@app.get("/api/memory/history")
async def get_history(session: str = "default", limit: int = 20):
    history = await agent.memory.get_history(session, limit)
    return {"history": history}


# ─── Código ───

executor = CodeExecutor()

@app.post("/api/code/run")
async def run_code(req: CodeRequest):
    result = await executor.execute(req.code)
    return result


# ─── Sistema ───

sys_ctrl = SystemController()

@app.get("/api/system")
async def get_system_stats():
    info = await sys_ctrl.get_system_info()
    return info


# ─── Modelos ───

llm_engine = LLMEngine()

@app.get("/api/models")
async def list_models():
    models = await llm_engine.list_models()
    return {"models": models}


# ─── Planificador ───

@app.post("/api/plan")
async def plan_task(req: ChatRequest):
    tasks = await agent.planner.plan(req.message)
    return {"tasks": tasks}


# ─── WebSocket Multi-Agente ───

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            message = payload.get("message", "")
            session = payload.get("session", "default")

            if not message.strip():
                await websocket.send_json({"type": "error", "content": "Mensaje vacío"})
                continue

            agent.set_session(session)
            async for chunk in agent.chat_stream(message):
                await websocket.send_json({"type": "token", "content": chunk})
            await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=8000, log_level="info")
