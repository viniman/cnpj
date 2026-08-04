import { Injectable, Logger } from '@nestjs/common';
import { Interval } from '@nestjs/schedule';
import { createTransport } from 'nodemailer';
import { decrypt } from '../common/crypto.util';
import { PrismaService } from '../prisma.service';
import { generateUnsubscribeToken } from './unsubscribe-token.util';
import { isDailyLimitReached, isDelayElapsed, resolveDelaySeconds, startOfResetWindow } from './send-throttle.util';
import { renderTemplate } from './template.util';

const TICK_INTERVAL_MS = 15_000;
const API_PUBLIC_URL = process.env.API_PUBLIC_URL || 'http://127.0.0.1:3001';

/**
 * Polling-based send worker. No Redis/BullMQ yet (see
 * docs/NEXT_ARCHITECTURE_LEDGER.md item 7); one @Interval tick handles
 * at most one send per active campaign, so the daily-limit/delay checks
 * stay correct without a queue. A campaign only sends after the user
 * explicitly starts it (status becomes "active") — never automatically
 * on creation (ver ADR-056 em docs/DECISIONS.md).
 */
@Injectable()
export class CampaignSenderService {
  private readonly logger = new Logger(CampaignSenderService.name);
  private ticking = false;

  constructor(private readonly prisma: PrismaService) {}

  @Interval(TICK_INTERVAL_MS)
  async tick() {
    if (this.ticking) return;
    this.ticking = true;
    try {
      const activeCampaigns = await this.prisma.campaign.findMany({
        where: { status: 'active' },
        include: { emailAccount: true },
      });
      for (const campaign of activeCampaigns) {
        await this.processCampaign(campaign);
      }
    } catch (err) {
      this.logger.error('Erro no tick do motor de envio', err instanceof Error ? err.stack : String(err));
    } finally {
      this.ticking = false;
    }
  }

  private async processCampaign(campaign: {
    id: number;
    subject: string;
    bodyHtml: string;
    emailAccount: {
      id: number;
      fromName: string;
      fromEmail: string;
      smtpHost: string;
      smtpPort: number;
      smtpSecure: boolean;
      smtpUser: string;
      smtpPasswordEncrypted: string;
      dailyLimit: number;
      limitResetTimezone: string;
      delayMode: string;
      delayFixedSeconds: number | null;
      delayMinSeconds: number | null;
      delayMaxSeconds: number | null;
      lastSentAt: Date | null;
    };
  }) {
    const account = campaign.emailAccount;
    const now = new Date();

    const windowStart = startOfResetWindow(now, account.limitResetTimezone);
    const sentToday = await this.prisma.campaignRecipient.count({
      where: {
        status: 'sent',
        sentAt: { gte: windowStart },
        campaign: { emailAccountId: account.id },
      },
    });
    if (isDailyLimitReached(sentToday, account.dailyLimit)) return;

    const delaySeconds = resolveDelaySeconds(account);
    if (!isDelayElapsed(account.lastSentAt, delaySeconds, now)) return;

    const recipient = await this.prisma.campaignRecipient.findFirst({
      where: { campaignId: campaign.id, status: 'pending' },
      orderBy: { id: 'asc' },
    });

    if (!recipient) {
      const stillPending = await this.prisma.campaignRecipient.count({
        where: { campaignId: campaign.id, status: 'pending' },
      });
      if (stillPending === 0) {
        await this.prisma.campaign.update({ where: { id: campaign.id }, data: { status: 'completed' } });
      }
      return;
    }

    if (recipient.email) {
      const suppressed = await this.prisma.suppressionEntry.findUnique({
        where: { email: recipient.email.toLowerCase() },
      });
      if (suppressed) {
        await this.prisma.campaignRecipient.update({
          where: { id: recipient.id },
          data: { status: 'skipped_suppressed' },
        });
        return;
      }
    }

    if (!recipient.email) {
      await this.prisma.campaignRecipient.update({
        where: { id: recipient.id },
        data: { status: 'skipped_no_email' },
      });
      return;
    }

    const templateVars = {
      razaoSocial: recipient.razaoSocial,
      nomeFantasia: recipient.nomeFantasia,
      municipioNome: recipient.municipioNome,
    };
    const subject = renderTemplate(campaign.subject, templateVars);
    const unsubscribeUrl = `${API_PUBLIC_URL}/unsubscribe?email=${encodeURIComponent(
      recipient.email,
    )}&token=${generateUnsubscribeToken(recipient.email)}`;
    const html = `${renderTemplate(campaign.bodyHtml, templateVars)}<p style="font-size:12px;color:#888;margin-top:24px;">Não quer mais receber estes e-mails? <a href="${unsubscribeUrl}">Cancelar inscrição</a>.</p>`;

    let password: string;
    try {
      password = decrypt(account.smtpPasswordEncrypted);
    } catch {
      await this.prisma.campaignRecipient.update({
        where: { id: recipient.id },
        data: { status: 'failed', errorMessage: 'Não foi possível descriptografar a senha da conta.' },
      });
      return;
    }

    const transporter = createTransport({
      host: account.smtpHost,
      port: account.smtpPort,
      secure: account.smtpSecure,
      auth: { user: account.smtpUser, pass: password },
    });

    try {
      await transporter.sendMail({
        from: `${account.fromName} <${account.fromEmail}>`,
        to: recipient.email,
        subject,
        html,
      });
      await this.prisma.$transaction([
        this.prisma.campaignRecipient.update({
          where: { id: recipient.id },
          data: { status: 'sent', sentAt: new Date() },
        }),
        this.prisma.emailAccount.update({ where: { id: account.id }, data: { lastSentAt: new Date() } }),
      ]);
    } catch (err) {
      await this.prisma.campaignRecipient.update({
        where: { id: recipient.id },
        data: { status: 'failed', errorMessage: err instanceof Error ? err.message : 'Falha ao enviar.' },
      });
    }
  }
}
