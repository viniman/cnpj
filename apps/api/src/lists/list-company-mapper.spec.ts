import { toListCompanyData } from './list-company-mapper';

describe('toListCompanyData', () => {
  const base = {
    cnpjBasico: '12345678',
    cnpjOrdem: '0001',
    cnpjDv: '05',
    razaoSocial: '  Acme Ltda  ',
    nomeFantasia: '  Acme  ',
    situacaoCadastral: '02',
    uf: 'sp',
    municipioNome: 'São Paulo',
    cnaeDescricao: 'Comércio varejista',
    correioEletronico: 'contato@acme.com.br',
  };

  it('trims text fields and keeps ids as-is', () => {
    const result = toListCompanyData(7, base);
    expect(result.listId).toBe(7);
    expect(result.cnpjBasico).toBe('12345678');
    expect(result.razaoSocial).toBe('Acme Ltda');
    expect(result.nomeFantasia).toBe('Acme');
  });

  it('converts blank optional fields to null instead of empty strings', () => {
    const result = toListCompanyData(1, { ...base, nomeFantasia: '   ' });
    expect(result.nomeFantasia).toBeNull();
  });

  it('converts missing optional fields to null', () => {
    const result = toListCompanyData(1, {
      ...base,
      nomeFantasia: undefined,
      situacaoCadastral: null,
    });
    expect(result.nomeFantasia).toBeNull();
    expect(result.situacaoCadastral).toBeNull();
  });

  it('preserves uf casing as provided (normalization happens elsewhere)', () => {
    const result = toListCompanyData(1, base);
    expect(result.uf).toBe('sp');
  });
});
