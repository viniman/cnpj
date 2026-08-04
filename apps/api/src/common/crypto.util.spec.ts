import { decrypt, encrypt } from './crypto.util';

describe('crypto.util', () => {
  const originalEnv = process.env.EMAIL_CREDENTIALS_KEY;

  beforeAll(() => {
    process.env.EMAIL_CREDENTIALS_KEY = 'test-key-only-for-unit-tests';
  });

  afterAll(() => {
    process.env.EMAIL_CREDENTIALS_KEY = originalEnv;
  });

  it('decrypts back to the original plain text', () => {
    const plain = 'super-secret-smtp-password';
    const encrypted = encrypt(plain);
    expect(decrypt(encrypted)).toBe(plain);
  });

  it('produces a different ciphertext each time (random IV)', () => {
    const plain = 'same-password';
    const a = encrypt(plain);
    const b = encrypt(plain);
    expect(a).not.toBe(b);
    expect(decrypt(a)).toBe(plain);
    expect(decrypt(b)).toBe(plain);
  });

  it('never contains the plain text as a substring of the ciphertext', () => {
    const plain = 'plaintext-marker-xyz';
    const encrypted = encrypt(plain);
    expect(encrypted).not.toContain(plain);
  });

  it('throws when the ciphertext was tampered with', () => {
    const encrypted = encrypt('anything');
    const tampered = encrypted.slice(0, -4) + 'AAAA';
    expect(() => decrypt(tampered)).toThrow();
  });

  it('throws when EMAIL_CREDENTIALS_KEY is missing', () => {
    delete process.env.EMAIL_CREDENTIALS_KEY;
    expect(() => encrypt('x')).toThrow('EMAIL_CREDENTIALS_KEY');
    process.env.EMAIL_CREDENTIALS_KEY = 'test-key-only-for-unit-tests';
  });
});
