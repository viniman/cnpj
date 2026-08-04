import { normalizeEmailAccountInput } from './email-account-input';

const BASE_INPUT = {
  name: 'Preparatório OLITEF',
  fromName: 'Preparatório OLITEF',
  fromEmail: 'preparatorio@realgrana.com.br',
  smtpHost: 'email-smtp.us-east-1.amazonaws.com',
  smtpUser: 'AKIAEXAMPLE',
  smtpPassword: 'super-secret',
  delayMode: 'random',
  delayMinSeconds: 307,
  delayMaxSeconds: 419,
};

describe('normalizeEmailAccountInput', () => {
  it('applies sensible defaults for port, security, limit and timezone', () => {
    const result = normalizeEmailAccountInput(BASE_INPUT);
    expect(result.smtpPort).toBe(587);
    expect(result.smtpSecure).toBe(false);
    expect(result.dailyLimit).toBe(100);
    expect(result.limitResetTimezone).toBe('UTC');
  });

  it('defaults smtpSecure to true when port is 465', () => {
    const result = normalizeEmailAccountInput({ ...BASE_INPUT, smtpPort: 465 });
    expect(result.smtpSecure).toBe(true);
  });

  it('requires required text fields', () => {
    expect(() => normalizeEmailAccountInput({ ...BASE_INPUT, name: '' })).toThrow('nome');
    expect(() => normalizeEmailAccountInput({ ...BASE_INPUT, smtpHost: '' })).toThrow('host SMTP');
  });

  it('rejects an invalid from email', () => {
    expect(() => normalizeEmailAccountInput({ ...BASE_INPUT, fromEmail: 'not-an-email' })).toThrow(
      'inválido',
    );
  });

  it('requires the password on create but allows omitting it on update', () => {
    const { smtpPassword, ...withoutPassword } = BASE_INPUT;
    expect(() => normalizeEmailAccountInput(withoutPassword)).toThrow('senha SMTP');
    const result = normalizeEmailAccountInput(withoutPassword, { requirePassword: false });
    expect(result.smtpPassword).toBe('');
  });

  it('rejects a daily limit above the maximum', () => {
    expect(() => normalizeEmailAccountInput({ ...BASE_INPUT, dailyLimit: 999999 })).toThrow(
      'limite diário',
    );
  });

  it('validates fixed delay mode requires delayFixedSeconds', () => {
    expect(() =>
      normalizeEmailAccountInput({ ...BASE_INPUT, delayMode: 'fixed', delayMinSeconds: undefined, delayMaxSeconds: undefined }),
    ).toThrow('atraso fixo');
  });

  it('accepts fixed delay mode with delayFixedSeconds', () => {
    const result = normalizeEmailAccountInput({
      ...BASE_INPUT,
      delayMode: 'fixed',
      delayFixedSeconds: 300,
      delayMinSeconds: undefined,
      delayMaxSeconds: undefined,
    });
    expect(result.delayMode).toBe('fixed');
    expect(result.delayFixedSeconds).toBe(300);
    expect(result.delayMinSeconds).toBeNull();
  });

  it('rejects random delay mode when min is greater than max', () => {
    expect(() =>
      normalizeEmailAccountInput({ ...BASE_INPUT, delayMinSeconds: 500, delayMaxSeconds: 100 }),
    ).toThrow('mínimo');
  });

  it('rejects an unknown delay mode', () => {
    expect(() => normalizeEmailAccountInput({ ...BASE_INPUT, delayMode: 'weird' })).toThrow(
      '"fixed" ou "random"',
    );
  });
});
