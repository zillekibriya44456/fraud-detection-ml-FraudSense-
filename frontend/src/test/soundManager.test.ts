import { describe, it, expect, beforeEach, vi } from 'vitest';
import { soundManager } from '../audio/soundManager';
import { soundSynthesizer } from '../audio/soundSynthesizer';
import { DEFAULT_SOUND_EVENTS } from '../audio/soundPresets';
import type { SoundPriority } from '../audio/soundTypes';

describe('FraudSense AI — Global Sound Effects & Fraud Alert System', () => {
  beforeEach(() => {
    localStorage.clear();
    soundManager.resetSoundSettings();
    soundManager.clearCooldowns();
    vi.restoreAllMocks();
  });

  describe('Event Registration & Sound Synthesis Mapping', () => {
    it('every configured default sound event has a valid soundCategory and priority', () => {
      const eventKeys = Object.keys(DEFAULT_SOUND_EVENTS);
      expect(eventKeys.length).toBeGreaterThan(30);

      const validPriorities: SoundPriority[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'NORMAL', 'LOW'];
      for (const key of eventKeys) {
        const evt = DEFAULT_SOUND_EVENTS[key];
        expect(evt.id).toBe(key);
        expect(evt.name).toBeTruthy();
        expect(evt.soundCategory).toBeTruthy();
        expect(validPriorities).toContain(evt.priority);
        expect(typeof evt.volume).toBe('number');
        expect(evt.volume).toBeGreaterThanOrEqual(0);
        expect(evt.volume).toBeLessThanOrEqual(1);
      }
    });

    it('plays synthesized sound through soundSynthesizer when event is triggered', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      soundManager.playEvent('upi.low_risk');
      expect(playSpy).toHaveBeenCalledWith('approve', 'CYBER_FINTECH', expect.any(Number));
    });
  });

  describe('Global Mute and Enable Controls', () => {
    it('suppresses audio when masterEnabled is false', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      soundManager.setMasterEnabled(false);
      soundManager.playEvent('dashboard.refresh');
      expect(playSpy).not.toHaveBeenCalled();
    });

    it('suppresses ordinary sounds when muted is true', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      soundManager.setMuted(true);
      soundManager.playEvent('dashboard.opened');
      expect(playSpy).not.toHaveBeenCalled();
    });

    it('allows separate disabling of fraud alarms while keeping other sounds', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      soundManager.setFraudAlertsEnabled(false);

      // Normal UI / confirmation sound still plays
      soundManager.playEvent('dashboard.refresh');
      expect(playSpy).toHaveBeenCalled();

      playSpy.mockClear();

      // High-risk fraud alarm is suppressed
      soundManager.playEvent('upi.high_risk');
      expect(playSpy).not.toHaveBeenCalled();
    });
  });

  describe('Context-Aware ML Decision Mapping', () => {
    it('maps CRITICAL risk level to critical_risk event', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      soundManager.playDecisionSound('upi', {
        risk_level: 'CRITICAL',
        recommended_action: 'BLOCK',
        fraud_probability: 0.98,
      });
      expect(playSpy).toHaveBeenCalledWith('critical', 'CYBER_FINTECH', expect.any(Number));
    });

    it('maps BLOCK action to block event', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      soundManager.playDecisionSound('card', {
        risk_level: 'HIGH',
        recommended_action: 'BLOCK',
        fraud_probability: 0.82,
      });
      expect(playSpy).toHaveBeenCalledWith('block', 'CYBER_FINTECH', expect.any(Number));
    });

    it('maps VERIFY action or MEDIUM risk to caution tone', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      soundManager.playDecisionSound('bank', {
        risk_level: 'MEDIUM',
        recommended_action: 'VERIFY',
        fraud_probability: 0.45,
      });
      expect(playSpy).toHaveBeenCalledWith('verify', 'CYBER_FINTECH', expect.any(Number));
    });

    it('maps LOW risk / APPROVE to gentle confirmation chord', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      soundManager.playDecisionSound('paysim', {
        risk_level: 'LOW',
        recommended_action: 'APPROVE',
        fraud_probability: 0.05,
      });
      expect(playSpy).toHaveBeenCalledWith('approve', 'CYBER_FINTECH', expect.any(Number));
    });

    it('handles domain aliases correctly (credit_card -> card, mobile_money -> paysim, url_phishing -> url)', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      soundManager.playDecisionSound('credit_card', {
        risk_level: 'CRITICAL',
        recommended_action: 'BLOCK',
      });
      expect(playSpy).toHaveBeenCalledWith('critical', 'CYBER_FINTECH', expect.any(Number));

      playSpy.mockClear();
      soundManager.playDecisionSound('url_phishing', {
        risk_level: 'HIGH',
        recommended_action: 'BLOCK',
      });
      expect(playSpy).toHaveBeenCalledWith('block', 'CYBER_FINTECH', expect.any(Number));
    });
  });

  describe('Deduplication & Cooldown Management', () => {
    it('prevents rapid duplicate triggers within cooldown window', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      soundManager.playEvent('dashboard.refresh');
      expect(playSpy).toHaveBeenCalledTimes(1);

      // Immediate second call should be ignored by cooldown
      soundManager.playEvent('dashboard.refresh');
      expect(playSpy).toHaveBeenCalledTimes(1);
    });

    it('allows event to trigger again after cooldown expires', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      const now = Date.now();
      vi.spyOn(Date, 'now').mockReturnValue(now);

      soundManager.playEvent('dashboard.refresh');
      expect(playSpy).toHaveBeenCalledTimes(1);

      // Advance time past 2500ms
      vi.spyOn(Date, 'now').mockReturnValue(now + 3000);
      soundManager.playEvent('dashboard.refresh');
      expect(playSpy).toHaveBeenCalledTimes(2);
    });
  });

  describe('Quiet Mode & Priority Safeguard', () => {
    it('in Quiet Mode, only CRITICAL alerts are permitted', () => {
      const playSpy = vi.spyOn(soundSynthesizer, 'play').mockImplementation(() => {});
      soundManager.setQuietMode(true);

      // Non-critical is suppressed
      soundManager.playEvent('upi.low_risk');
      soundManager.playEvent('upi.medium_risk');
      soundManager.playEvent('dashboard.opened');
      expect(playSpy).not.toHaveBeenCalled();

      // Critical attack alarm plays even in quiet mode
      soundManager.playEvent('upi.critical_risk');
      expect(playSpy).toHaveBeenCalledWith('critical', 'CYBER_FINTECH', expect.any(Number));
    });
  });

  describe('Settings Persistence & Subscription', () => {
    it('persists settings to localStorage and notifies subscribers', () => {
      let notified = false;
      const unsub = soundManager.subscribe((s) => {
        if (s.masterVolume === 0.42) notified = true;
      });

      soundManager.setMasterVolume(0.42);
      expect(notified).toBe(true);

      // Verify localStorage was updated
      const raw = localStorage.getItem('fraudsense_sound_settings_v1');
      expect(raw).toBeTruthy();
      const parsed = JSON.parse(raw!);
      expect(parsed.masterVolume).toBe(0.42);

      unsub();
    });

    it('resets settings to defaults upon request', () => {
      soundManager.setMasterVolume(0.1);
      soundManager.setQuietMode(true);
      expect(soundManager.getSettings().masterVolume).toBe(0.1);
      expect(soundManager.getSettings().quietMode).toBe(true);

      soundManager.resetSoundSettings();
      expect(soundManager.getSettings().masterVolume).toBe(0.75);
      expect(soundManager.getSettings().quietMode).toBe(false);
    });
  });
});
