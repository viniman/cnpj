import { Mail } from 'lucide-react';
import { ComingSoon } from '../../../components/coming-soon';
import { PageHeader } from '../../../components/page-header';

export default function ConfigEmailPage() {
  return (
    <div>
      <PageHeader
        title="Configuração de e-mail"
        description="Conecte a conta SMTP (AWS SES) usada para disparar campanhas e defina o limite diário de envios."
      />
      <div className="px-8 py-6">
        <ComingSoon
          icon={Mail}
          title="Em construção"
          description="Em breve você vai poder cadastrar as credenciais SMTP e configurar o limite diário e o atraso entre envios."
        />
      </div>
    </div>
  );
}
