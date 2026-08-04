-- CreateTable
CREATE TABLE "app"."lists" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "lists_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "app"."list_companies" (
    "id" SERIAL NOT NULL,
    "list_id" INTEGER NOT NULL,
    "cnpj_basico" TEXT NOT NULL,
    "cnpj_ordem" TEXT NOT NULL,
    "cnpj_dv" TEXT NOT NULL,
    "razao_social" TEXT NOT NULL,
    "nome_fantasia" TEXT,
    "situacao_cadastral" TEXT,
    "uf" TEXT,
    "municipio_nome" TEXT,
    "cnae_descricao" TEXT,
    "correio_eletronico" TEXT,
    "added_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "list_companies_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "list_companies_list_id_cnpj_basico_cnpj_ordem_cnpj_dv_key" ON "app"."list_companies"("list_id", "cnpj_basico", "cnpj_ordem", "cnpj_dv");

-- AddForeignKey
ALTER TABLE "app"."list_companies" ADD CONSTRAINT "list_companies_list_id_fkey" FOREIGN KEY ("list_id") REFERENCES "app"."lists"("id") ON DELETE CASCADE ON UPDATE CASCADE;
