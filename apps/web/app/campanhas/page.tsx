import { Send } from 'lucide-react';
import { ComingSoon } from '../../components/coming-soon';
import { PageHeader } from '../../components/page-header';

export default function CampanhasPage() {
  return (
    <div>
      <PageHeader
        title="Campanhas"
        description="Dispare e acompanhe campanhas de e-mail para as listas salvas."
      />
      <div className="px-8 py-6">
        <ComingSoon
          icon={Send}
          title="Em construção"
          description="Em breve você vai poder criar campanhas vinculadas a uma lista e a uma conta de e-mail configurada."
        />
      </div>
    </div>
  );
}
