import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Book, MessageCircle, User, Map, Send, Save, Volume2, VolumeX } from 'lucide-react';
import { useGameStore } from '../lib/store';
import { api } from '../lib/api';

export function MainGameScreen() {
  const { world, narrative, gameState, setGameState, setError, addNarrative, isMuted, toggleMute } = useGameStore();
  const [actionInput, setActionInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [suggestedActions, setSuggestedActions] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'narrative' | 'conversation' | 'character'>('narrative');

  const handleAction = async () => {
    if (!actionInput.trim()) return;
    setIsProcessing(true);
    addNarrative(`> ${actionInput}`);

    try {
      const result = await api.performAction(actionInput);
      addNarrative(result.narrative);
      setSuggestedActions(result.suggested_actions || []);
      setActionInput('');
      const state = await api.getState();
      setGameState(state);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al procesar acción';
      setError(message);
    }
    setIsProcessing(false);
  };

  const handleSave = async () => {
    try {
      await api.save(`partida_${Date.now()}`);
      setError(null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error desconocido';
      setError(`Error al guardar: ${msg}`);
    }
  };

  const handleSuggestedAction = (action: string) => {
    setActionInput(action);
  };

  return (
    <div className="h-screen bg-night flex flex-col">
      <header className="flex items-center justify-between px-6 py-3 bg-stone-900/80 border-b border-stone-800">
        <div className="flex items-center gap-3">
          <Book className="w-5 h-5 text-gold" />
          <h1 className="text-lg font-bold text-gold">{world?.name || 'La Taberna'}</h1>
          {gameState && (
            <span className="text-stone-500 text-sm">Turno {gameState.turn_count}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={toggleMute}
            className="p-1.5 text-stone-500 hover:text-gold transition-colors"
            title={isMuted ? 'Activar sonido' : 'Silenciar'}
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </motion.button>
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={handleSave}
            className="px-3 py-1.5 text-sm bg-stone-800 border border-stone-700 text-stone-300 rounded hover:bg-stone-700 transition-all flex items-center gap-1.5"
          >
            <Save className="w-3.5 h-3.5" />
            Guardar
          </motion.button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin">
            <AnimatePresence>
              {narrative.length === 0 && world && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-12"
                >
                  <Map className="w-16 h-16 text-gold/30 mx-auto mb-4" />
                  <h2 className="text-xl text-gold mb-2">{world.name}</h2>
                  <p className="text-stone-400 italic max-w-lg mx-auto">{world.description}</p>
                  <hr className="border-stone-800 my-6 max-w-md mx-auto" />
                  <p className="text-stone-500">¿Qué haces? Describe tu acción...</p>
                </motion.div>
              )}
              {narrative.map((line, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: line.startsWith('>') ? -10 : 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  className={`${line.startsWith('>') ? 'text-gold/80 font-semibold pl-4 border-l-2 border-gold/40' : 'text-parchment/90 leading-relaxed'}`}
                >
                  {line}
                </motion.div>
              ))}
            </AnimatePresence>

            {suggestedActions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 p-4 bg-stone-900/60 border border-stone-800 rounded-lg"
              >
                <p className="text-xs text-stone-500 mb-2 uppercase tracking-wider">Acciones sugeridas</p>
                <div className="flex flex-wrap gap-2">
                  {suggestedActions.map((action, i) => (
                    <motion.button
                      key={i}
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => handleSuggestedAction(action)}
                      className="px-3 py-1.5 text-sm bg-stone-800 border border-stone-700 text-stone-300 rounded-lg hover:bg-gold/10 hover:border-gold/30 transition-all"
                    >
                      {action}
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}
          </div>

          <div className="p-4 bg-stone-900/80 border-t border-stone-800">
            <div className="flex gap-3 max-w-4xl mx-auto">
              <input
                value={actionInput}
                onChange={(e) => setActionInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !isProcessing && handleAction()}
                placeholder="Describe tu acción..."
                className="flex-1 bg-stone-800 border border-stone-700 rounded-lg px-4 py-2.5 text-parchment
                           placeholder:text-stone-600 focus:border-gold/50 focus:outline-none font-serif"
                disabled={isProcessing}
              />
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={handleAction}
                disabled={isProcessing || !actionInput.trim()}
                className="px-5 py-2.5 bg-gold/20 border border-gold/50 text-gold rounded-lg
                           hover:bg-gold/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all
                           flex items-center gap-2"
              >
                <Send className="w-4 h-4" />
                Actuar
              </motion.button>
            </div>
          </div>
        </div>

        <aside className="w-72 bg-stone-900/50 border-l border-stone-800 flex flex-col">
          <div className="flex border-b border-stone-800">
            {[
              { id: 'narrative', icon: Book, label: 'Bitácora' },
              { id: 'conversation', icon: MessageCircle, label: 'Diálogo' },
              { id: 'character', icon: User, label: 'Personaje' },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`flex-1 flex flex-col items-center py-3 text-xs transition-all ${
                    isActive ? 'text-gold border-t-2 border-gold bg-gold/5' : 'text-stone-500 hover:text-stone-300'
                  }`}
                >
                  <Icon className="w-4 h-4 mb-1" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
            {activeTab === 'narrative' && (
              <div className="space-y-3">
                <h3 className="text-xs uppercase tracking-wider text-stone-500 mb-3">Estado del Mundo</h3>
                {gameState && (
                  <>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-stone-400">Turno</span>
                      <span className="text-gold font-bold">{gameState.turn_count}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-stone-400">Locación</span>
                      <span className="text-parchment">{gameState.current_location_id || 'Desconocida'}</span>
                    </div>
                  </>
                )}
                {world && (
                  <div className="mt-4 p-3 bg-stone-800/50 rounded-lg">
                    <p className="text-xs text-stone-500 mb-1">Ambientación</p>
                    <p className="text-sm text-gold capitalize">{world.setting}</p>
                    <p className="text-xs text-stone-500 mt-1">Tono</p>
                    <p className="text-sm text-ember capitalize">{world.tone}</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'conversation' && gameState?.conversation_history && (
              <div className="space-y-3">
                <h3 className="text-xs uppercase tracking-wider text-stone-500 mb-3">Historial</h3>
                {gameState.conversation_history.length === 0 && (
                  <p className="text-stone-600 text-sm italic">Aún no has hablado con nadie.</p>
                )}
                {gameState.conversation_history.slice(-10).map((entry, i) => (
                  <div key={i} className={`text-sm ${entry.speaker === 'player' ? 'text-gold/70' : 'text-parchment/80'}`}>
                    <span className="font-semibold">{entry.speaker}: </span>
                    <span>{entry.text}</span>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'character' && (
              <div className="space-y-3">
                <h3 className="text-xs uppercase tracking-wider text-stone-500 mb-3">Aventurero</h3>
                <p className="text-stone-600 text-sm italic">Tu historia comienza ahora...</p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
