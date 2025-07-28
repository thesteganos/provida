# Stage 1: Build dependencies
FROM python:3.10-slim as builder

WORKDIR /app

# Install uv
RUN pip install uv==0.2.1

# Copy requirements.txt and install dependencies using uv
COPY requirements.txt .
RUN uv pip install -r requirements.txt --system

# Stage 2: Create final image
FROM python:3.10-slim

WORKDIR /app

# Define environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

# Copy the rest of the application code
COPY . .

# Keep the container running for development purposes
CMD ["tail", "-f", "/dev/null"]
