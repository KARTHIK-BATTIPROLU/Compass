FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy uv dependency files
COPY pyproject.toml .

# Install dependencies using uv
RUN uv pip install --system fastapi uvicorn pydantic

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
