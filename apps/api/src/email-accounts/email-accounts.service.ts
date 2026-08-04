import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { createTransport } from 'nodemailer';
import { decrypt, encrypt } from '../common/crypto.util';
import { PrismaService } from '../prisma.service';
import { EmailAccountInput, normalizeEmailAccountInput } from './email-account-input';

const PUBLIC_FIELDS = {
  id: true,
  name: true,
  fromName: true,
  fromEmail: true,
  smtpHost: true,
  smtpPort: true,
  smtpSecure: true,
  smtpUser: true,
  dailyLimit: true,
  limitResetTimezone: true,
  delayMode: true,
  delayFixedSeconds: true,
  delayMinSeconds: true,
  delayMaxSeconds: true,
  createdAt: true,
  updatedAt: true,
} as const;

@Injectable()
export class EmailAccountsService {
  constructor(private readonly prisma: PrismaService) {}

  async create(input: EmailAccountInput) {
    const normalized = normalizeEmailAccountInput(input, { requirePassword: true });
    return this.prisma.emailAccount.create({
      data: {
        name: normalized.name,
        fromName: normalized.fromName,
        fromEmail: normalized.fromEmail,
        smtpHost: normalized.smtpHost,
        smtpPort: normalized.smtpPort,
        smtpSecure: normalized.smtpSecure,
        smtpUser: normalized.smtpUser,
        smtpPasswordEncrypted: encrypt(normalized.smtpPassword),
        dailyLimit: normalized.dailyLimit,
        limitResetTimezone: normalized.limitResetTimezone,
        delayMode: normalized.delayMode,
        delayFixedSeconds: normalized.delayFixedSeconds,
        delayMinSeconds: normalized.delayMinSeconds,
        delayMaxSeconds: normalized.delayMaxSeconds,
      },
      select: PUBLIC_FIELDS,
    });
  }

  findAll() {
    return this.prisma.emailAccount.findMany({
      orderBy: { createdAt: 'desc' },
      select: PUBLIC_FIELDS,
    });
  }

  async findOne(id: number) {
    const account = await this.prisma.emailAccount.findUnique({ where: { id }, select: PUBLIC_FIELDS });
    if (!account) {
      throw new NotFoundException('Conta de e-mail não encontrada.');
    }
    return account;
  }

  async update(id: number, input: EmailAccountInput) {
    const existing = await this.prisma.emailAccount.findUnique({ where: { id } });
    if (!existing) {
      throw new NotFoundException('Conta de e-mail não encontrada.');
    }
    const normalized = normalizeEmailAccountInput(input, { requirePassword: false });
    return this.prisma.emailAccount.update({
      where: { id },
      data: {
        name: normalized.name,
        fromName: normalized.fromName,
        fromEmail: normalized.fromEmail,
        smtpHost: normalized.smtpHost,
        smtpPort: normalized.smtpPort,
        smtpSecure: normalized.smtpSecure,
        smtpUser: normalized.smtpUser,
        ...(normalized.smtpPassword ? { smtpPasswordEncrypted: encrypt(normalized.smtpPassword) } : {}),
        dailyLimit: normalized.dailyLimit,
        limitResetTimezone: normalized.limitResetTimezone,
        delayMode: normalized.delayMode,
        delayFixedSeconds: normalized.delayFixedSeconds,
        delayMinSeconds: normalized.delayMinSeconds,
        delayMaxSeconds: normalized.delayMaxSeconds,
      },
      select: PUBLIC_FIELDS,
    });
  }

  async remove(id: number) {
    const existing = await this.prisma.emailAccount.findUnique({ where: { id } });
    if (!existing) {
      throw new NotFoundException('Conta de e-mail não encontrada.');
    }
    await this.prisma.emailAccount.delete({ where: { id } });
  }

  async testConnection(id: number): Promise<{ ok: boolean; message: string }> {
    const account = await this.prisma.emailAccount.findUnique({ where: { id } });
    if (!account) {
      throw new NotFoundException('Conta de e-mail não encontrada.');
    }

    let password: string;
    try {
      password = decrypt(account.smtpPasswordEncrypted);
    } catch {
      throw new BadRequestException('Não foi possível descriptografar a senha salva.');
    }

    const transporter = createTransport({
      host: account.smtpHost,
      port: account.smtpPort,
      secure: account.smtpSecure,
      auth: { user: account.smtpUser, pass: password },
    });

    try {
      await transporter.verify();
      return { ok: true, message: 'Conexão SMTP validada com sucesso.' };
    } catch (err) {
      return { ok: false, message: err instanceof Error ? err.message : 'Falha ao conectar.' };
    }
  }
}
