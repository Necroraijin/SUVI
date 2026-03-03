# Use the official lightweight Python image.
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set the working directory
WORKDIR /app

# Copy dependencies list and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the gateway code
COPY . ./suvi_gateway

# Expose the port Cloud Run expects
EXPOSE 8080

# Command to run the FastAPI app using Uvicorn
CMD ["uvicorn", "suvi_gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]