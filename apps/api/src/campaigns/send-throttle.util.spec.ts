import {
  isDailyLimitReached,
  isDelayElapsed,
  parseUtcOffsetMinutes,
  resolveDelaySeconds,
  startOfResetWindow,
} from './send-throttle.util';

describe('resolveDelaySeconds', () => {
  it('returns the fixed delay in fixed mode', () => {
    const result = resolveDelaySeconds({
      delayMode: 'fixed',
      delayFixedSeconds: 307,
      delayMinSeconds: null,
      delayMaxSeconds: null,
    });
    expect(result).toBe(307);
  });

  it('returns a value within [min, max] in random mode', () => {
    const config = { delayMode: 'random', delayFixedSeconds: null, delayMinSeconds: 300, delayMaxSeconds: 420 };
    for (const roll of [0, 0.5, 0.999]) {
      const result = resolveDelaySeconds(config, () => roll);
      expect(result).toBeGreaterThanOrEqual(300);
      expect(result).toBeLessThanOrEqual(420);
    }
  });

  it('is deterministic given a fixed random() implementation', () => {
    const config = { delayMode: 'random', delayFixedSeconds: null, delayMinSeconds: 300, delayMaxSeconds: 420 };
    expect(resolveDelaySeconds(config, () => 0)).toBe(300);
    expect(resolveDelaySeconds(config, () => 0.999999)).toBe(420);
  });

  it('falls back to min when max <= min', () => {
    const config = { delayMode: 'random', delayFixedSeconds: null, delayMinSeconds: 300, delayMaxSeconds: 300 };
    expect(resolveDelaySeconds(config, () => 0.9)).toBe(300);
  });
});

describe('isDelayElapsed', () => {
  it('is always eligible when there is no previous send', () => {
    expect(isDelayElapsed(null, 300, new Date())).toBe(true);
  });

  it('is false when not enough time has passed', () => {
    const now = new Date('2026-01-01T00:05:00Z');
    const lastSentAt = new Date('2026-01-01T00:00:00Z');
    expect(isDelayElapsed(lastSentAt, 400, now)).toBe(false);
  });

  it('is true once the delay has fully elapsed', () => {
    const now = new Date('2026-01-01T00:05:00Z');
    const lastSentAt = new Date('2026-01-01T00:00:00Z');
    expect(isDelayElapsed(lastSentAt, 300, now)).toBe(true);
  });
});

describe('isDailyLimitReached', () => {
  it('is false below the limit', () => {
    expect(isDailyLimitReached(50, 100)).toBe(false);
  });

  it('is true at or above the limit', () => {
    expect(isDailyLimitReached(100, 100)).toBe(true);
    expect(isDailyLimitReached(150, 100)).toBe(true);
  });
});

describe('parseUtcOffsetMinutes', () => {
  it('treats "UTC" as 0', () => {
    expect(parseUtcOffsetMinutes('UTC')).toBe(0);
  });

  it('parses negative offsets like Brazil', () => {
    expect(parseUtcOffsetMinutes('UTC-03:00')).toBe(-180);
  });

  it('parses positive offsets without minutes', () => {
    expect(parseUtcOffsetMinutes('UTC+05')).toBe(300);
  });

  it('falls back to 0 for unrecognized input', () => {
    expect(parseUtcOffsetMinutes('America/Sao_Paulo')).toBe(0);
  });
});

describe('startOfResetWindow', () => {
  it('returns UTC midnight for the UTC timezone', () => {
    const now = new Date('2026-03-15T14:30:00Z');
    const start = startOfResetWindow(now, 'UTC');
    expect(start.toISOString()).toBe('2026-03-15T00:00:00.000Z');
  });

  it('shifts the window start for a negative offset (Brazil)', () => {
    // 2026-03-15T02:00:00Z is 2026-03-14T23:00:00 in UTC-03:00, still the previous local day.
    const now = new Date('2026-03-15T02:00:00Z');
    const start = startOfResetWindow(now, 'UTC-03:00');
    expect(start.toISOString()).toBe('2026-03-14T03:00:00.000Z');
  });
});
