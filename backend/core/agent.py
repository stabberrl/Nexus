"""
Nexus AI - Multi-Agent Orchestrator
Orquesta agentes especializados: coordinator, system, web, code, documents.
Cada agente tiene tools, personalidad y contexto propio.
"""

import asyncio
from backend.core.llm import LLMEngine, ToolDefinition, DEFAULT_MODEL
from backend.core.system import SystemController
from backend.core.web import WebNavigator
from backend.core.memory import MemoryStore
from backend.core.planner import TaskPlanner
from backend.core.codex import CodeExecutor
from backend.core.documents import DocumentCreator


# ─── SPECIALIZED AGENTS ─────────────────────────────

class SystemAgent:
    """Agente especializado en control del PC."""

    def __init__(self, llm: LLMEngine):
        self.llm = llm
        self.sys = SystemController()
        self._register_tools()

    def _register_tools(self):
        self.llm.register_tool(ToolDefinition(
            name="execute_command",
            description="Ejecuta un comando de PowerShell",
            parameters={"type": "object", "properties": {"command": {"type": "string", "description": "Comando PowerShell"}}, "required": ["command"]},
            handler=self.sys.execute_powershell,
        ))
        self.llm.register_tool(ToolDefinition(
            name="open_application",
            description="Abre una aplicacion en el PC",
            parameters={"type": "object", "properties": {"app_name": {"type": "string", "description": "Nombre o ruta de la app"}}, "required": ["app_name"]},
            handler=self.sys.open_application,
        ))
        self.llm.register_tool(ToolDefinition(
            name="get_system_info",
            description="Obtiene informacion del sistema (CPU, RAM, disco, uptime)",
            parameters={"type": "object", "properties": {}},
            handler=lambda: self.sys.get_system_info(),
        ))
        self.llm.register_tool(ToolDefinition(
            name="list_processes",
            description="Lista los procesos en ejecucion (top 30)",
            parameters={"type": "object", "properties": {}},
            handler=lambda: self.sys.list_processes(),
        ))
        self.llm.register_tool(ToolDefinition(
            name="create_folder",
            description="Crea una carpeta en la ruta especificada",
            parameters={"type": "object", "properties": {"path": {"type": "string", "description": "Ruta de la carpeta"}}, "required": ["path"]},
            handler=self.sys.create_folder,
        ))
        self.llm.register_tool(ToolDefinition(
            name="list_directory",
            description="Lista el contenido de un directorio",
            parameters={"type": "object", "properties": {"path": {"type": "string", "description": "Ruta del directorio"}}, "required": ["path"]},
            handler=self.sys.list_directory,
        ))
        self.llm.register_tool(ToolDefinition(
            name="read_file",
            description="Lee el contenido de un archivo de texto",
            parameters={"type": "object", "properties": {"path": {"type": "string", "description": "Ruta del archivo"}}, "required": ["path"]},
            handler=self.sys.read_file,
        ))
        self.llm.register_tool(ToolDefinition(
            name="write_file",
            description="Escribe contenido en un archivo",
            parameters={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
            handler=self.sys.write_file,
        ))

    @property
    def system_prompt(self) -> str:
        return (
            "Eres un agente especializado en control del sistema de Nexus. "
            "Puedes ejecutar comandos, abrir aplicaciones, gestionar archivos, "
            "y monitorear el rendimiento del PC. Responde en espanol."
        )


class WebAgent:
    """Agente especializado en navegacion web."""

    def __init__(self, llm: LLMEngine):
        self.llm = llm
        self.web = WebNavigator()
        self._register_tools()

    def _register_tools(self):
        self.llm.register_tool(ToolDefinition(
            name="web_search",
            description="Busca informacion en internet",
            parameters={"type": "object", "properties": {"query": {"type": "string", "description": "Termino de busqueda"}}, "required": ["query"]},
            handler=self.web.search,
        ))
        self.llm.register_tool(ToolDefinition(
            name="fetch_page",
            description="Obtiene el contenido textual de una pagina web",
            parameters={"type": "object", "properties": {"url": {"type": "string", "description": "URL de la pagina"}}, "required": ["url"]},
            handler=self.web.fetch_page,
        ))

    @property
    def system_prompt(self) -> str:
        return (
            "Eres un agente especializado en navegacion web de Nexus. "
            "Puedes buscar en internet y extraer contenido de paginas web. "
            "Responde en espanol."
        )

    async def cleanup(self):
        await self.web.close()


class CodeAgent:
    """Agente especializado en ejecucion de codigo."""

    def __init__(self, llm: LLMEngine):
        self.llm = llm
        self.executor = CodeExecutor()
        self._register_tools()

    def _register_tools(self):
        self.llm.register_tool(ToolDefinition(
            name="execute_python",
            description="Ejecuta codigo Python en un entorno seguro",
            parameters={"type": "object", "properties": {"code": {"type": "string", "description": "Codigo Python a ejecutar"}}, "required": ["code"]},
            handler=self.executor.execute,
        ))

    @property
    def system_prompt(self) -> str:
        return (
            "Eres un agente especializado en codigo de Nexus. "
            "Puedes escribir y ejecutar codigo Python para resolver problemas, "
            "analizar datos, o automatizar tareas. "
            "Siempre explica que hace el codigo antes de ejecutarlo. "
            "Responde en espanol."
        )


class DocumentsAgent:
    """Agente especializado en creacion de documentos."""

    def __init__(self, llm: LLMEngine):
        self.llm = llm
        self.docs = DocumentCreator()
        self._register_tools()

    def _register_tools(self):
        self.llm.register_tool(ToolDefinition(
            name="create_word_document",
            description="Crea un documento Word con titulo y parrafos",
            parameters={"type": "object", "properties": {
                "title": {"type": "string", "description": "Titulo del documento"},
                "content": {"type": "array", "items": {"type": "string"}, "description": "Lista de parrafos"},
            }, "required": ["title", "content"]},
            handler=self.docs.create_word,
        ))
        self.llm.register_tool(ToolDefinition(
            name="create_excel_spreadsheet",
            description="Crea un archivo Excel con headers y filas de datos",
            parameters={"type": "object", "properties": {
                "headers": {"type": "array", "items": {"type": "string"}, "description": "Nombres de columnas"},
                "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "Filas de datos"},
            }, "required": ["headers", "rows"]},
            handler=self.docs.create_excel,
        ))
        self.llm.register_tool(ToolDefinition(
            name="create_powerpoint_presentation",
            description="Crea una presentacion PowerPoint con titulo y diapositivas",
            parameters={"type": "object", "properties": {
                "title": {"type": "string", "description": "Titulo de la presentacion"},
                "slides": {"type": "array", "items": {
                    "type": "array", "items": {"type": "string"}, "description": "[titulo diapositiva, contenido]"
                }},
            }, "required": ["title", "slides"]},
            handler=self.docs.create_presentation,
        ))

    @property
    def system_prompt(self) -> str:
        return (
            "Eres un agente especializado en crear documentos de Nexus. "
            "Puedes crear documentos Word, Excel y PowerPoint. "
            "Pregunta al usuario que contenido quiere incluir si no lo especifica. "
            "Responde en espanol."
        )


# ─── MAIN NEXUS ORCHESTRATOR ────────────────────────

class NexusAgent:
    """
    Orquestador multi-agente con memoria persistente y planificador.
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.memory = MemoryStore()
        self.planner = TaskPlanner()

        # Crear LLM base (sin tools) para el coordinator
        self.coordinator_llm = LLMEngine(model=model)
        self._session_id = "default"

        # Sub-agentes (cada uno con su propio LLM y tools)
        self.system_agent = SystemAgent(LLMEngine(model=model))
        self.web_agent = WebAgent(LLMEngine(model=model))
        self.code_agent = CodeAgent(LLMEngine(model=model))
        self.documents_agent = DocumentsAgent(LLMEngine(model=model))

    # ─── Chat principal ───

    async def chat_stream(self, message: str):
        """
        Procesa mensaje: planifica, delega a sub-agentes, retorna respuesta final.
        """
        # 1. Guardar mensaje en memoria
        await self.memory.save_message(self._session_id, "user", message)

        # 2. Planificar tareas (solo con el mensaje, sin contexto extra)
        tasks = await self.planner.plan(message)
        yield f"_Plan: {len(tasks)} tarea(s) identificada(s)_\n\n"

        # 3. Ejecutar cada tarea
        results = []
        for i, task in enumerate(tasks):
            desc = task["description"]
            agent_type = task["agent"]
            yield f"**Tarea {i+1}:** {desc} → *{agent_type}*\n\n"

            try:
                result = await self._execute_task(desc, agent_type)
                results.append({"task": desc, "agent": agent_type, **result})
                if result.get("output"):
                    yield f"{result['output']}\n\n"
            except Exception as e:
                results.append({"task": desc, "agent": agent_type, "error": str(e)})
                yield f"_Error en tarea: {e}_\n\n"

            await asyncio.sleep(0.3)

        # 4. Generar respuesta final con contexto de memoria
        context = await self._build_context(message)
        final = await self._generate_final_response(message, tasks, results, context)
        yield final

        # 5. Guardar respuesta en memoria
        await self.memory.save_message(self._session_id, "assistant", final)

    async def chat(self, message: str) -> str:
        chunks = []
        async for chunk in self.chat_stream(message):
            chunks.append(chunk)
        return "".join(chunks)

    # ─── Ejecución de tareas ───

    async def _execute_task(self, description: str, agent_type: str) -> dict:
        """Ejecuta una tarea: tools directas para system/web/code, LLM para assistant."""
        if agent_type == "system":
            return await self._execute_system_task(description)
        elif agent_type == "web":
            return await self._execute_specialized(
                self.web_agent.llm,
                self.web_agent.system_prompt,
                description,
            )
        elif agent_type == "code":
            return await self._execute_specialized(
                self.code_agent.llm,
                self.code_agent.system_prompt,
                description,
            )
        elif agent_type == "documents":
            return await self._execute_specialized(
                self.documents_agent.llm,
                self.documents_agent.system_prompt,
                description,
            )
        else:
            return await self._execute_specialized(
                self.coordinator_llm,
                "Te llamas Nexus. Eres un asistente de IA. Responde en espanol, se breve.",
                description,
            )

    async def _execute_system_task(self, description: str) -> dict:
        """Ejecuta tareas del sistema sin pasar por LLM: detecta la intencion y ejecuta directo."""
        desc_lower = description.lower()
        sys = SystemAgent(self.system_agent.llm)
        try:
            if "proceso" in desc_lower or "ejecutando" in desc_lower:
                procs = await sys.sys.list_processes()
                lines = [f"{i+1}. {p['name']} (CPU: {p.get('cpu_percent',0)}%, RAM: {p.get('memory_percent',0):.1f}%)" for i, p in enumerate(procs[:10])]
                return {"output": "Top procesos:\n" + "\n".join(lines), "error": None}

            if "ram" in desc_lower or "memoria" in desc_lower or "cpu" in desc_lower or "sistema" in desc_lower:
                info = await sys.sys.get_system_info()
                ram_pct = info.get("memory", {}).get("percent", 0)
                ram_free = info.get("memory", {}).get("available_gb", 0)
                ram_total = info.get("memory", {}).get("total_gb", 0)
                cpu = info.get("cpu_percent", 0)
                return {"output": f"RAM: {ram_free}GB libres de {ram_total}GB ({ram_pct}% usado) | CPU: {cpu}%", "error": None}

            if "archivo" in desc_lower or "carpeta" in desc_lower or "directorio" in desc_lower:
                import re
                path_match = re.search(r'[a-zA-Z]:\\(?:[^\\]+(?:\\)?)+', description)
                path = path_match.group(0) if path_match else "."
                items = await sys.sys.list_directory(path)
                lines = [f"{'📁' if i['type']=='folder' else '📄'} {i['name']}" for i in items[:20]]
                return {"output": f"Contenido de {path}:\n" + "\n".join(lines), "error": None}

            # Fallback: usar LLM del system agent
            return await self._execute_specialized(
                self.system_agent.llm, self.system_agent.system_prompt, description
            )
        except Exception as e:
            return {"output": "", "error": str(e)}

    async def _execute_specialized(self, llm: LLMEngine, system_prompt: str, task: str) -> dict:
        """Ejecuta un prompt en un LLM con herramientas y devuelve resultado."""
        original_prompt = llm._system_prompt
        def custom_prompt():
            return system_prompt
        llm._system_prompt = custom_prompt

        try:
            output = await llm.chat(task)
            return {"output": output, "error": None}
        except Exception as e:
            return {"output": "", "error": str(e)}
        finally:
            llm._system_prompt = original_prompt

    # ─── Contexto y respuesta final ───

    async def _build_context(self, message: str) -> str:
        """Construye contexto desde memoria (tolerante a fallos)."""
        parts = []
        try:
            facts = await self.memory.recall_all()
            if facts:
                parts.append("Hechos conocidos:\n" + "\n".join(f"- {k}: {v}" for k, v in facts.items()))
        except Exception:
            pass
        try:
            history = await self.memory.get_history(self._session_id, limit=6)
            if history:
                lines = []
                for h in history[-4:]:
                    lines.append(f"{h['role']}: {h['content'][:200]}")
                parts.append("Historial reciente:\n" + "\n".join(lines))
        except Exception:
            pass
        try:
            semantic = await self.memory.search_semantic(message, n=2)
            if semantic:
                parts.append("Memoria semantica:\n" + "\n".join(f"- {s['content'][:200]}" for s in semantic))
        except Exception:
            pass
        return "\n\n".join(parts)

    async def _generate_final_response(self, original: str, tasks: list, results: list, context: str = "") -> str:
        """Arma respuesta final con los datos exactos obtenidos (sin alucinaciones)."""
        lines = []
        for t, r in zip(tasks, results):
            output = (r.get("output", "") or "").strip()
            error = r.get("error")
            if error:
                lines.append(f"Error en '{t['description']}': {error}")
            elif output:
                lines.append(output)

        data_text = "\n".join(lines)

        prompt = (
            f"Resume estos datos como si fueras Nexus:\n{data_text}\n\n"
            f"Responde en espanol, maximo 3 oraciones, sin inventar informacion."
        )
        return await self.coordinator_llm.chat(prompt)

    # ─── Gestión ───

    def set_session(self, session_id: str):
        self._session_id = session_id

    def clear_history(self):
        self.coordinator_llm.clear_history()
        self.system_agent.llm.clear_history()
        self.web_agent.llm.clear_history()
        self.code_agent.llm.clear_history()

    async def cleanup(self):
        await self.web_agent.cleanup()
        self.memory.close()
