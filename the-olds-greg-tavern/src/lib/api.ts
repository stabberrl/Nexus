const BACKEND_URL = 'http://127.0.0.1:8765';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  return response.json();
}

export interface WorldData {
  name: string;
  description: string;
  setting: string;
  tone: string;
}

export interface GameStateData {
  phase: string;
  world: WorldData | null;
  current_location_id: string;
  turn_count: number;
  narrative_log: string[];
  conversation_history: { speaker: string; text: string }[];
}

export interface ActionResult {
  narrative: string;
  success: boolean;
  consequences: string[];
  suggested_actions: string[];
  turn: number;
}

export interface ChatResult {
  response: string;
  npc_name: string;
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  newGame: (playerIdea: string) =>
    request<{ world: WorldData; phase: string }>('/api/game/new', {
      method: 'POST',
      body: JSON.stringify({ player_idea: playerIdea }),
    }),

  getState: () => request<GameStateData>('/api/game/state'),

  performAction: (action: string, context?: Record<string, unknown>) =>
    request<ActionResult>('/api/game/action', {
      method: 'POST',
      body: JSON.stringify({ action, context: context ?? {} }),
    }),

  chat: (npcId: string, message: string) =>
    request<ChatResult>('/api/game/chat', {
      method: 'POST',
      body: JSON.stringify({ npc_id: npcId, message }),
    }),

  save: (name: string) =>
    request<{ status: string; name: string }>('/api/game/save', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),

  load: (name: string) => request<GameStateData>(`/api/game/load/${name}`, { method: 'POST' }),

  listSaves: () => request<{ id: number; name: string; created_at: string }[]>('/api/game/saves'),

  ollamaHealth: () => request<{ healthy: boolean; model: string }>('/api/ollama/health'),
};
