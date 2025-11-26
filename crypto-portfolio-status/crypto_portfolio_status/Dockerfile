FROM python:3.12-slim-bookworm

# Copy uv directly from the official image
# This puts 'uv' and 'uvx' executable binaries into /bin/, which is always in PATH
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Sync dependencies
RUN uv sync --frozen

# Copy the rest of the application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the application
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.address=0.0.0.0"]

