import { DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, normalizeCompanySearchParams } from './company-search-params';

describe('normalizeCompanySearchParams', () => {
  it('applies defaults when no query params are given', () => {
    const result = normalizeCompanySearchParams({});
    expect(result).toEqual({
      q: null,
      uf: null,
      cnae: null,
      situacao: null,
      page: 1,
      pageSize: DEFAULT_PAGE_SIZE,
      offset: 0,
    });
  });

  it('trims and keeps a valid search term', () => {
    const result = normalizeCompanySearchParams({ q: '  Petrobras  ' });
    expect(result.q).toBe('Petrobras');
  });

  it('discards a search term shorter than the minimum length', () => {
    const result = normalizeCompanySearchParams({ q: 'a' });
    expect(result.q).toBeNull();
  });

  it('discards a blank search term', () => {
    const result = normalizeCompanySearchParams({ q: '   ' });
    expect(result.q).toBeNull();
  });

  it('uppercases a valid two-letter uf', () => {
    const result = normalizeCompanySearchParams({ uf: 'sp' });
    expect(result.uf).toBe('SP');
  });

  it('discards an invalid uf', () => {
    const result = normalizeCompanySearchParams({ uf: 'SAO' });
    expect(result.uf).toBeNull();
  });

  it('passes through cnae and situacao as trimmed text', () => {
    const result = normalizeCompanySearchParams({ cnae: ' 4711302 ', situacao: ' 02 ' });
    expect(result.cnae).toBe('4711302');
    expect(result.situacao).toBe('02');
  });

  it('defaults page to 1 for invalid input', () => {
    expect(normalizeCompanySearchParams({ page: '0' }).page).toBe(1);
    expect(normalizeCompanySearchParams({ page: '-5' }).page).toBe(1);
    expect(normalizeCompanySearchParams({ page: 'abc' }).page).toBe(1);
  });

  it('clamps pageSize to the maximum allowed', () => {
    const result = normalizeCompanySearchParams({ pageSize: '99999' });
    expect(result.pageSize).toBe(MAX_PAGE_SIZE);
  });

  it('computes offset from page and pageSize', () => {
    const result = normalizeCompanySearchParams({ page: '3', pageSize: '10' });
    expect(result.page).toBe(3);
    expect(result.pageSize).toBe(10);
    expect(result.offset).toBe(20);
  });
});
