import { ListChecks } from 'lucide-react';
import { ComingSoon } from '../../components/coming-soon';
import { PageHeader } from '../../components/page-header';

export default function ListasPage() {
  return (
    <div>
      <PageHeader
        title="Listas"
        description="Salve empresas encontradas em Empresas para usar em campanhas."
      />
      <div className="px-8 py-6">
        <ComingSoon
          icon={ListChecks}
          title="Em construção"
          description="Em breve você vai poder criar listas a partir de uma busca e gerenciar as empresas salvas aqui."
        />
      </div>
    </div>
  );
}
