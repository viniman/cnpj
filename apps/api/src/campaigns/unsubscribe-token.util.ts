import { createHmac, timingSafeEqual } from 'crypto';

function getSecret(): string {
  const secret = process.env.EMAIL_CREDENTIALS_KEY;
  if (!secret) {
    throw new Error('EMAIL_CREDENTIALS_KEY não configurada nas variáveis de ambiente.');
  }
  return secret;
}

/**
 * HMAC-SHA256 token for a recipient's unsubscribe link, so
 * GET /unsubscribe cannot be used to suppress an arbitrary address
 * without knowing a token derived from the shared server secret.
 */
export function generateUnsubscribeToken(email: string): string {
  return createHmac('sha256', getSecret()).update(email.toLowerCase().trim()).digest('hex');
}

export function verifyUnsubscribeToken(email: string, token: string): boolean {
  const expected = generateUnsubscribeToken(email);
  const expectedBuffer = Buffer.from(expected, 'hex');
  const providedBuffer = Buffer.from(token, 'hex');
  if (expectedBuffer.length !== providedBuffer.length) {
    return false;
  }
  return timingSafeEqual(expectedBuffer, providedBuffer);
}
