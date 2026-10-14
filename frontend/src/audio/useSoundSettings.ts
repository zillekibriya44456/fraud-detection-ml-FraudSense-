import { useState, useEffect } from 'react';
import { soundManager } from './soundManager';
import type { SoundSettings, SoundTheme, SoundEventConfig, SoundCategory } from './soundTypes';

export function useSoundSettings() {
  const [settings, setSettings] = useState<SoundSettings>(() => soundManager.getSettings());
  const [isTesting, setIsTesting] = useState(false);
  const [testProgress, setTestProgress] = useState<{ category: string; index: number; total: number } | null>(null);

  useEffect(() => {
    return soundManager.subscribe((updated) => {
      setSettings({ ...updated, events: { ...updated.events } });
    });
  }, []);

  const setMasterEnabled = (val: boolean) => soundManager.setMasterEnabled(val);
  const setFraudAlertsEnabled = (val: boolean) => soundManager.setFraudAlertsEnabled(val);
  const setMasterVolume = (val: number) => soundManager.setMasterVolume(val);
  const setAlertVolume = (val: number) => soundManager.setAlertVolume(val);
  const setMuted = (val: boolean) => soundManager.setMuted(val);
  const setQuietMode = (val: boolean) => soundManager.setQuietMode(val);
  const setQuietHours = (enabled: boolean, start?: string, end?: string) => soundManager.setQuietHours(enabled, start, end);
  const setSoundTheme = (theme: SoundTheme) => soundManager.setSoundTheme(theme);
  const setDefaultCooldown = (ms: number) => soundManager.setDefaultCooldown(ms);
  const setEventConfig = (eventId: string, config: Partial<SoundEventConfig>) => soundManager.setEventConfig(eventId, config);
  const previewSound = (cat: SoundCategory) => soundManager.previewSound(cat);
  const resetSoundSettings = () => soundManager.resetSoundSettings();

  const testAllSounds = async () => {
    if (isTesting) return;
    setIsTesting(true);
    try {
      await soundManager.testAllSounds((category, index, total) => {
        setTestProgress({ category, index, total });
      });
    } finally {
      setIsTesting(false);
      setTestProgress(null);
    }
  };

  return {
    settings,
    isTesting,
    testProgress,
    setMasterEnabled,
    setFraudAlertsEnabled,
    setMasterVolume,
    setAlertVolume,
    setMuted,
    setQuietMode,
    setQuietHours,
    setSoundTheme,
    setDefaultCooldown,
    setEventConfig,
    previewSound,
    resetSoundSettings,
    testAllSounds,
  };
}
