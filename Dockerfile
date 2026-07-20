FROM python:3.11-slim

WORKDIR /app
COPY . .

ENV RADAR_CNPJ_HOST=0.0.0.0
ENV RADAR_CNPJ_PORT=8000

EXPOSE 8000

CMD ["python", "-m", "radar_cnpj.server"]

