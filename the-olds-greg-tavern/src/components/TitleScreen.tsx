import { motion } from 'framer-motion';
import { useGameStore } from '../lib/store';

export function TitleScreen() {
  const { setScreen, setIsLoading, setError } = useGameStore();

  const handleStart = async () => {
    setError(null);
    setScreen('new-game');
  };

  const handleLoad = async () => {
    setError(null);
    setIsLoading(true);
    try {
      const { api } = await import('../lib/api');
      const saves = await api.listSaves();
      if (saves.length === 0) {
        setError('No hay partidas guardadas.');
        setIsLoading(false);
        return;
      }
      const lastSave = saves[0].name;
      const state = await api.load(lastSave);
      useGameStore.getState().setGameState(state);
      if (state.world) {
        useGameStore.getState().setWorld(state.world);
        useGameStore.getState().setNarrative(state.narrative_log);
      }
      useGameStore.getState().setScreen('main-game');
    } catch {
      setError('No se pudo cargar la partida.');
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-night flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--color-gold)_0%,_transparent_70%)] opacity-10" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.5 }}
        className="text-center z-10"
      >
        <motion.div
          animate={{ textShadow: ['0 0 20px rgba(201,168,76,0.3)', '0 0 40px rgba(201,168,76,0.6)', '0 0 20px rgba(201,168,76,0.3)'] }}
          transition={{ duration: 3, repeat: Infinity }}
          className="mb-4"
        >
          <h1 className="text-6xl font-bold text-gold text-shadow-glow mb-2">
            The Old's Greg Tavern
          </h1>
          <p className="text-xl text-parchment/60 italic">Donde cada historia comienza</p>
        </motion.div>

        <div className="mt-12 space-y-4">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleStart}
            className="block w-64 mx-auto px-8 py-3 bg-gold/20 border border-gold/50 text-gold rounded-lg
                       hover:bg-gold/30 transition-all font-semibold text-lg"
          >
            Nueva Historia
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleLoad}
            className="block w-64 mx-auto px-8 py-3 bg-stone-800/50 border border-stone-600/50 text-stone-300 rounded-lg
                       hover:bg-stone-700/50 transition-all"
          >
            Continuar Aventura
          </motion.button>
        </div>

        <p className="mt-16 text-stone-600 text-sm italic">
          Un RPG narrativo impulsado por IA · 100% local y gratuito
        </p>
      </motion.div>
    </div>
  );
}
