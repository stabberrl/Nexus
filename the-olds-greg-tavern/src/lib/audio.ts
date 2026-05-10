import * as Tone from 'tone';
import type { WorldData } from './api';

export type Mood = 'silence' | 'title' | 'warm' | 'dark' | 'airy' | 'grand' | 'ethereal';

interface MoodConfig {
  padNotes: string[];
  droneNote: string | null;
  filterFreq: number;
  filterLfoMin: number;
  filterLfoMax: number;
  reverbDecay: number;
  reverbWet: number;
  noiseType: Tone.NoiseType | null;
  noiseFilterFreq: number;
  noiseVolume: number;
  volume: number;
}

const MOODS: Record<Mood, MoodConfig> = {
  silence: {
    padNotes: [],
    droneNote: null,
    filterFreq: 1000,
    filterLfoMin: 500,
    filterLfoMax: 1500,
    reverbDecay: 3,
    reverbWet: 0,
    noiseType: null,
    noiseFilterFreq: 200,
    noiseVolume: 0,
    volume: 0,
  },
  title: {
    padNotes: ['C4', 'D#4', 'F#4'],
    droneNote: 'A3',
    filterFreq: 600,
    filterLfoMin: 300,
    filterLfoMax: 1200,
    reverbDecay: 6,
    reverbWet: 0.8,
    noiseType: null,
    noiseFilterFreq: 200,
    noiseVolume: 0,
    volume: 0.2,
  },
  warm: {
    padNotes: ['C4', 'E4', 'G4'],
    droneNote: 'C3',
    filterFreq: 1000,
    filterLfoMin: 600,
    filterLfoMax: 2000,
    reverbDecay: 3,
    reverbWet: 0.4,
    noiseType: 'brown',
    noiseFilterFreq: 250,
    noiseVolume: 0.03,
    volume: 0.25,
  },
  dark: {
    padNotes: ['D3', 'F3', 'A3'],
    droneNote: 'D2',
    filterFreq: 300,
    filterLfoMin: 100,
    filterLfoMax: 500,
    reverbDecay: 8,
    reverbWet: 0.9,
    noiseType: 'brown',
    noiseFilterFreq: 100,
    noiseVolume: 0.08,
    volume: 0.25,
  },
  airy: {
    padNotes: ['C4', 'G4', 'D5'],
    droneNote: 'G3',
    filterFreq: 2000,
    filterLfoMin: 800,
    filterLfoMax: 4000,
    reverbDecay: 5,
    reverbWet: 0.7,
    noiseType: 'pink',
    noiseFilterFreq: 500,
    noiseVolume: 0.04,
    volume: 0.2,
  },
  grand: {
    padNotes: ['F3', 'A3', 'C4'],
    droneNote: 'F2',
    filterFreq: 800,
    filterLfoMin: 400,
    filterLfoMax: 1600,
    reverbDecay: 6,
    reverbWet: 0.7,
    noiseType: 'white',
    noiseFilterFreq: 200,
    noiseVolume: 0.02,
    volume: 0.25,
  },
  ethereal: {
    padNotes: ['C4', 'D#4', 'F#4', 'A4'],
    droneNote: null,
    filterFreq: 1500,
    filterLfoMin: 600,
    filterLfoMax: 3000,
    reverbDecay: 7,
    reverbWet: 0.9,
    noiseType: null,
    noiseFilterFreq: 200,
    noiseVolume: 0,
    volume: 0.15,
  },
};

export function deriveMood(
  screen: string,
  world: WorldData | null,
  phase?: string,
): Mood {
  if (screen === 'title') return 'title';
  if (screen === 'new-game') return 'ethereal';
  if (screen === 'main-game') {
    if (!world) return 'title';
    if (phase === 'world_creation') return 'ethereal';

    const tone = (world.tone || '').toLowerCase();
    const setting = (world.setting || '').toLowerCase();

    if (tone.includes('oscuro') || tone.includes('siniestro') || tone.includes('tenebroso')) return 'dark';
    if (tone.includes('épico') || tone.includes('heroico') || tone.includes('grandioso')) return 'grand';
    if (tone.includes('misterio') || tone.includes('enigmático') || tone.includes('misterioso')) return 'airy';
    if (tone.includes('humor') || tone.includes('cómico') || tone.includes('alegre')) return 'warm';
    if (tone.includes('melancólico') || tone.includes('triste')) return 'dark';

    if (setting.includes('cyberpunk') || setting.includes('distopía') || setting.includes('horror')) return 'dark';
    if (setting.includes('fantasía') || setting.includes('medieval')) return 'warm';
    if (setting.includes('espacio') || setting.includes('sci-fi') || setting.includes('alien')) return 'ethereal';
    if (setting.includes('bosque') || setting.includes('naturaleza') || setting.includes('selva')) return 'airy';

    return 'warm';
  }
  return 'warm';
}

