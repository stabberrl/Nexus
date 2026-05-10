import { useEffect, useRef } from 'react';
import { useGameStore } from '../lib/store';
import { audio, deriveMood } from '../lib/audio';

export function AudioController() {
  const screen = useGameStore((s) => s.screen);
  const world = useGameStore((s) => s.world);
  const gameState = useGameStore((s) => s.gameState);
  const isMuted = useGameStore((s) => s.isMuted);
  const initRef = useRef(false);

  useEffect(() => {
    if (initRef.current) return;
    const handler = () => {
      if (initRef.current) return;
      initRef.current = true;
      audio.start();
    };
    document.addEventListener('click', handler);
    document.addEventListener('keydown', handler);
    return () => {
      document.removeEventListener('click', handler);
      document.removeEventListener('keydown', handler);
    };
  }, []);

  useEffect(() => {
    if (!audio.started) return;
    const mood = deriveMood(screen, world, gameState?.phase);
    audio.setMood(mood);
  }, [screen, world, gameState?.phase]);

  useEffect(() => {
    audio.setVolume(isMuted ? 0 : 0.25);
  }, [isMuted]);

  return null;
}
