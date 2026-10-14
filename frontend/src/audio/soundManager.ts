import type { SoundSettings, SoundEventConfig, PlayEventOptions, SoundCategory, SoundTheme } from './soundTypes';
import { DEFAULT_SOUND_SETTINGS, DEFAULT_SOUND_EVENTS } from './soundPresets';
import { soundSynthesizer } from './soundSynthesizer';

const STORAGE_KEY = 'fraudsense_sound_settings_v1';

const cloneDefaultSettings = (): SoundSettings => JSON.parse(JSON.stringify(DEFAULT_SOUND_SETTINGS));

class SoundManager {
  private settings: SoundSettings;
  private lastTriggered: Map<string, number> = new Map();
  private previewTimeout: any = null;
  private initialized: boolean = false;

  private listeners: Set<(settings: SoundSettings) => void> = new Set();

  constructor() {
    this.settings = this.loadSoundSettings();
    if (typeof window !== 'undefined') {
      const initAudioOnUserInteraction = () => {
        this.initializeAudio();
        window.removeEventListener('click', initAudioOnUserInteraction);
        window.removeEventListener('keydown', initAudioOnUserInteraction);
      };
      window.addEventListener('click', initAudioOnUserInteraction, { once: true });
      window.addEventListener('keydown', initAudioOnUserInteraction, { once: true });
    }
  }

  public subscribe(cb: (settings: SoundSettings) => void): () => void {
    this.listeners.add(cb);
    return () => this.listeners.delete(cb);
  }

  private notify(): void {
    this.listeners.forEach((cb) => {
      try {
        cb(this.settings);
      } catch {
        // ignore subscriber errors
      }
    });
  }

  public initializeAudio(): void {
    if (this.initialized) return;
    this.initialized = true;
    soundSynthesizer.resume();
  }

