FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY shared/ ./shared/
COPY scraper/ ./scraper/
COPY mongodb/ ./mongodb/

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "scraper"]
