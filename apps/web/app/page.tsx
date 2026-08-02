const API_URL = process.env.API_URL || 'http://127.0.0.1:3001';

async function getApiStatus() {
  try {
    const response = await fetch(`${API_URL}/receita/status`, {
      cache: 'no-store',
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const status = await getApiStatus();

  return (
    <main className="shell">
      <section className="panel">
        <p className="eyebrow">Next.js SSR / fundação inicial</p>
        <h1>Radar CNPJ</h1>
        <p>
          Esta é a primeira tela Next.js. A interface Python continua como super
          admin/ETL enquanto o produto principal nasce aqui.
        </p>
        <div className="statusGrid">
          <div>
            <span>API Nest</span>
            <strong>{status ? 'conectada' : 'aguardando'}</strong>
          </div>
          <div>
            <span>Fonte</span>
            <strong>{status?.schema || 'receita_staging'}</strong>
          </div>
          <div>
            <span>Próximo passo</span>
            <strong>busca normalizada</strong>
          </div>
        </div>
      </section>
    </main>
  );
}
