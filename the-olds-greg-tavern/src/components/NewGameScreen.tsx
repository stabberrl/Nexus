import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Send } from 'lucide-react';
import { useGameStore } from '../lib/store';
import { api } from '../lib/api';

export function NewGameScreen() {
  const { playerIdea, setPlayerIdea, setWorld, setGameState, setScreen, setIsLoading, setError } = useGameStore();
  const [isGenerating, setIsGenerating] = useState(false);
  const [worldPreview, setWorldPreview] = useState<{ name: string; description: string; setting: string; tone: string } | null>(null);

  const handleGenerate = async () => {
    if (!playerIdea.trim()) return;
    setIsGenerating(true);
    setError(null);

    try {
      const result = await api.newGame(playerIdea);
      setWorld(result.world);
      setWorldPreview(result.world);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al crear el mundo';
      setError(message);
    }
    setIsGenerating(false);
  };

  const handleStartAdventure = () => {
    setIsLoading(true);
    api.getState().then((state) => {
      setGameState(state);
      setScreen('main-game');
    }).catch((err) => {
      setError(err instanceof Error ? err.message : 'Error al iniciar');
    }).finally(() => setIsLoading(false));
  };

  return (
    <div className="min-h-screen bg-night p-8">
      <div className="max-w-3xl mx-auto">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl font-bold text-gold mb-2"
        >
          Forja tu Mundo
        </motion.h1>
        <p className="text-stone-400 mb-8">Describe el mundo que quieres explorar. La IA lo hará realidad.</p>

        <div className="relative">
          <textarea
            value={playerIdea}
            onChange={(e) => setPlayerIdea(e.target.value)}
            placeholder="Ej: Un reino de fantasía donde la magia está prohibida y los antiguos dioses han despertado..."
            className="w-full h-32 bg-stone-900/80 border border-stone-700 rounded-lg p-4 text-parchment
                       placeholder:text-stone-600 focus:border-gold/50 focus:outline-none resize-none
                       font-serif text-lg"
            disabled={isGenerating}
          />
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleGenerate}
            disabled={isGenerating || !playerIdea.trim()}
            className="absolute bottom-3 right-3 px-4 py-2 bg-gold/20 border border-gold/50 text-gold rounded-lg
                       hover:bg-gold/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all
                       flex items-center gap-2"
          >
            {isGenerating ? (
              <span className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 animate-pulse" />
                Forjando...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Send className="w-4 h-4" />
                Crear Mundo
              </span>
            )}
          </motion.button>
        </div>

        <AnimatePresence>
          {worldPreview && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-8 p-6 bg-stone-900/60 border border-gold/20 rounded-lg"
            >
              <h2 className="text-2xl font-bold text-gold mb-2">{worldPreview.name}</h2>
              <div className="flex gap-3 mb-4">
                <span className="px-3 py-1 bg-gold/10 border border-gold/30 text-gold text-sm rounded-full">
                  {worldPreview.setting}
                </span>
                <span className="px-3 py-1 bg-ember/10 border border-ember/30 text-ember text-sm rounded-full">
                  {worldPreview.tone}
                </span>
              </div>
              <p className="text-parchment/80 leading-relaxed">{worldPreview.description}</p>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleStartAdventure}
                className="mt-6 px-6 py-3 bg-gold/20 border border-gold/50 text-gold rounded-lg
                           hover:bg-gold/30 transition-all font-semibold"
              >
                Comenzar Aventura
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
