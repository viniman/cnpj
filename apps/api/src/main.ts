import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.enableCors({
    origin: process.env.WEB_ORIGIN || 'http://127.0.0.1:3000',
    credentials: true,
  });
  await app.listen(Number(process.env.PORT || 3001));
}

bootstrap();
