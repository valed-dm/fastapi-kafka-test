FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/home/app"

WORKDIR /home/app

# Install system dependencies (if needed, e.g., for PostgreSQL, etc.)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package

# Install Poetry and configure it to install dependencies globally (avoid virtualenvs in Docker)
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false

# Copy dependency files first for caching
COPY pyproject.toml poetry.lock* ./

# Install project dependencies (including uvicorn if it's in pyproject.toml)
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the application code
COPY . .

# Explicitly ensure uvicorn is available (if not in pyproject.toml)
RUN pip install uvicorn

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]