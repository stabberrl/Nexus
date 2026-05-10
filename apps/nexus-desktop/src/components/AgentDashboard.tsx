interface AgentTask {
  id: number;
  description: string;
  agent: string;
  status: "pending" | "running" | "done" | "error";
}

interface AgentDashboardProps {
  agentTasks: AgentTask[];
  activeAgent: string | null;
  isStreaming: boolean;
}

const AGENT_META: Record<string, { name: string; icon: string; color: string }> = {
  system: { name: "Sistema", icon: "⚙", color: "#6366f1" },
  web: { name: "Web", icon: "🌐", color: "#06b6d4" },
  code: { name: "Código", icon: "💻", color: "#22c55e" },
  documents: { name: "Docs", icon: "📄", color: "#f59e0b" },
  assistant: { name: "Asistente", icon: "🤖", color: "#8b5cf6" },
};

const AGENT_IDS = ["system", "web", "code", "documents", "assistant"];

export default function AgentDashboard({
  agentTasks,
  activeAgent,
  isStreaming,
}: AgentDashboardProps) {
  const activeTaskCounts: Record<string, number> = {};
  agentTasks.forEach((t) => {
    activeTaskCounts[t.agent] = (activeTaskCounts[t.agent] || 0) + 1;
  });

  return (
    <div className="agent-dashboard">
      {AGENT_IDS.map((id) => {
        const meta = AGENT_META[id];
        const isActive = activeAgent === id;
        const taskCount = activeTaskCounts[id] || 0;

        return (
          <div
            key={id}
            className={`agent-card ${isActive ? "active" : ""} ${isStreaming && isActive ? "pulse" : ""}`}
          >
            <div className="agent-card-icon" style={{ background: `${meta.color}22`, color: meta.color }}>
              {meta.icon}
            </div>
            <div className="agent-card-info">
              <div className="agent-card-name">{meta.name}</div>
              <div className="agent-card-status">
                {isActive ? (
                  <span style={{ color: meta.color }}>Trabajando{taskCount > 0 ? ` (${taskCount})` : ""}</span>
                ) : (
                  <span style={{ color: "var(--text-muted)" }}>Inactivo</span>
                )}
              </div>
            </div>
            <div
              className="agent-card-indicator"
              style={{
                background: isActive ? meta.color : "var(--text-muted)",
                opacity: isActive ? 1 : 0.3,
              }}
            />
          </div>
        );
      })}
    </div>
  );
}
