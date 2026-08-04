import { BadRequestException } from '@nestjs/common';

export interface EmailAccountInput {
  name?: string;
  fromName?: string;
  fromEmail?: string;
  smtpHost?: string;
  smtpPort?: number | string;
  smtpSecure?: boolean;
  smtpUser?: string;
  smtpPassword?: string;
  dailyLimit?: number | string;
  limitResetTimezone?: string;
  delayMode?: string;
  delayFixedSeconds?: number | string;
  delayMinSeconds?: number | string;
  delayMaxSeconds?: number | string;
}

export interface NormalizedEmailAccountInput {
  name: string;
  fromName: string;
  fromEmail: string;
  smtpHost: string;
  smtpPort: number;
  smtpSecure: boolean;
  smtpUser: string;
  smtpPassword: string;
  dailyLimit: number;
  limitResetTimezone: string;
  delayMode: 'fixed' | 'random';
  delayFixedSeconds: number | null;
  delayMinSeconds: number | null;
  delayMaxSeconds: number | null;
}

const MAX_DAILY_LIMIT = 5000;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function requireText(value: string | undefined, field: string): string {
  const trimmed = value?.trim();
  if (!trimmed) {
    throw new BadRequestException(`Informe ${field}.`);
  }
  return trimmed;
}

function toPositiveInt(value: number | string | undefined, field: string, fallback?: number): number {
  if (value === undefined || value === '') {
    if (fallback !== undefined) return fallback;
    throw new BadRequestException(`Informe ${field}.`);
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || !Number.isInteger(parsed) || parsed <= 0) {
    throw new BadRequestException(`${field} deve ser um número inteiro positivo.`);
  }
  return parsed;
}

/**
 * Pure validation/normalization for an EmailAccount create/update payload,
 * kept separate from Prisma/crypto calls so it can be unit tested without
 * a database or the encryption key.
 */
export function normalizeEmailAccountInput(
  input: EmailAccountInput,
  options: { requirePassword: boolean } = { requirePassword: true },
): NormalizedEmailAccountInput {
  const name = requireText(input.name, 'um nome para a conta');
  const fromName = requireText(input.fromName, 'o nome do remetente');
  const fromEmail = requireText(input.fromEmail, 'o e-mail do remetente');
  if (!EMAIL_PATTERN.test(fromEmail)) {
    throw new BadRequestException('E-mail do remetente inválido.');
  }
  const smtpHost = requireText(input.smtpHost, 'o host SMTP');
  const smtpUser = requireText(input.smtpUser, 'o usuário SMTP');

  const smtpPort = toPositiveInt(input.smtpPort, 'a porta SMTP', 587);
  const smtpSecure = input.smtpSecure ?? smtpPort === 465;

  let smtpPassword = '';
  if (options.requirePassword || input.smtpPassword) {
    smtpPassword = requireText(input.smtpPassword, 'a senha SMTP');
  }

  const dailyLimit = toPositiveInt(input.dailyLimit, 'o limite diário', 100);
  if (dailyLimit > MAX_DAILY_LIMIT) {
    throw new BadRequestException(`O limite diário não pode passar de ${MAX_DAILY_LIMIT}.`);
  }

  const limitResetTimezone = input.limitResetTimezone?.trim() || 'UTC';

  const delayMode = (input.delayMode?.trim() || 'random') as 'fixed' | 'random';
  if (delayMode !== 'fixed' && delayMode !== 'random') {
    throw new BadRequestException('Modo de atraso deve ser "fixed" ou "random".');
  }

  let delayFixedSeconds: number | null = null;
  let delayMinSeconds: number | null = null;
  let delayMaxSeconds: number | null = null;

  if (delayMode === 'fixed') {
    delayFixedSeconds = toPositiveInt(input.delayFixedSeconds, 'o atraso fixo em segundos');
  } else {
    delayMinSeconds = toPositiveInt(input.delayMinSeconds, 'o atraso mínimo em segundos');
    delayMaxSeconds = toPositiveInt(input.delayMaxSeconds, 'o atraso máximo em segundos');
    if (delayMinSeconds > delayMaxSeconds) {
      throw new BadRequestException('O atraso mínimo não pode ser maior que o máximo.');
    }
  }

  return {
    name,
    fromName,
    fromEmail,
    smtpHost,
    smtpPort,
    smtpSecure,
    smtpUser,
    smtpPassword,
    dailyLimit,
    limitResetTimezone,
    delayMode,
    delayFixedSeconds,
    delayMinSeconds,
    delayMaxSeconds,
  };
}
