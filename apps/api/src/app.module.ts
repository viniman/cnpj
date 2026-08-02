import { Module } from '@nestjs/common';
import { HealthController } from './health.controller';
import { ReceitaController } from './receita.controller';

@Module({
  controllers: [HealthController, ReceitaController],
})
export class AppModule {}
