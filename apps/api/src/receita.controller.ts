import { Controller, Get } from '@nestjs/common';

@Controller('receita')
export class ReceitaController {
  @Get('status')
  status() {
    return {
      schema: 'receita_staging',
      mode: 'postgres-staging-read-model',
      search_endpoint: 'GET /companies/search',
    };
  }
}
