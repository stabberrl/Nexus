import { useRef, useEffect, useCallback } from "react";

interface AgentEntity {
  id: string;
  name: string;
  icon: string;
  color: string;
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  status: "idle" | "working" | "error";
  pulsePhase: number;
}

interface VirtualOfficeProps {
  activeAgent: string | null;
  agentTasks: { id: number; description: string; agent: string; status: string }[];
  width?: number;
  height?: number;
}

const AGENT_CONFIGS: Record<string, { name: string; icon: string; color: string }> = {
  system: { name: "Sistema", icon: "⚙", color: "#6366f1" },
  web: { name: "Web", icon: "🌐", color: "#06b6d4" },
  code: { name: "Código", icon: "💻", color: "#22c55e" },
  documents: { name: "Docs", icon: "📄", color: "#f59e0b" },
  assistant: { name: "Asistente", icon: "🤖", color: "#8b5cf6" },
};

const DESK_POSITIONS = [
  { x: 0.15, y: 0.3 },
  { x: 0.38, y: 0.2 },
  { x: 0.62, y: 0.25 },
  { x: 0.38, y: 0.6 },
  { x: 0.62, y: 0.65 },
];

export default function VirtualOffice({
  activeAgent,
  agentTasks,
  width = 400,
  height = 300,
}: VirtualOfficeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const agentsRef = useRef<AgentEntity[]>([]);
  const animFrameRef = useRef<number>(0);
  const timeRef = useRef(0);

  const initAgents = useCallback(() => {
    const keys = Object.keys(AGENT_CONFIGS);
    agentsRef.current = keys.map((key, i) => {
      const cfg = AGENT_CONFIGS[key];
      const pos = DESK_POSITIONS[i] || { x: 0.5, y: 0.5 };
      return {
        id: key,
        name: cfg.name,
        icon: cfg.icon,
        color: cfg.color,
        x: pos.x * width,
        y: pos.y * height,
        targetX: pos.x * width,
        targetY: pos.y * height,
        status: "idle" as const,
        pulsePhase: Math.random() * Math.PI * 2,
      };
    });
  }, [width, height]);

  useEffect(() => {
    initAgents();
  }, [initAgents]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    function drawDesk(ctx: CanvasRenderingContext2D, x: number, y: number, color: string) {
      ctx.save();
      ctx.translate(x, y);

      // Desk body
      const deskW = 60;
      const deskH = 40;
      const gradient = ctx.createLinearGradient(-deskW / 2, -deskH / 2, deskW / 2, deskH / 2);
      gradient.addColorStop(0, "rgba(30, 30, 60, 0.8)");
      gradient.addColorStop(1, "rgba(20, 20, 40, 0.8)");
      ctx.fillStyle = gradient;
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(-deskW / 2, -deskH / 2, deskW, deskH, 4);
      ctx.fill();
      ctx.stroke();

      // Monitor
      ctx.fillStyle = "rgba(15, 15, 30, 0.9)";
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(-15, -18, 30, 20, 2);
      ctx.fill();
      ctx.stroke();

      // Screen glow
      ctx.fillStyle = `${color}22`;
      ctx.beginPath();
      ctx.roundRect(-12, -15, 24, 14, 1);
      ctx.fill();

      // Screen content (scan lines)
      ctx.fillStyle = `${color}11`;
      for (let i = -12; i < 12; i += 3) {
        ctx.fillRect(i, -14, 2, 12);
      }

      ctx.restore();
    }

    function drawAgent(
      ctx: CanvasRenderingContext2D,
      agent: AgentEntity,
      isActive: boolean,
      time: number
    ) {
      const pulse = Math.sin(time * 0.003 + agent.pulsePhase) * 0.3 + 0.7;
      const radius = isActive ? 16 + pulse * 4 : 14;

      ctx.save();
      ctx.translate(agent.x, agent.y);

      // Glow
      const glowRadius = radius * 2.5;
      const glow = ctx.createRadialGradient(0, 0, 0, 0, 0, glowRadius);
      glow.addColorStop(0, `${agent.color}${isActive ? "44" : "22"}`);
      glow.addColorStop(1, "transparent");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(0, 0, glowRadius, 0, Math.PI * 2);
      ctx.fill();

      // Body circle
      const gradient = ctx.createRadialGradient(-4, -4, 0, 0, 0, radius);
      gradient.addColorStop(0, isActive ? "#fff" : agent.color);
      gradient.addColorStop(0.3, agent.color);
      gradient.addColorStop(1, `${agent.color}99`);
      ctx.fillStyle = gradient;
      ctx.strokeStyle = isActive ? "#fff" : agent.color;
      ctx.lineWidth = isActive ? 2 : 1;
      ctx.beginPath();
      ctx.arc(0, 0, radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // Icon
      ctx.fillStyle = isActive ? agent.color : "#fff";
      ctx.font = `${radius * 0.8}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(agent.icon, 0, 1);

      // Name label
      ctx.fillStyle = isActive ? "#fff" : "rgba(255,255,255,0.6)";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillText(agent.name, 0, radius + 4);

      // Status ring
      if (isActive) {
        ctx.strokeStyle = agent.color;
        ctx.lineWidth = 2;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.arc(0, 0, radius + 4, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Connection lines to nearby agents (subtle)
      ctx.restore();
    }

    function drawConnections(
      ctx: CanvasRenderingContext2D,
      agents: AgentEntity[],
      time: number
    ) {
      for (let i = 0; i < agents.length; i++) {
        for (let j = i + 1; j < agents.length; j++) {
          const a = agents[i];
          const b = agents[j];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 200 && (a.status === "working" || b.status === "working")) {
            const alpha = (1 - dist / 200) * 0.15;
            const phase = Math.sin(time * 0.002 + i + j) * 0.5 + 0.5;
            ctx.strokeStyle = `rgba(99, 102, 241, ${alpha * phase})`;
            ctx.lineWidth = 1;
            ctx.setLineDash([2, 4]);
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
            ctx.setLineDash([]);
          }
        }
      }
    }

    function render(time: number) {
      if (!canvas || !ctx) return;
      ctx.clearRect(0, 0, width, height);

      // Background
      const bg = ctx.createRadialGradient(width / 2, height / 2, 0, width / 2, height / 2, width * 0.6);
      bg.addColorStop(0, "#14142a");
      bg.addColorStop(1, "#0a0a14");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, width, height);

      // Grid pattern
      ctx.strokeStyle = "rgba(99, 102, 241, 0.04)";
      ctx.lineWidth = 1;
      const gridSize = 30;
      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      const agents = agentsRef.current;
      const activeIds = agentTasks.map((t) => t.agent);

      // Update agent statuses
      agents.forEach((a) => {
        a.status = activeIds.includes(a.id) ? "working" : "idle";
        if (a.status === "working") {
          a.targetX = a.x + (Math.random() - 0.5) * 4;
          a.targetY = a.y + (Math.random() - 0.5) * 3;
        }
        a.x += (a.targetX - a.x) * 0.05;
        a.y += (a.targetY - a.y) * 0.05;
      });

      // Draw connections
      drawConnections(ctx, agents, time);

      // Draw desks
      agents.forEach((a) => {
        const pos = DESK_POSITIONS[agents.indexOf(a)] || { x: 0.5, y: 0.5 };
        drawDesk(ctx, pos.x * width, pos.y * height + 18, a.color);
      });

      // Draw agents
      agents.forEach((a) => {
        drawAgent(ctx, a, a.status === "working", time);
      });

      animFrameRef.current = requestAnimationFrame(render);
    }

    animFrameRef.current = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [width, height, agentTasks, activeAgent]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{
        width: "100%",
        height: "auto",
        borderRadius: 12,
        border: "1px solid rgba(99, 102, 241, 0.15)",
        background: "#0a0a14",
        display: "block",
      }}
    />
  );
}
