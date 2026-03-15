FROM python:3.12-slim

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

COPY . ./

# Just requirements.txt — not apps/gateway/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8080
ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]