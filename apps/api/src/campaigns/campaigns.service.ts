import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma.service';

export interface CreateCampaignInput {
  name?: string;
  listId?: number;
  emailAccountId?: number;
  subject?: string;
  bodyHtml?: string;
}

const RECIPIENT_STATUSES = ['pending', 'sent', 'failed', 'skipped_no_email', 'skipped_suppressed'] as const;

@Injectable()
export class CampaignsService {
  constructor(private readonly prisma: PrismaService) {}

  async create(input: CreateCampaignInput) {
    const name = input.name?.trim();
    const subject = input.subject?.trim();
    const bodyHtml = input.bodyHtml?.trim();
    if (!name) throw new BadRequestException('Informe um nome para a campanha.');
    if (!input.listId) throw new BadRequestException('Selecione uma lista.');
    if (!input.emailAccountId) throw new BadRequestException('Selecione uma conta de e-mail.');
    if (!subject) throw new BadRequestException('Informe o assunto do e-mail.');
    if (!bodyHtml) throw new BadRequestException('Informe o corpo do e-mail.');

    const list = await this.prisma.list.findUnique({
      where: { id: input.listId },
      include: { companies: true },
    });
    if (!list) throw new NotFoundException('Lista não encontrada.');
    if (list.companies.length === 0) {
      throw new BadRequestException('Essa lista não tem nenhuma empresa salva.');
    }

    const emailAccount = await this.prisma.emailAccount.findUnique({ where: { id: input.emailAccountId } });
    if (!emailAccount) throw new NotFoundException('Conta de e-mail não encontrada.');

    return this.prisma.campaign.create({
      data: {
        name,
        listId: input.listId,
        emailAccountId: input.emailAccountId,
        subject,
        bodyHtml,
        recipients: {
          create: list.companies.map((company) => ({
            listCompanyId: company.id,
            razaoSocial: company.razaoSocial,
            nomeFantasia: company.nomeFantasia,
            municipioNome: company.municipioNome,
            email: company.correioEletronico,
            status: company.correioEletronico ? 'pending' : 'skipped_no_email',
          })),
        },
      },
      include: { _count: { select: { recipients: true } } },
    });
  }

  async findAll() {
    const campaigns = await this.prisma.campaign.findMany({
      orderBy: { createdAt: 'desc' },
      include: { list: { select: { name: true } }, emailAccount: { select: { name: true } } },
    });
    const withCounts = await Promise.all(campaigns.map((campaign) => this.attachCounts(campaign)));
    return withCounts;
  }

  async findOne(id: number) {
    const campaign = await this.prisma.campaign.findUnique({
      where: { id },
      include: {
        list: { select: { name: true } },
        emailAccount: { select: { name: true, fromEmail: true } },
        recipients: { orderBy: { id: 'asc' } },
      },
    });
    if (!campaign) throw new NotFoundException('Campanha não encontrada.');
    return { ...campaign, counts: await this.countsFor(id) };
  }

  async start(id: number) {
    const campaign = await this.prisma.campaign.findUnique({ where: { id } });
    if (!campaign) throw new NotFoundException('Campanha não encontrada.');
    if (campaign.status === 'completed') {
      throw new BadRequestException('Essa campanha já foi concluída.');
    }
    return this.prisma.campaign.update({ where: { id }, data: { status: 'active' } });
  }

  async pause(id: number) {
    const campaign = await this.prisma.campaign.findUnique({ where: { id } });
    if (!campaign) throw new NotFoundException('Campanha não encontrada.');
    return this.prisma.campaign.update({ where: { id }, data: { status: 'paused' } });
  }

  async remove(id: number) {
    const campaign = await this.prisma.campaign.findUnique({ where: { id } });
    if (!campaign) throw new NotFoundException('Campanha não encontrada.');
    await this.prisma.campaign.delete({ where: { id } });
  }

  private async countsFor(campaignId: number) {
    const grouped = await this.prisma.campaignRecipient.groupBy({
      by: ['status'],
      where: { campaignId },
      _count: true,
    });
    const counts: Record<string, number> = Object.fromEntries(RECIPIENT_STATUSES.map((s) => [s, 0]));
    for (const row of grouped) {
      counts[row.status] = row._count;
    }
    counts.total = Object.values(counts).reduce((sum, n) => sum + n, 0);
    return counts;
  }

  private async attachCounts<T extends { id: number }>(campaign: T) {
    return { ...campaign, counts: await this.countsFor(campaign.id) };
  }
}