class AudioEngine {
  private initialized = false;
  private _started = false;
  private _currentMood: Mood = 'silence';
  private _volume = 0.25;
  private _muted = false;

  private masterVol!: Tone.Gain;
  private reverb!: Tone.Reverb;
  private filter!: Tone.Filter;
  private filterLfo!: Tone.LFO;
  private padSynth!: Tone.PolySynth;
  private droneSynth!: Tone.Synth;
  private noiseGen!: Tone.Noise;
  private noiseFilter!: Tone.Filter;
  private noiseGain!: Tone.Gain;

  get currentMood() { return this._currentMood; }
  get started() { return this._started; }
  get muted() { return this._muted; }

  async init(): Promise<void> {
    if (this.initialized) return;
    await Tone.start();

    this.masterVol = new Tone.Gain(0).toDestination();

    this.reverb = new Tone.Reverb({ decay: 4, wet: 0.5 });

    this.filter = new Tone.Filter(1000, 'lowpass');

    this.padSynth = new Tone.PolySynth(Tone.Synth, {
      oscillator: { type: 'sine' },
      envelope: { attack: 3, decay: 1, sustain: 0.8, release: 4 },
    });

    this.droneSynth = new Tone.Synth({
      oscillator: { type: 'triangle' },
      envelope: { attack: 4, decay: 1, sustain: 0.6, release: 5 },
    });

    this.noiseGen = new Tone.Noise('brown');
    this.noiseFilter = new Tone.Filter(200, 'lowpass');
    this.noiseGain = new Tone.Gain(0);
    this.noiseGen.connect(this.noiseFilter);
    this.noiseFilter.connect(this.noiseGain);
    this.noiseGain.connect(this.masterVol);

    this.padSynth.chain(this.filter, this.reverb, this.masterVol);
    this.droneSynth.chain(this.filter, this.reverb, this.masterVol);

    this.filterLfo = new Tone.LFO({
      frequency: 0.08,
      min: 200,
      max: 2000,
    });
    this.filterLfo.connect(this.filter.frequency);

    this.initialized = true;
  }

  async start(): Promise<void> {
    await this.init();
    if (this._started) return;
    this._started = true;
    this.filterLfo.start();
    this.noiseGen.start();
    this.setMood('title');
    this.masterVol.gain.value = this._muted ? 0 : this._volume;
  }

  setMood(mood: Mood): void {
    if (!this.initialized || !this._started) return;
    if (mood === this._currentMood) return;

    const config = MOODS[mood];
    if (!config) return;

    this._currentMood = mood;

    this.padSynth.releaseAll();
    this.droneSynth.triggerRelease();

    const rampTime = 2;
    this.filter.frequency.rampTo(config.filterFreq, rampTime);
    this.filterLfo.set({ min: config.filterLfoMin, max: config.filterLfoMax });
    this.reverb.set({ decay: config.reverbDecay });
    this.reverb.wet.rampTo(config.reverbWet, rampTime);

    if (config.noiseType) {
      this.noiseGen.type = config.noiseType;
      this.noiseFilter.frequency.rampTo(config.noiseFilterFreq, rampTime);
      this.noiseGain.gain.rampTo(config.noiseVolume, rampTime);
    } else {
      this.noiseGain.gain.rampTo(0, rampTime);
    }

    this.masterVol.gain.rampTo(
      this._muted ? 0 : config.volume,
      rampTime,
    );

    if (config.padNotes.length > 0 || config.droneNote) {
      Tone.getTransport().scheduleOnce(() => {
        if (config.padNotes.length > 0) {
          this.padSynth.triggerAttack(config.padNotes);
        }
        if (config.droneNote) {
          this.droneSynth.triggerAttack(config.droneNote);
        }
      }, `+${rampTime * 0.3}`);
    }
  }

  setVolume(vol: number): void {
    this._volume = Math.max(0, Math.min(1, vol));
    if (!this.initialized) return;
    const targetVol = this._muted ? 0 : this._volume;
    this.masterVol.gain.rampTo(targetVol, 0.3);
  }

  toggleMute(): boolean {
    this._muted = !this._muted;
    if (this.initialized) {
      const targetVol = this._muted ? 0 : this._volume;
      this.masterVol.gain.rampTo(targetVol, 0.3);
    }
    return this._muted;
  }

  stop(): void {
    if (!this.initialized) return;
    this.filterLfo.stop();
    this.noiseGen.stop();
    this.padSynth.releaseAll();
    this.droneSynth.triggerRelease();
    this._started = false;
  }
}

export const audio = new AudioEngine();
