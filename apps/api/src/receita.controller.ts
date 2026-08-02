import { Controller, Get } from '@nestjs/common';

@Controller('receita')
export class ReceitaController {
  @Get('status')
  status() {
    return {
      schema: 'receita_staging',
      mode: 'postgres-staging-read-model',
      next: 'Implementar Prisma service e endpoints de busca normalizados.',
    };
  }
}
