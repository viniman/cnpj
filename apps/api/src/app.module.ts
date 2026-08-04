import { Module } from '@nestjs/common';
import { CampaignsModule } from './campaigns/campaigns.module';
import { CompaniesModule } from './companies/companies.module';
import { EmailAccountsModule } from './email-accounts/email-accounts.module';
import { HealthController } from './health.controller';
import { ListsModule } from './lists/lists.module';
import { ReceitaController } from './receita.controller';

@Module({
  imports: [CompaniesModule, ListsModule, EmailAccountsModule, CampaignsModule],
  controllers: [HealthController, ReceitaController],
})
export class AppModule {}
