FROM python:3.12-slim

WORKDIR /app

# Install uv for fast package management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml README.md ./

# Install dependencies
RUN uv pip install --system -e .

# Copy application code
COPY app app/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run the worker
CMD ["python", "-m", "app.main"]
