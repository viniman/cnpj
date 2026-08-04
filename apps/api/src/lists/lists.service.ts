import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma.service';
import { CompanyInput, toListCompanyData } from './list-company-mapper';

const MAX_PAGE_SIZE = 100;
const DEFAULT_PAGE_SIZE = 25;

@Injectable()
export class ListsService {
  constructor(private readonly prisma: PrismaService) {}

  async create(input: { name?: string; description?: string }) {
    const name = input.name?.trim();
    if (!name) {
      throw new BadRequestException('Informe um nome para a lista.');
    }
    return this.prisma.list.create({
      data: { name, description: input.description?.trim() || null },
    });
  }

  async findAll() {
    const lists = await this.prisma.list.findMany({
      orderBy: { createdAt: 'desc' },
      include: { _count: { select: { companies: true } } },
    });
    return lists.map((list) => ({
      id: list.id,
      name: list.name,
      description: list.description,
      createdAt: list.createdAt,
      companyCount: list._count.companies,
    }));
  }

  async findOne(id: number, page = 1, pageSize = DEFAULT_PAGE_SIZE) {
    const list = await this.prisma.list.findUnique({ where: { id } });
    if (!list) {
      throw new NotFoundException('Lista não encontrada.');
    }

    const safePageSize = Math.min(Math.max(pageSize, 1), MAX_PAGE_SIZE);
    const safePage = Math.max(page, 1);

    const [companies, companyCount] = await Promise.all([
      this.prisma.listCompany.findMany({
        where: { listId: id },
        orderBy: { addedAt: 'desc' },
        skip: (safePage - 1) * safePageSize,
        take: safePageSize,
      }),
      this.prisma.listCompany.count({ where: { listId: id } }),
    ]);

    return { ...list, companies, companyCount, page: safePage, pageSize: safePageSize };
  }

  async remove(id: number) {
    const list = await this.prisma.list.findUnique({ where: { id } });
    if (!list) {
      throw new NotFoundException('Lista não encontrada.');
    }
    await this.prisma.list.delete({ where: { id } });
  }

  async addCompanies(listId: number, companies: CompanyInput[]) {
    const list = await this.prisma.list.findUnique({ where: { id: listId } });
    if (!list) {
      throw new NotFoundException('Lista não encontrada.');
    }
    if (!Array.isArray(companies) || companies.length === 0) {
      throw new BadRequestException('Informe ao menos uma empresa para adicionar.');
    }

    const data = companies.map((company) => toListCompanyData(listId, company));
    const result = await this.prisma.listCompany.createMany({ data, skipDuplicates: true });
    return { added: result.count, requested: companies.length };
  }

  async removeCompany(listId: number, listCompanyId: number) {
    const entry = await this.prisma.listCompany.findFirst({ where: { id: listCompanyId, listId } });
    if (!entry) {
      throw new NotFoundException('Empresa não encontrada nesta lista.');
    }
    await this.prisma.listCompany.delete({ where: { id: listCompanyId } });
  }
}
