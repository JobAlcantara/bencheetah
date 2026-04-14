FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY tests/ tests/
COPY examples/ examples/

# Install library + optional matplotlib dependency
RUN pip install --no-cache-dir -e ".[dev]" matplotlib

# Default: run the demo (saves scaling_sort.png inside the container)
CMD ["python", "examples/demo.py"]
