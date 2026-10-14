/**
 * FraudSense AI — Intelligent Audio & Alarm System Types
 */

export type SoundPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'NORMAL' | 'LOW';

export type SoundTheme = 'CYBER_FINTECH' | 'MINIMAL_DIGITAL' | 'TACTICAL_ALARM';

export type SoundCategory =
  | 'ui'
  | 'processing'
  | 'complete'
  | 'low_risk'
  | 'medium_risk'
  | 'high_risk'
  | 'critical'
  | 'approve'
  | 'verify'
  | 'block'
  | 'error'
  | 'drift'
  | 'case';

export interface SoundEventConfig {
  id: string;                      // Unique event key, e.g. 'transaction.submitted'
  section: string;                 // e.g. 'Transaction Detection'
  subsection: string;              // e.g. 'PaySim / Mobile Money'
  name: string;                    // Human readable name, e.g. 'PaySim Block Decision'
  soundCategory: SoundCategory;    // Mapped synthesized audio tone
  volume: number;                  // Event volume multiplier 0.0 - 1.0
  enabled: boolean;                // Whether this event plays audio
  priority: SoundPriority;         // Event priority
  cooldownMs: number;              // Min delay between duplicate event triggers (ms)
  quietHoursMuted: boolean;        // Whether muted during quiet hours
}

export interface SoundSettings {
  masterEnabled: boolean;          // Master audio switch
  fraudAlertsEnabled: boolean;     // Separate switch for fraud/alarm alerts
  masterVolume: number;            // 0.0 - 1.0 (default 0.75)
  alertVolume: number;             // Volume multiplier for alert/alarm tones (0.0 - 1.0)
  muted: boolean;                  // Global mute
  quietMode: boolean;              // Force mute all except critical alerts
  quietHoursEnabled: boolean;      // Enable scheduling
  quietHoursStart: string;         // '22:00'
  quietHoursEnd: string;           // '07:00'
  defaultCooldownMs: number;       // Default cooldown between duplicate alerts
  soundTheme: SoundTheme;          // Audio sound synthesis profile
  events: Record<string, SoundEventConfig>;
}

export interface PlayEventOptions {
  domain?: string;
  riskLevel?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommendedAction?: 'APPROVE' | 'VERIFY' | 'BLOCK';
  error?: boolean;
  force?: boolean;
}
