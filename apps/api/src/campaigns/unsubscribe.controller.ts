import { BadRequestException, Controller, Get, Query } from '@nestjs/common';
import { PrismaService } from '../prisma.service';
import { verifyUnsubscribeToken } from './unsubscribe-token.util';

@Controller('unsubscribe')
export class UnsubscribeController {
  constructor(private readonly prisma: PrismaService) {}

  @Get()
  async unsubscribe(@Query('email') email?: string, @Query('token') token?: string) {
    if (!email || !token || !verifyUnsubscribeToken(email, token)) {
      throw new BadRequestException('Link de descadastro inválido.');
    }
    const normalized = email.toLowerCase().trim();
    await this.prisma.suppressionEntry.upsert({
      where: { email: normalized },
      create: { email: normalized, reason: 'unsubscribed' },
      update: {},
    });
    return { ok: true, message: 'Você foi removido da nossa lista de envios.' };
  }
}
