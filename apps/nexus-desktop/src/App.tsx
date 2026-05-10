import { useState, useRef, useEffect, useCallback, type KeyboardEvent } from "react";
import ReactMarkdown from "react-markdown";
import VirtualOffice from "./components/VirtualOffice";
import AgentDashboard from "./components/AgentDashboard";

// ─── Types ───
interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

interface AgentTask {
  id: number;
  description: string;
  agent: string;
  status: "pending" | "running" | "done" | "error";
}

interface SystemStats {
  cpu_percent: number;
  memory: { total_gb: number; available_gb: number; percent: number };
  disk: { total_gb: number; free_gb: number; percent: number };
  uptime: string;
}

const AGENT_ICONS: Record<string, string> = {
  system: "⚙",
  web: "🌐",
  code: "💻",
  documents: "📄",
  assistant: "🤖",
};

const AGENT_COLORS: Record<string, string> = {
  system: "#6366f1",
  web: "#06b6d4",
  code: "#22c55e",
  documents: "#f59e0b",
  assistant: "#8b5cf6",
};

const SUGGESTIONS = [
  "¿Qué puedes hacer por mí?",
  "Muéstrame el estado del sistema",
  "Abre el bloc de notas",
  "Busca en internet sobre IA local",
  "Crea una carpeta llamada Nexus",
  "¿Cuánta RAM tengo?",
];

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [modelInfo, setModelInfo] = useState<string>("llama3.2");
  const [sysStats, setSysStats] = useState<SystemStats | null>(null);
  const [agentTasks, setAgentTasks] = useState<AgentTask[]>([]);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [view, setView] = useState<"chat" | "office">("chat");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // ─── Auto-scroll ───
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // ─── WebSocket connection ───
  useEffect(() => {
    function connect() {
      const ws = new WebSocket("ws://127.0.0.1:8000/ws/chat");
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onclose = () => {
        setWsConnected(false);
        setTimeout(connect, 2000);
      };

      ws.onerror = () => {
        ws.close();
      };

      let buffer = "";
      let taskIdCounter = 0;
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "token") {
            buffer += data.content;

            // Parse agent activity markers
            const planMatch = data.content.match(/\*\*Tarea (\d+):\*\* (.+?) → \*(\w+)\*/);
            if (planMatch) {
              taskIdCounter++;
              const newTask: AgentTask = {
                id: taskIdCounter,
                description: planMatch[2],
                agent: planMatch[3],
                status: "running",
              };
              setAgentTasks((prev) => [...prev, newTask]);
              setActiveAgent(planMatch[3]);
            }

            setMessages((prev) => {
              const updated = [...prev];
              if (updated.length > 0 && updated[updated.length - 1].role === "assistant") {
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  content: buffer,
                };
              }
              return updated;
            });
          } else if (data.type === "done") {
            setIsStreaming(false);
            setAgentTasks([]);
            setActiveAgent(null);
            buffer = "";
          } else if (data.type === "error") {
            setIsStreaming(false);
            setAgentTasks([]);
            setActiveAgent(null);
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content: `**Error:** ${data.content}`,
                timestamp: Date.now(),
              },
            ]);
            buffer = "";
          }
        } catch (e) {
          console.error("WS parse error:", e);
        }
      };
    }

    connect();
    fetchSysStats();
    fetchModels();

    return () => {
      wsRef.current?.close();
    };
  }, []);

  // ─── Fetch system stats ───
  async function fetchSysStats() {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/system");
      const data = await res.json();
      setSysStats(data);
    } catch {}
  }

  async function fetchModels() {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/models");
      const data = await res.json();
      if (data.models?.length > 0) {
        setModelInfo(data.models[0].name);
      }
    } catch {}
  }

  // ─── Send message ───
  async function sendMessage(content: string) {
    if (!content.trim() || isStreaming) return;

    const userMsg: Message = { role: "user", content: content.trim(), timestamp: Date.now() };
    const assistantMsg: Message = { role: "assistant", content: "", timestamp: Date.now() };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput("");
    setIsStreaming(true);

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message: content.trim() }));
    } else {
      // Fallback to REST API
      try {
        const res = await fetch("http://127.0.0.1:8000/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: content.trim() }),
        });
        const data = await res.json();
        setMessages((prev) => {
          const updated = [...prev];
          if (updated.length > 0 && updated[updated.length - 1].role === "assistant") {
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: data.response,
            };
          }
          return updated;
        });
      } catch (e) {
        setMessages((prev) => [
          ...prev.slice(0, -1),
          {
            role: "assistant",
            content: "**Error:** No pude conectar con el backend. ¿Está el servidor corriendo?",
            timestamp: Date.now(),
          },
        ]);
      }
      setIsStreaming(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  function handleSuggestion(suggestion: string) {
    sendMessage(suggestion);
  }

  function formatTimestamp(ts: number) {
    return new Date(ts).toLocaleTimeString("es-ES", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function renderOffice() {
    return (
      <>
        <div className="chat-header">
          <h2>Oficina Virtual</h2>
          <div className="model-selector">
            <span className={`status-dot ${wsConnected ? "" : "offline"}`} />
            <span>{wsConnected ? "Agentes activos" : "Desconectado"}</span>
          </div>
        </div>
        <div className="office-full" style={{ overflow: "auto", padding: 24 }}>
          <div style={{ width: "100%", maxWidth: 700, margin: "0 auto" }}>
            <VirtualOffice
              activeAgent={activeAgent}
              agentTasks={agentTasks}
              width={700}
              height={420}
            />
            <div style={{ marginTop: 16 }}>
              <AgentDashboard
                agentTasks={agentTasks}
                activeAgent={activeAgent}
                isStreaming={isStreaming}
              />
            </div>
          </div>
        </div>
      </>
    );
  }

  function renderChat() {
    if (messages.length === 0) {
      return (
        <>
          <div className="chat-header">
            <h2>Chat</h2>
            <div className="model-selector">
              <span className={`status-dot ${wsConnected ? "" : "offline"}`} />
              <span>{wsConnected ? "Conectado" : "Reconectando..."}</span>
              <span className="model-badge">{modelInfo}</span>
            </div>
          </div>
          <div className="messages-container">
            <div className="welcome-message">
              <h1>Nexus AI</h1>
              <p>Tu asistente personal con IA local. Puedo controlar tu PC, buscar en internet, crear archivos, ejecutar comandos y mas.</p>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="suggestion-chip" onClick={() => handleSuggestion(s)} disabled={isStreaming}>{s}</button>
                ))}
              </div>
            </div>
            <div ref={messagesEndRef} />
          </div>
          <ChatInputBox input={input} setInput={setInput} sendMessage={sendMessage} isStreaming={isStreaming} handleKeyDown={handleKeyDown} inputRef={inputRef} />
        </>
      );
    }
    return (
      <>
        <div className="chat-header">
          <h2>Chat{isStreaming && <span style={{ marginLeft: 8, fontSize: 12, color: "var(--accent-2)" }}> · Pensando...</span>}</h2>
          <div className="model-selector">
            <span className={`status-dot ${wsConnected ? "" : "offline"}`} />
            <span>{wsConnected ? "Conectado" : "Reconectando..."}</span>
            <span className="model-badge">{modelInfo}</span>
          </div>
        </div>
        <div className="messages-container">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="message-avatar">{msg.role === "user" ? "T" : "N"}</div>
              <div className="message-content">
                {msg.content ? <ReactMarkdown>{msg.content}</ReactMarkdown> : msg.role === "assistant" && (
                  <div className="typing-indicator"><span /><span /><span /></div>
                )}
                <div style={{ fontSize: 11, opacity: 0.5, marginTop: 6 }}>{msg.timestamp ? formatTimestamp(msg.timestamp) : ""}</div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <ChatInputBox input={input} setInput={setInput} sendMessage={sendMessage} isStreaming={isStreaming} handleKeyDown={handleKeyDown} inputRef={inputRef} />
      </>
    );
  }

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">N</div>
          <div>
            <div className="sidebar-title">Nexus</div>
            <div className="sidebar-subtitle">Asistente IA Local</div>
          </div>
        </div>
        <nav className="sidebar-nav">
          <button className={`nav-item ${view === "chat" ? "active" : ""}`} onClick={() => setView("chat")}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            Chat
          </button>
          <button className={`nav-item ${view === "office" ? "active" : ""}`} onClick={() => setView("office")}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            Oficina Virtual
          </button>
        </nav>
        {activeAgent && (
          <div style={{ padding: "12px", background: "var(--bg-card)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-color)", marginBottom: 12 }}>
            <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>Agente Activo</div>
            {agentTasks.map((t) => (
              <div key={t.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 0", fontSize: 12 }}>
                <span style={{ fontSize: 14 }}>{AGENT_ICONS[t.agent] || "🤖"}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.description}</div>
                  <div style={{ color: AGENT_COLORS[t.agent] || "var(--text-muted)", fontSize: 10 }}>{t.agent}</div>
                </div>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: AGENT_COLORS[t.agent] || "var(--accent-2)", animation: t.status === "running" ? "pulse 1s infinite" : "none" }} />
              </div>
            ))}
          </div>
        )}
        <div className="system-info">
          <h4>Sistema</h4>
          <div className="sys-stat">
            <span>Conexion</span>
            <span className="value"><span className={`status-dot ${wsConnected ? "" : "offline"}`} style={{ marginRight: 6 }} />{wsConnected ? "Online" : "Offline"}</span>
          </div>
          <div className="sys-stat">
            <span>Modelo</span>
            <span className="value" style={{ fontSize: 11 }}>{modelInfo}</span>
          </div>
          {sysStats && (
            <>
              <div className="sys-stat"><span>CPU</span><span className="value">{sysStats.cpu_percent}%</span></div>
              <div className="sys-stat"><span>RAM</span><span className="value">{sysStats.memory.percent}%</span></div>
            </>
          )}
        </div>
      </aside>
      <main className="main-content">
        {view === "office" ? renderOffice() : renderChat()}
      </main>
    </div>
  );
}

function ChatInputBox({ input, setInput, sendMessage, isStreaming, handleKeyDown, inputRef }: {
  input: string;
  setInput: (v: string) => void;
  sendMessage: (v: string) => void;
  isStreaming: boolean;
  handleKeyDown: (e: KeyboardEvent<HTMLTextAreaElement>) => void;
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
}) {
  return (
    <div className="input-area">
      <div className="input-wrapper">
        <textarea
          ref={inputRef}
          className="chat-input"
          placeholder="Escribe un mensaje a Nexus..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
          rows={1}
        />
        <button className="send-button" onClick={() => sendMessage(input)} disabled={!input.trim() || isStreaming}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
      <div className="input-footer">
        <span>Powered by Ollama · Modelos locales</span>
        <span>Enter para enviar · Shift+Enter para salto de linea</span>
      </div>
    </div>
  );
}

export default App;
