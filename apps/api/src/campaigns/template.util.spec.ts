import { renderTemplate } from './template.util';

describe('renderTemplate', () => {
  it('substitutes known variables', () => {
    const result = renderTemplate('Olá {{razaoSocial}} de {{municipioNome}}!', {
      razaoSocial: 'Acme Ltda',
      municipioNome: 'São Paulo',
    });
    expect(result).toBe('Olá Acme Ltda de São Paulo!');
  });

  it('replaces missing/null variables with an empty string instead of leaving the placeholder', () => {
    const result = renderTemplate('Fantasia: {{nomeFantasia}}.', {
      razaoSocial: 'Acme Ltda',
      nomeFantasia: null,
    });
    expect(result).toBe('Fantasia: .');
  });

  it('replaces unknown variable names with an empty string', () => {
    const result = renderTemplate('{{unknownVar}}', { razaoSocial: 'Acme' });
    expect(result).toBe('');
  });

  it('tolerates extra whitespace inside the braces', () => {
    const result = renderTemplate('{{ razaoSocial }}', { razaoSocial: 'Acme' });
    expect(result).toBe('Acme');
  });

  it('leaves plain text without variables untouched', () => {
    expect(renderTemplate('Sem variaveis aqui.', { razaoSocial: 'x' })).toBe('Sem variaveis aqui.');
  });
});
