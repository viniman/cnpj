-- AlterTable
ALTER TABLE "app"."email_accounts" ADD COLUMN     "last_sent_at" TIMESTAMP(3);

-- CreateTable
CREATE TABLE "app"."campaigns" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "list_id" INTEGER NOT NULL,
    "email_account_id" INTEGER NOT NULL,
    "subject" TEXT NOT NULL,
    "body_html" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'draft',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "campaigns_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "app"."campaign_recipients" (
    "id" SERIAL NOT NULL,
    "campaign_id" INTEGER NOT NULL,
    "list_company_id" INTEGER NOT NULL,
    "razao_social" TEXT NOT NULL,
    "nome_fantasia" TEXT,
    "municipio_nome" TEXT,
    "email" TEXT,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "sent_at" TIMESTAMP(3),
    "error_message" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "campaign_recipients_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "app"."suppression_entries" (
    "id" SERIAL NOT NULL,
    "email" TEXT NOT NULL,
    "reason" TEXT NOT NULL DEFAULT 'unsubscribed',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "suppression_entries_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "suppression_entries_email_key" ON "app"."suppression_entries"("email");

-- AddForeignKey
ALTER TABLE "app"."campaigns" ADD CONSTRAINT "campaigns_list_id_fkey" FOREIGN KEY ("list_id") REFERENCES "app"."lists"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "app"."campaigns" ADD CONSTRAINT "campaigns_email_account_id_fkey" FOREIGN KEY ("email_account_id") REFERENCES "app"."email_accounts"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "app"."campaign_recipients" ADD CONSTRAINT "campaign_recipients_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "app"."campaigns"("id") ON DELETE CASCADE ON UPDATE CASCADE;
