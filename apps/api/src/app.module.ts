import { Module } from '@nestjs/common';
import { CompaniesModule } from './companies/companies.module';
import { HealthController } from './health.controller';
import { ReceitaController } from './receita.controller';

@Module({
  imports: [CompaniesModule],
  controllers: [HealthController, ReceitaController],
})
export class AppModule {}
