import { Module } from '@nestjs/common';
import { ScheduleModule } from '@nestjs/schedule';
import { PrismaService } from '../prisma.service';
import { CampaignSenderService } from './campaign-sender.service';
import { CampaignsController } from './campaigns.controller';
import { CampaignsService } from './campaigns.service';
import { UnsubscribeController } from './unsubscribe.controller';

@Module({
  imports: [ScheduleModule.forRoot()],
  controllers: [CampaignsController, UnsubscribeController],
  providers: [CampaignsService, CampaignSenderService, PrismaService],
})
export class CampaignsModule {}
