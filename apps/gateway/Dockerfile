FROM python:3.12-slim

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

# Copy entire repo (Cloud Run GitHub deploys from root)
COPY . ./

# Point to gateway requirements specifically
RUN pip install --no-cache-dir -r apps/gateway/requirements.txt

ENV PORT=8080
ENV PYTHONPATH=/app

CMD ["uvicorn", "apps.gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]