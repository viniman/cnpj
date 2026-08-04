import { Body, Controller, Delete, Get, Param, ParseIntPipe, Post, Query } from '@nestjs/common';
import { CompanyInput } from './list-company-mapper';
import { ListsService } from './lists.service';

@Controller('lists')
export class ListsController {
  constructor(private readonly listsService: ListsService) {}

  @Post()
  create(@Body() body: { name?: string; description?: string }) {
    return this.listsService.create(body);
  }

  @Get()
  findAll() {
    return this.listsService.findAll();
  }

  @Get(':id')
  findOne(
    @Param('id', ParseIntPipe) id: number,
    @Query('page') page?: string,
    @Query('pageSize') pageSize?: string,
  ) {
    return this.listsService.findOne(id, Number(page) || 1, Number(pageSize) || undefined);
  }

  @Delete(':id')
  remove(@Param('id', ParseIntPipe) id: number) {
    return this.listsService.remove(id);
  }

  @Post(':id/companies')
  addCompanies(@Param('id', ParseIntPipe) id: number, @Body() body: { companies?: CompanyInput[] }) {
    return this.listsService.addCompanies(id, body.companies || []);
  }

  @Delete(':id/companies/:companyId')
  removeCompany(
    @Param('id', ParseIntPipe) id: number,
    @Param('companyId', ParseIntPipe) companyId: number,
  ) {
    return this.listsService.removeCompany(id, companyId);
  }
}
