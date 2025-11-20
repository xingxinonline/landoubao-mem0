FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy pyproject.toml
COPY pyproject.toml .

# Install dependencies using uv
RUN uv pip install --system .

COPY main.py .
COPY memory_maintenance.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
