import { useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, Volume2, VolumeX } from 'lucide-react';
import { useGameStore } from './lib/store';
import { TitleScreen } from './components/TitleScreen';
import { NewGameScreen } from './components/NewGameScreen';
import { MainGameScreen } from './components/MainGameScreen';
import { AudioController } from './components/AudioController';

function App() {
  const { screen, error, setError, isLoading, isMuted, toggleMute } = useGameStore();

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error, setError]);

  return (
    <div className="min-h-screen bg-night text-parchment font-serif">
      <AudioController />

      <AnimatePresence mode="wait">
        {screen === 'title' && (
          <motion.div key="title" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <TitleScreen />
          </motion.div>
        )}
        {screen === 'new-game' && (
          <motion.div key="new-game" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <NewGameScreen />
          </motion.div>
        )}
        {screen === 'main-game' && (
          <motion.div key="main-game" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <MainGameScreen />
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-4 right-4 z-50 px-4 py-3 bg-blood/90 border border-blood/50 text-parchment rounded-lg shadow-lg flex items-center gap-2"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileTap={{ scale: 0.9 }}
        onClick={toggleMute}
        className="fixed bottom-4 right-4 z-50 p-2.5 bg-stone-900/80 border border-stone-700 rounded-full text-stone-400 hover:text-gold hover:border-gold/40 transition-all"
        title={isMuted ? 'Activar sonido' : 'Silenciar'}
      >
        {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
      </motion.button>

      {isLoading && (
        <div className="fixed inset-0 bg-night/80 flex items-center justify-center z-40">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="w-8 h-8 border-2 border-gold/50 border-t-gold rounded-full"
          />
        </div>
      )}
    </div>
  );
}

export default App;
