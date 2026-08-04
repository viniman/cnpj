import { Module } from '@nestjs/common';
import { PrismaService } from '../prisma.service';
import { EmailAccountsController } from './email-accounts.controller';
import { EmailAccountsService } from './email-accounts.service';

@Module({
  controllers: [EmailAccountsController],
  providers: [EmailAccountsService, PrismaService],
})
export class EmailAccountsModule {}
