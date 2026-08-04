export interface DelayConfig {
  delayMode: string;
  delayFixedSeconds: number | null;
  delayMinSeconds: number | null;
  delayMaxSeconds: number | null;
}

/**
 * Resolves the delay (in seconds) to wait before the next send for this
 * account. Random mode re-rolls every call, matching Snov.io's "atraso
 * aleatório entre e-mails" behaviour (ver ADR-056).
 */
export function resolveDelaySeconds(config: DelayConfig, random: () => number = Math.random): number {
  if (config.delayMode === 'fixed') {
    return config.delayFixedSeconds ?? 0;
  }
  const min = config.delayMinSeconds ?? 0;
  const max = config.delayMaxSeconds ?? min;
  if (max <= min) return min;
  return min + Math.floor(random() * (max - min + 1));
}

/**
 * True when enough time has passed since the account's last send. A
 * null lastSentAt means the account has never sent, so it's always
 * eligible.
 */
export function isDelayElapsed(lastSentAt: Date | null, delaySeconds: number, now: Date): boolean {
  if (!lastSentAt) return true;
  const elapsedMs = now.getTime() - lastSentAt.getTime();
  return elapsedMs >= delaySeconds * 1000;
}

/**
 * True when sentToday has already reached (or passed) the account's
 * daily limit.
 */
export function isDailyLimitReached(sentToday: number, dailyLimit: number): boolean {
  return sentToday >= dailyLimit;
}

const OFFSET_PATTERN = /^UTC([+-])(\d{1,2}):?(\d{2})?$/i;

/**
 * Parses a "UTC", "UTC-03:00" or "UTC+03" style string into an offset in
 * minutes east of UTC. Falls back to 0 (UTC) for anything unrecognized,
 * rather than pulling in a full IANA timezone library for what is, for
 * now, just a fixed-offset picker (matches the "UTC ±HH:MM" pattern used
 * by the account's limit-reset setting).
 */
export function parseUtcOffsetMinutes(timezone: string): number {
  const trimmed = timezone.trim().toUpperCase();
  if (trimmed === 'UTC' || trimmed === '') return 0;
  const match = OFFSET_PATTERN.exec(trimmed);
  if (!match) return 0;
  const sign = match[1] === '-' ? -1 : 1;
  const hours = Number(match[2]);
  const minutes = Number(match[3] ?? '0');
  return sign * (hours * 60 + minutes);
}

/**
 * Start of the current "day" for an account's limit-reset window, given
 * its configured timezone string (see parseUtcOffsetMinutes).
 */
export function startOfResetWindow(now: Date, timezone: string): Date {
  const offsetMinutes = parseUtcOffsetMinutes(timezone);
  const shifted = new Date(now.getTime() + offsetMinutes * 60 * 1000);
  const startShifted = new Date(
    Date.UTC(shifted.getUTCFullYear(), shifted.getUTCMonth(), shifted.getUTCDate()),
  );
  return new Date(startShifted.getTime() - offsetMinutes * 60 * 1000);
}
