import { generateUnsubscribeToken, verifyUnsubscribeToken } from './unsubscribe-token.util';

describe('unsubscribe-token.util', () => {
  const originalEnv = process.env.EMAIL_CREDENTIALS_KEY;

  beforeAll(() => {
    process.env.EMAIL_CREDENTIALS_KEY = 'test-key-only-for-unit-tests';
  });

  afterAll(() => {
    process.env.EMAIL_CREDENTIALS_KEY = originalEnv;
  });

  it('generates a token that verifies for the same email', () => {
    const token = generateUnsubscribeToken('contato@empresa.com.br');
    expect(verifyUnsubscribeToken('contato@empresa.com.br', token)).toBe(true);
  });

  it('is case/whitespace insensitive for the email', () => {
    const token = generateUnsubscribeToken('Contato@Empresa.com.br');
    expect(verifyUnsubscribeToken('  contato@empresa.com.br  ', token)).toBe(true);
  });

  it('rejects a token generated for a different email', () => {
    const token = generateUnsubscribeToken('a@empresa.com.br');
    expect(verifyUnsubscribeToken('b@empresa.com.br', token)).toBe(false);
  });

  it('rejects a tampered token', () => {
    const token = generateUnsubscribeToken('contato@empresa.com.br');
    const tampered = token.slice(0, -2) + (token.slice(-2) === 'aa' ? 'bb' : 'aa');
    expect(verifyUnsubscribeToken('contato@empresa.com.br', tampered)).toBe(false);
  });

  it('rejects a token of the wrong length instead of throwing', () => {
    expect(verifyUnsubscribeToken('contato@empresa.com.br', 'short')).toBe(false);
  });
});
