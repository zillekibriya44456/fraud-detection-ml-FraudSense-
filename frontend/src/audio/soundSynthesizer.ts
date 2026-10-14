import type { SoundCategory, SoundTheme } from './soundTypes';

/**
 * Web Audio API synthesizer for FraudSense AI.
 * Creates clean, professional, non-intrusive cyber-fintech audio cues.
 */
export class SoundSynthesizer {
  private ctx: AudioContext | null = null;

  private getContext(): AudioContext | null {
    if (typeof window === 'undefined') return null;
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  public resume(): void {
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
  }

  public play(category: SoundCategory, theme: SoundTheme, volume: number): void {
    const ctx = this.getContext();
    if (!ctx) return;

    try {
      const now = ctx.currentTime;
      const masterGain = ctx.createGain();
      masterGain.gain.setValueAtTime(Math.max(0.01, Math.min(1.0, volume)), now);
      masterGain.connect(ctx.destination);

      switch (category) {
        case 'ui':
          this.playUi(ctx, masterGain, now, theme);
          break;
        case 'processing':
          this.playProcessing(ctx, masterGain, now, theme);
          break;
        case 'complete':
          this.playComplete(ctx, masterGain, now, theme);
          break;
        case 'approve':
        case 'low_risk':
          this.playApprove(ctx, masterGain, now, theme);
          break;
        case 'verify':
        case 'medium_risk':
          this.playVerify(ctx, masterGain, now, theme);
          break;
        case 'high_risk':
          this.playHighRisk(ctx, masterGain, now, theme);
          break;
        case 'block':
          this.playBlock(ctx, masterGain, now, theme);
          break;
        case 'critical':
          this.playCritical(ctx, masterGain, now, theme);
          break;
        case 'error':
          this.playError(ctx, masterGain, now, theme);
          break;
        case 'drift':
          this.playDrift(ctx, masterGain, now, theme);
          break;
        case 'case':
          this.playCase(ctx, masterGain, now, theme);
          break;
        default:
          this.playUi(ctx, masterGain, now, theme);
      }
    } catch {
      // Audio synthesis fallback (non-blocking)
    }
  }

  // 1. Soft UI digital click (35ms)
  private playUi(ctx: AudioContext, dest: GainNode, now: number, theme: SoundTheme) {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = theme === 'MINIMAL_DIGITAL' ? 'triangle' : 'sine';
    const baseFreq = theme === 'TACTICAL_ALARM' ? 1200 : 800;
    osc.frequency.setValueAtTime(baseFreq, now);
    osc.frequency.exponentialRampToValueAtTime(baseFreq * 0.5, now + 0.035);

    gain.gain.setValueAtTime(0.25, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.035);

    osc.connect(gain);
    gain.connect(dest);
    osc.start(now);
    osc.stop(now + 0.035);
  }

  // 2. Subtle two-tone electronic pulse (80ms)
  private playProcessing(ctx: AudioContext, dest: GainNode, now: number, _theme: SoundTheme) {
    [520, 650].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const t = now + idx * 0.04;

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(0.18, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.035);

      osc.connect(gain);
      gain.connect(dest);
      osc.start(t);
      osc.stop(t + 0.04);
    });
  }

  // 3. Clean ascending confirmation tone (140ms)
  private playComplete(ctx: AudioContext, dest: GainNode, now: number, _theme: SoundTheme) {
    [440, 660, 880].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const t = now + idx * 0.045;

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(0.22, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.06);

      osc.connect(gain);
      gain.connect(dest);
      osc.start(t);
      osc.stop(t + 0.065);
    });
  }

  // 4. Soft positive confirmation (C - E harmonic, 160ms)
  private playApprove(ctx: AudioContext, dest: GainNode, now: number, _theme: SoundTheme) {
    [523.25, 659.25].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const t = now + idx * 0.06;

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(0.28, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.12);

      osc.connect(gain);
      gain.connect(dest);
      osc.start(t);
      osc.stop(t + 0.13);
    });
  }

  // 5. Neutral attention tone (E - B, 180ms)
  private playVerify(ctx: AudioContext, dest: GainNode, now: number, _theme: SoundTheme) {
    [493.88, 587.33].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const t = now + idx * 0.08;

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(0.3, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.1);

      osc.connect(gain);
      gain.connect(dest);
      osc.start(t);
      osc.stop(t + 0.11);
    });
  }

  // 6. Distinctive alert with moderate urgency (220ms)
  private playHighRisk(ctx: AudioContext, dest: GainNode, now: number, theme: SoundTheme) {
    const freqs = theme === 'TACTICAL_ALARM' ? [700, 850, 700] : [620, 780, 920];
    freqs.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const t = now + idx * 0.07;

      osc.type = theme === 'MINIMAL_DIGITAL' ? 'sine' : 'sawtooth';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(0.24, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.075);

      osc.connect(gain);
      gain.connect(dest);
      osc.start(t);
      osc.stop(t + 0.08);
    });
  }

  // 7. Short, unmistakable low digital alert for BLOCK (150ms)
  private playBlock(ctx: AudioContext, dest: GainNode, now: number, _theme: SoundTheme) {
    [320, 240].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const t = now + idx * 0.07;

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq, t);
      osc.frequency.exponentialRampToValueAtTime(freq * 0.8, t + 0.08);

      gain.gain.setValueAtTime(0.35, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.085);

      osc.connect(gain);
      gain.connect(dest);
      osc.start(t);
      osc.stop(t + 0.09);
    });
  }

  // 8. Urgent but controlled critical alert (tri-burst, 320ms)
  private playCritical(ctx: AudioContext, dest: GainNode, now: number, theme: SoundTheme) {
    const baseFreqs = theme === 'TACTICAL_ALARM' ? [880, 1100, 880, 1100] : [750, 950, 1150];
    baseFreqs.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const t = now + idx * 0.075;

      osc.type = 'square';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(0.26, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.07);

      osc.connect(gain);
      gain.connect(dest);
      osc.start(t);
      osc.stop(t + 0.075);
    });
  }

  // 9. Short descending error tone (120ms)
  private playError(ctx: AudioContext, dest: GainNode, now: number, _theme: SoundTheme) {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(420, now);
    osc.frequency.exponentialRampToValueAtTime(180, now + 0.12);

    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

    osc.connect(gain);
    gain.connect(dest);
    osc.start(now);
    osc.stop(now + 0.13);
  }

  // 10. Model statistical drift warning (180ms)
  private playDrift(ctx: AudioContext, dest: GainNode, now: number, _theme: SoundTheme) {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(450, now);
    osc.frequency.linearRampToValueAtTime(680, now + 0.08);
    osc.frequency.linearRampToValueAtTime(520, now + 0.16);

    gain.gain.setValueAtTime(0.25, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.17);

    osc.connect(gain);
    gain.connect(dest);
    osc.start(now);
    osc.stop(now + 0.18);
  }

  // 11. New fraud case created alert (160ms)
  private playCase(ctx: AudioContext, dest: GainNode, now: number, _theme: SoundTheme) {
    [580, 870].forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const t = now + idx * 0.07;

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(0.3, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.08);

      osc.connect(gain);
      gain.connect(dest);
      osc.start(t);
      osc.stop(t + 0.09);
    });
  }
}

export const soundSynthesizer = new SoundSynthesizer();
