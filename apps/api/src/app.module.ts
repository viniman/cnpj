import { Module } from '@nestjs/common';
import { CompaniesModule } from './companies/companies.module';
import { HealthController } from './health.controller';
import { ListsModule } from './lists/lists.module';
import { ReceitaController } from './receita.controller';

@Module({
  imports: [CompaniesModule, ListsModule],
  controllers: [HealthController, ReceitaController],
})
export class AppModule {}
