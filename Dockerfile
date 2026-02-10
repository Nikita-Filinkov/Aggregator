FROM python:3.11-slim

RUN mkdir /aggregator

WORKDIR /aggregator

COPY pyproject.toml uv.lock ./

RUN pip install uv && \
    uv sync --frozen --no-dev

COPY . .
ENV PATH="/aggregator/.venv/bin:$PATH"

RUN chmod a+x /aggregator/docker/*.sh

CMD ["/aggregator/docker/app.sh"]