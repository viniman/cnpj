export interface TemplateVariables {
  razaoSocial: string;
  nomeFantasia?: string | null;
  municipioNome?: string | null;
  [key: string]: string | null | undefined;
}

const VARIABLE_PATTERN = /\{\{\s*(\w+)\s*\}\}/g;

/**
 * Replaces {{razaoSocial}}, {{nomeFantasia}}, {{municipioNome}} with the
 * recipient's snapshot values. Unknown variables and null/undefined
 * values are replaced with an empty string rather than left as-is, so a
 * missing value never leaks the literal "{{...}}" into a sent email.
 */
export function renderTemplate(template: string, variables: TemplateVariables): string {
  return template.replace(VARIABLE_PATTERN, (_match, key: string) => {
    const value = variables[key];
    return value ?? '';
  });
}
