import { create } from 'zustand';
import type { GameStateData, WorldData } from '../lib/api';

export type Screen = 'title' | 'new-game' | 'main-game';

interface GameStore {
  screen: Screen;
  setScreen: (screen: Screen) => void;

  gameState: GameStateData | null;
  setGameState: (state: GameStateData) => void;

  world: WorldData | null;
  setWorld: (world: WorldData) => void;

  narrative: string[];
  addNarrative: (line: string) => void;
  setNarrative: (lines: string[]) => void;

  playerIdea: string;
  setPlayerIdea: (idea: string) => void;

  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  error: string | null;
  setError: (error: string | null) => void;

  activeNpcId: string | null;
  setActiveNpcId: (id: string | null) => void;

  isMuted: boolean;
  toggleMute: () => void;
}

export const useGameStore = create<GameStore>((set) => ({
  screen: 'title',
  setScreen: (screen) => set({ screen }),

  gameState: null,
  setGameState: (gameState) => set({ gameState }),

  world: null,
  setWorld: (world) => set({ world }),

  narrative: [],
  addNarrative: (line) => set((state) => ({ narrative: [...state.narrative, line] })),
  setNarrative: (lines) => set({ narrative: lines }),

  playerIdea: '',
  setPlayerIdea: (playerIdea) => set({ playerIdea }),

  isLoading: false,
  setIsLoading: (isLoading) => set({ isLoading }),

  error: null,
  setError: (error) => set({ error }),

  activeNpcId: null,
  setActiveNpcId: (activeNpcId) => set({ activeNpcId }),

  isMuted: false,
  toggleMute: () =>
    set((state) => {
      const next = !state.isMuted;
      return { isMuted: next };
    }),
}));
