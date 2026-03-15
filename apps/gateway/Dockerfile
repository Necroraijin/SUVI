# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.12-slim

# Allow statements and errors to be immediately logged to the Cloud Run logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup.
# We set a default PORT to 8080 if not provided by Cloud Run.
ENV PORT=8080
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
