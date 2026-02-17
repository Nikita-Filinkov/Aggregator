FROM python:3.11-slim

RUN mkdir /aggregator && \
    addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 --ingroup appuser appuser && \
    chown -R appuser:appuser /aggregator


WORKDIR /aggregator

COPY pyproject.toml uv.lock ./

RUN pip install uv && \
    uv sync --frozen --no-dev

COPY . .

ENV PATH="/aggregator/.venv/bin:$PATH"

RUN chmod a+x /aggregator/docker/*.sh

USER appuser

CMD ["/aggregator/docker/app.sh"]