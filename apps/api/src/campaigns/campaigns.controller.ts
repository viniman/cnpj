import { Body, Controller, Delete, Get, Param, ParseIntPipe, Post } from '@nestjs/common';
import { CampaignsService, CreateCampaignInput } from './campaigns.service';

@Controller('campaigns')
export class CampaignsController {
  constructor(private readonly campaignsService: CampaignsService) {}

  @Post()
  create(@Body() body: CreateCampaignInput) {
    return this.campaignsService.create(body);
  }

  @Get()
  findAll() {
    return this.campaignsService.findAll();
  }

  @Get(':id')
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.campaignsService.findOne(id);
  }

  @Post(':id/start')
  start(@Param('id', ParseIntPipe) id: number) {
    return this.campaignsService.start(id);
  }

  @Post(':id/pause')
  pause(@Param('id', ParseIntPipe) id: number) {
    return this.campaignsService.pause(id);
  }

  @Delete(':id')
  remove(@Param('id', ParseIntPipe) id: number) {
    return this.campaignsService.remove(id);
  }
}