  public loadSoundSettings(): SoundSettings {
    if (typeof window === 'undefined') return cloneDefaultSettings();
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return cloneDefaultSettings();
      const parsed = JSON.parse(stored);
      // Merge in any newly added default events and settings
      return {
        ...DEFAULT_SOUND_SETTINGS,
        ...parsed,
        events: {
          ...DEFAULT_SOUND_SETTINGS.events,
          ...(parsed.events || {}),
        },
      };
    } catch {
      return cloneDefaultSettings();
    }
  }

  public saveSoundSettings(newSettings?: Partial<SoundSettings>): boolean {
    if (typeof window === 'undefined') return false;
    try {
      if (newSettings) {
        this.settings = { ...this.settings, ...newSettings };
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.settings));
      this.notify();
      return true;
    } catch {
      return false;
    }
  }

  public clearCooldowns(): void {
    this.lastTriggered.clear();
  }

  public resetSoundSettings(): SoundSettings {
    this.clearCooldowns();
    this.settings = cloneDefaultSettings();
    this.saveSoundSettings();
    return this.settings;
  }

  public getSettings(): SoundSettings {
    return this.settings;
  }

  public setMasterEnabled(enabled: boolean): void {
    this.settings.masterEnabled = enabled;
    this.saveSoundSettings();
  }

  public setFraudAlertsEnabled(enabled: boolean): void {
    this.settings.fraudAlertsEnabled = enabled;
    this.saveSoundSettings();
  }

  public setMasterVolume(vol: number): void {
    this.settings.masterVolume = Math.max(0, Math.min(1, vol));
    this.saveSoundSettings();
  }

  public setAlertVolume(vol: number): void {
    this.settings.alertVolume = Math.max(0, Math.min(1, vol));
    this.saveSoundSettings();
  }

  public setMuted(muted: boolean): void {
    this.settings.muted = muted;
    this.saveSoundSettings();
  }

  public setQuietMode(quiet: boolean): void {
    this.settings.quietMode = quiet;
    this.saveSoundSettings();
  }

  public setQuietHours(enabled: boolean, start?: string, end?: string): void {
    this.settings.quietHoursEnabled = enabled;
    if (start) this.settings.quietHoursStart = start;
    if (end) this.settings.quietHoursEnd = end;
    this.saveSoundSettings();
  }

  public setSoundTheme(theme: SoundTheme): void {
    this.settings.soundTheme = theme;
    this.saveSoundSettings();
  }

  public setDefaultCooldown(ms: number): void {
    this.settings.defaultCooldownMs = Math.max(100, Math.min(10000, ms));
    this.saveSoundSettings();
  }

  public setEventConfig(eventId: string, config: Partial<SoundEventConfig>): void {
    if (!this.settings.events[eventId]) return;
    this.settings.events[eventId] = {
      ...this.settings.events[eventId],
      ...config,
    };
    this.saveSoundSettings();
  }

  private isQuietHours(): boolean {
    if (!this.settings.quietHoursEnabled) return false;
    const now = new Date();
    const currentMins = now.getHours() * 60 + now.getMinutes();

    const [startH, startM] = (this.settings.quietHoursStart || '22:00').split(':').map(Number);
    const [endH, endM] = (this.settings.quietHoursEnd || '07:00').split(':').map(Number);
    const startMins = (startH || 0) * 60 + (startM || 0);
    const endMins = (endH || 0) * 60 + (endM || 0);

    if (startMins <= endMins) {
      return currentMins >= startMins && currentMins < endMins;
    } else {
      // Wraps around midnight (e.g. 22:00 -> 07:00)
      return currentMins >= startMins || currentMins < endMins;
    }
  }

  public playEvent(eventId: string, _options?: PlayEventOptions): void {
    if (!this.settings.masterEnabled || this.settings.muted) return;

    const event = this.settings.events[eventId] || DEFAULT_SOUND_EVENTS[eventId];
    if (!event || !event.enabled) return;

    const isFraudAlarm = ['medium_risk', 'high_risk', 'critical', 'block'].includes(event.soundCategory);
    if (isFraudAlarm && !this.settings.fraudAlertsEnabled && event.priority !== 'CRITICAL') {
      return;
    }

    // Check Quiet Mode: only critical sounds play
    if (this.settings.quietMode && event.priority !== 'CRITICAL') {
      return;
    }

    // Check Quiet Hours:
    if (event.quietHoursMuted && this.isQuietHours() && event.priority !== 'CRITICAL') {
      return;
    }

    // Cooldown check for repetitive triggers
    const now = Date.now();
    const lastTime = this.lastTriggered.get(eventId) || 0;
    const cooldown = event.cooldownMs ?? this.settings.defaultCooldownMs ?? 1000;
    if (now - lastTime < cooldown) {
      return;
    }
    this.lastTriggered.set(eventId, now);

    // Calculate effective volume
    const isAlert = ['high_risk', 'critical', 'block', 'error'].includes(event.soundCategory);
    const volumeMultiplier = isAlert ? this.settings.alertVolume : 1.0;
    const effectiveVolume = this.settings.masterVolume * event.volume * volumeMultiplier;

    soundSynthesizer.play(event.soundCategory, this.settings.soundTheme, effectiveVolume);
  }

  /**
   * High-level intelligent context-aware mapper based on real ML risk decisions
   */
  public playDecisionSound(domain: string, result: {
    prediction?: string;
    risk_level?: string;
    recommended_action?: string;
    fraud_probability?: number;
  }): void {
    let normDomain = (domain || 'paysim').toLowerCase();
    if (normDomain === 'mobile_money') normDomain = 'paysim';
    if (normDomain === 'credit_card') normDomain = 'card';
    if (normDomain === 'url_phishing') normDomain = 'url';
    const risk = (result.risk_level || 'LOW').toUpperCase();
    const action = (result.recommended_action || 'APPROVE').toUpperCase();

    // 1. Critical priority check:
    if (risk === 'CRITICAL') {
      const eventKey = `${normDomain}.critical_risk`;
      if (this.settings.events[eventKey]) {
        this.playEvent(eventKey);
        return;
      }
    }

    // 2. Block action check:
    if (action === 'BLOCK') {
      const eventKey = `${normDomain}.block`;
      if (this.settings.events[eventKey]) {
        this.playEvent(eventKey);
        return;
      }
    }

    // 3. High risk check:
    if (risk === 'HIGH') {
      const eventKey = `${normDomain}.high_risk`;
      if (this.settings.events[eventKey]) {
        this.playEvent(eventKey);
        return;
      }
    }

    // 4. Verification check:
    if (action === 'VERIFY' || risk === 'MEDIUM') {
      const verifyKey = `${normDomain}.verify`;
      const mediumKey = `${normDomain}.medium_risk`;
      if (this.settings.events[verifyKey]) {
        this.playEvent(verifyKey);
        return;
      }
      if (this.settings.events[mediumKey]) {
        this.playEvent(mediumKey);
        return;
      }
    }

    // 5. Nominal / Low risk approve
    const lowKey = `${normDomain}.low_risk`;
    if (this.settings.events[lowKey]) {
      this.playEvent(lowKey);
    }
  }

  public previewSound(category: SoundCategory): void {
    this.stopPreview();
    soundSynthesizer.resume();
    const effectiveVolume = this.settings.masterVolume;
    soundSynthesizer.play(category, this.settings.soundTheme, effectiveVolume);
  }

  public stopPreview(): void {
    if (this.previewTimeout) {
      clearTimeout(this.previewTimeout);
      this.previewTimeout = null;
    }
  }

  public async testAllSounds(onProgress?: (category: SoundCategory, index: number, total: number) => void): Promise<void> {
    const categories: SoundCategory[] = [
      'ui',
      'processing',
      'complete',
      'approve',
      'verify',
      'high_risk',
      'block',
      'critical',
      'error',
      'drift',
      'case',
    ];
    this.initializeAudio();
    for (let i = 0; i < categories.length; i++) {
      const cat = categories[i];
      if (onProgress) onProgress(cat, i + 1, categories.length);
      this.previewSound(cat);
      await new Promise((r) => setTimeout(r, 480));
    }
  }

  public stopAllSounds(): void {
    this.stopPreview();
  }
}

export const soundManager = new SoundManager();
