-- CreateTable
CREATE TABLE "app"."email_accounts" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "from_name" TEXT NOT NULL,
    "from_email" TEXT NOT NULL,
    "smtp_host" TEXT NOT NULL,
    "smtp_port" INTEGER NOT NULL,
    "smtp_secure" BOOLEAN NOT NULL DEFAULT true,
    "smtp_user" TEXT NOT NULL,
    "smtp_password_encrypted" TEXT NOT NULL,
    "daily_limit" INTEGER NOT NULL DEFAULT 100,
    "limit_reset_timezone" TEXT NOT NULL DEFAULT 'UTC',
    "delay_mode" TEXT NOT NULL DEFAULT 'random',
    "delay_fixed_seconds" INTEGER,
    "delay_min_seconds" INTEGER,
    "delay_max_seconds" INTEGER,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "email_accounts_pkey" PRIMARY KEY ("id")
);
