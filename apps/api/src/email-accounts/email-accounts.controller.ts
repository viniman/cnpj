import { Body, Controller, Delete, Get, Param, ParseIntPipe, Patch, Post } from '@nestjs/common';
import { EmailAccountInput } from './email-account-input';
import { EmailAccountsService } from './email-accounts.service';

@Controller('email-accounts')
export class EmailAccountsController {
  constructor(private readonly emailAccountsService: EmailAccountsService) {}

  @Post()
  create(@Body() body: EmailAccountInput) {
    return this.emailAccountsService.create(body);
  }

  @Get()
  findAll() {
    return this.emailAccountsService.findAll();
  }

  @Get(':id')
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.emailAccountsService.findOne(id);
  }

  @Patch(':id')
  update(@Param('id', ParseIntPipe) id: number, @Body() body: EmailAccountInput) {
    return this.emailAccountsService.update(id, body);
  }

  @Delete(':id')
  remove(@Param('id', ParseIntPipe) id: number) {
    return this.emailAccountsService.remove(id);
  }

  @Post(':id/test')
  testConnection(@Param('id', ParseIntPipe) id: number) {
    return this.emailAccountsService.testConnection(id);
  }
}
