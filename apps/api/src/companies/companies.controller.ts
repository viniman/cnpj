import { Controller, Get, Query } from '@nestjs/common';
import { CompaniesService } from './companies.service';
import { CompanySearchQuery } from './company-search-params';

@Controller('companies')
export class CompaniesController {
  constructor(private readonly companiesService: CompaniesService) {}

  @Get('search')
  search(@Query() query: CompanySearchQuery) {
    return this.companiesService.search(query);
  }
}
